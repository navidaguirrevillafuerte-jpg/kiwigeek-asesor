import streamlit as st
import os
import re
import json
from google import genai
from google.genai import types

# --- CONFIGURACION DE LA PAGINA ---
st.set_page_config(
    page_title="Kiwigeek AI - Cotizador de Hardware",
    page_icon="https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- CONSTANTES ---
AVATAR_URL = "https://kiwigeekperu.com/wp-content/uploads/2026/01/gatitow.webp"
WHATSAPP_LINK = "https://api.whatsapp.com/send/?phone=51939081940&text=Hola%2C+vengo+del+Chat+AI+y+quiero+reclamar+mi+descuento+especial+por+PC+Completa&type=phone_number&app_absent=0"
MAX_RETRIES = 3
BUDGET_MARGIN = 0.10  # 10%
MAX_CASE_PRICE = 500

# --- FUNCIONES DE VALIDACION ---
def extract_budget(text):
    """Extrae el presupuesto numerico del mensaje del usuario usando regex."""
    patterns = [
        r'(?:presupuesto|budget|tengo|dispongo)\s*(?:de|es|:)?\s*[sS]?/?\.?\s*(\d{1,3}(?:[,.]?\d{3})*)',
        r'[sS]/?\.?\s*(\d{1,3}(?:[,.]?\d{3})*)',
        r'(\d{1,3}(?:[,.]?\d{3})*)\s*(?:soles?|nuevos soles)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            budget_str = match.group(1).replace(',', '').replace('.', '')
            try:
                return float(budget_str)
            except ValueError:
                continue
    return None

def validate_quote(quote_data, user_budget):
    """
    Valida una cotizacion completa segun las reglas del negocio.
    Retorna: (es_valida: bool, errores: list, detalles: dict)
    """
    errors = []
    details = {}
    
    if not quote_data.get("components"):
        errors.append("La cotizacion no tiene componentes.")
        return False, errors, details
    
    # Calcular total
    total = sum(float(item.get("price", 0)) for item in quote_data["components"])
    details["total"] = total
    details["budget"] = user_budget
    
    # Validar margen de presupuesto (10%)
    if user_budget:
        min_budget = user_budget * (1 - BUDGET_MARGIN)
        max_budget = user_budget * (1 + BUDGET_MARGIN)
        
        if total < min_budget:
            diff = min_budget - total
            errors.append(f"El presupuesto esta MUY por debajo: falta usar S/ {diff:.2f}. Optimiza los componentes para acercarte a S/ {user_budget:,.0f}")
        elif total > max_budget:
            diff = total - max_budget
            errors.append(f"Te pasaste del presupuesto en S/ {diff:.2f}. El maximo permitido es S/ {max_budget:,.0f}")
    
    # Extraer precios de GPU, CPU y Case
    gpu_price = 0
    cpu_price = 0
    case_price = 0
    
    for item in quote_data["components"]:
        name_lower = item.get("name", "").lower()
        price = float(item.get("price", 0))
        
        if any(keyword in name_lower for keyword in ["rtx", "gtx", "radeon", "rx ", "gpu", "grafica", "video"]):
            gpu_price = max(gpu_price, price)
        
        if any(keyword in name_lower for keyword in ["ryzen", "intel", "core i", "processor", "cpu"]):
            cpu_price = max(cpu_price, price)
        
        if any(keyword in name_lower for keyword in ["case", "gabinete", "torre", "caja"]):
            case_price = max(case_price, price)
    
    details["gpu_price"] = gpu_price
    details["cpu_price"] = cpu_price
    details["case_price"] = case_price
    
    # Validar GPU > CPU
    if gpu_price > 0 and cpu_price > 0:
        if gpu_price <= cpu_price:
            diff = cpu_price - gpu_price
            errors.append(f"CRITICO: La GPU (S/ {gpu_price:,.0f}) debe ser MAS CARA que la CPU (S/ {cpu_price:,.0f}). Diferencia actual: S/ {diff:.0f}. Aumenta el presupuesto de GPU.")
    
    # Validar precio del Case
    if case_price > MAX_CASE_PRICE:
        diff = case_price - MAX_CASE_PRICE
        errors.append(f"El Case cuesta S/ {case_price:,.0f} pero el maximo permitido es S/ {MAX_CASE_PRICE}. Reduce S/ {diff:.0f} y reasigna ese presupuesto a GPU/CPU.")
    
    return len(errors) == 0, errors, details

def generate_retry_prompt(errors, details):
    """Genera un mensaje de feedback para la IA cuando falla la validacion."""
    feedback = "VALIDACION FALLIDA. Debes corregir lo siguiente:\n\n"
    
    for i, error in enumerate(errors, 1):
        feedback += f"{i}. {error}\n"
    
    feedback += f"\n--- Detalles de la ultima cotizacion ---\n"
    feedback += f"Total calculado: S/ {details.get('total', 0):,.2f}\n"
    feedback += f"Presupuesto objetivo: S/ {details.get('budget', 0):,.2f}\n"
    feedback += f"GPU: S/ {details.get('gpu_price', 0):,.2f}\n"
    feedback += f"CPU: S/ {details.get('cpu_price', 0):,.2f}\n"
    feedback += f"Case: S/ {details.get('case_price', 0):,.2f}\n\n"
    feedback += "Por favor, genera una nueva cotizacion corrigiendo estos errores. RESPETA LAS REGLAS: GPU > CPU, Case <= S/ 500, margen 10%."
    
    return feedback

# --- CSS MIXTO ---
def apply_custom_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
        
        * { font-family: 'Inter', sans-serif !important; }
        
        .neon-title {
            color: #00FF41 !important;
            text-shadow: 0 0 30px rgba(0,255,65,0.6);
            text-align: center;
            font-weight: 900 !important;
            font-size: 6rem !important;
            margin: 0;
            line-height: 1;
        }

        .stChatMessage { background: transparent !important; border: none !important; padding: 1rem 0; }
        .stMarkdown h3 { margin-top: 20px; font-size: 1.2rem; font-weight: bold; color: #000 !important; }
        .stMarkdown a { color: #0066cc !important; text-decoration: underline; }
        .stMarkdown li { background: transparent !important; padding: 2px 0 !important; border: none !important; color: #000 !important; }
        .stMarkdown p { color: #000 !important; margin-bottom: 0.5rem; }

        [data-testid="stSidebar"] { background-color: #f8f9fa; }
        .info-box { background: #fff; border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .info-title-yes { color: #28a745; font-weight: bold; border-bottom: 2px solid #28a745; margin-bottom: 8px; }
        .info-title-no { color: #d9534f; font-weight: bold; border-bottom: 2px solid #d9534f; margin-bottom: 8px; }
        .info-title-promo { color: #d4ac0d; font-weight: bold; border-bottom: 2px solid #ffd700; margin-bottom: 8px; }
        
        .promo-btn {
            display: block; width: 100%; text-align: center; background-color: #25D366;
            color: white !important; padding: 10px 0; border-radius: 8px; text-decoration: none !important;
            font-weight: bold; margin-top: 10px; transition: 0.3s;
        }
        .promo-btn:hover { background-color: #128C7E; }
        
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# --- CONFIGURACION DE IA ---
def get_api_key():
    try: 
        return st.secrets["GEMINI_API_KEY"]
    except: 
        return os.getenv("GEMINI_API_KEY", "")

api_key = get_api_key()
if not api_key:
    st.sidebar.warning("⚠️ API Key no encontrada")
    st.stop()

client = genai.Client(api_key=api_key)
MODEL_ID = 'models/gemini-2.0-flash'

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "needs_info": {"type": "BOOLEAN"},
        "is_quote": {"type": "BOOLEAN"},
        "message": {"type": "STRING"},
        "quotes": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "strategy": {"type": "STRING"},
                    "components": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "name": {"type": "STRING"},
                                "price": {"type": "NUMBER"},
                                "url": {"type": "STRING"},
                                "insight": {"type": "STRING"}
                            },
                            "required": ["name", "price"]
                        }
                    }
                },
                "required": ["title", "components"]
            }
        }
    },
    "required": ["needs_info", "is_quote", "message"]
}

@st.cache_resource
def setup_kiwi_brain():
    try:
        catalog = ""
        if os.path.exists('catalogo_kiwigeek.json'):
            with open('catalogo_kiwigeek.json', 'r', encoding='utf-8') as f:
                catalog = f.read()
            
        sys_prompt = """ROL: Eres 'Kiwigeek AI', Ingeniero Senior de Hardware y Cotizador Experto.

REGLAS CRITICAS (NUNCA VIOLAR):
1. GPU > CPU: La GPU SIEMPRE debe costar MAS que la CPU. Esto es OBLIGATORIO.
2. Case economico: El gabinete/case NO puede superar S/ 500. Usa opciones economicas.
3. Margen presupuesto: El total debe estar dentro del ±10% del presupuesto del usuario.
4. Antes de cotizar: Si el usuario no especifica "Solo Torre" o "PC Completa", pregunta y marca 'needs_info: true'.

JERARQUIA DE INVERSION:
- Solo Torre: GPU (MAS CARO) > CPU > RAM > Placa Madre > SSD > Fuente > Case (≤S/500)
- PC Completa: GPU (MAS CARO) > CPU > RAM > Monitor > Placa Madre > SSD > Fuente > Perifericos > Case (≤S/500)

PROCESO DE COTIZACION:
1. Identifica el presupuesto total disponible
2. Asigna 30-40% a GPU (componente mas caro)
3. Asigna 20-25% a CPU (segundo mas caro, pero MENOS que GPU)
4. Distribuye el resto en orden de prioridad
5. Verifica que GPU > CPU antes de responder
6. Case SIEMPRE economico (maximo S/500)

LIMITACIONES:
- NO des descripciones largas de productos
- NO gestiones ventas directas
- NO envies promociones
- Tu trabajo es COTIZAR tecnicamente

FORMATO: Responde en JSON. Python calculara los totales y validara."""
        
        return client.caches.create(
            model=MODEL_ID,
            config=types.CreateCachedContentConfig(
                display_name='kiwi_v8_validator',
                system_instruction=sys_prompt,
                contents=[catalog] if catalog else [],
                ttl='7200s'
            )
        ).name, None
    except Exception as e:
        return None, str(e)

def initialize_session(force=False):
    """Inicializa la sesion de chat con persistencia robusta."""
    if "messages" not in st.session_state: 
        st.session_state.messages = []
    
    if "user_budget" not in st.session_state:
        st.session_state.user_budget = None
    
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = None
    
    # Reinicializar solo si se fuerza o no existe
    if force or "chat_session" not in st.session_state:
        cache_name, err = setup_kiwi_brain()
        config = types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA
        )
        if cache_name: 
            config.cached_content = cache_name
        
        st.session_state.chat_session = client.chats.create(model=MODEL_ID, config=config)
        
        if not st.session_state.messages:
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "¡Hola! Soy **Kiwigeek AI**. Dime tu presupuesto y si buscas **Solo Torre** o **PC Completa** para darte opciones optimizadas."
            })

# Inicializar sesion al cargar
initialize_session()

# --- UI (SIDEBAR) ---
with st.sidebar:
    st.image('https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png', use_container_width=True)
    
    # Panel SI hago
    st.markdown("""
    <div class="info-box"><div class="info-title-yes">✅ Cotizador Especializado</div>
    <ul class="info-list">
        <li>GPU siempre > CPU (Garantizado).</li>
        <li>Case economico (Max S/500).</li>
        <li>Presupuesto exacto (±10%).</li>
        <li>Validacion automatica con reintentos.</li>
    </ul></div>
    """, unsafe_allow_html=True)

    # Panel NO hago
    st.markdown("""
    <div class="info-box"><div class="info-title-no">🚫 Cosas que NO hago</div>
    <ul class="info-list">
        <li>Descripciones de productos.</li>
        <li>Ventas directas.</li>
        <li>Envio de promociones.</li>
    </ul></div>
    """, unsafe_allow_html=True)

    # Panel Promocion
    st.markdown(f"""
    <div class="info-box" style="border: 1px solid #ffd700; background: #fffdf0;">
    <div class="info-title-promo">🎁 ¡Promocion Especial!</div>
    <p style="font-size: 0.85rem;">Compra tu combo <b>CPU + Placa + RAM + GPU</b> y obten un descuento exclusivo.</p>
    <a href="{WHATSAPP_LINK}" target="_blank" class="promo-btn">📲 Reclamar Descuento</a></div>
    """, unsafe_allow_html=True)
    
    # Mostrar presupuesto detectado
    if st.session_state.user_budget:
        st.info(f"💰 Presupuesto detectado: S/ {st.session_state.user_budget:,.0f}")
    
    if st.button("🗑️ Reiniciar Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.user_budget = None
        if "chat_session" in st.session_state: 
            del st.session_state["chat_session"]
        st.rerun()

# --- HEADER ---
st.markdown("""
    <div style="display: flex; align-items: center; justify-content: center; gap: 20px; padding: 20px 0;">
        <img src="https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png" height="120">
        <h1 class='neon-title'>AI</h1>
    </div>
""", unsafe_allow_html=True)

# Renderizar historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=AVATAR_URL if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])

# --- INPUT DE CHAT CON VALIDACION Y RETRY LOGIC ---
if prompt := st.chat_input("Dime tu presupuesto y tipo de PC..."):
    # Extraer presupuesto del mensaje
    detected_budget = extract_budget(prompt)
    if detected_budget and not st.session_state.user_budget:
        st.session_state.user_budget = detected_budget
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"): 
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=AVATAR_URL):
        with st.spinner("Analizando componentes y optimizando inversion..."):
            try:
                # Verificacion de seguridad
                if "chat_session" not in st.session_state:
                    initialize_session(force=True)
                
                # RETRY LOGIC: Intentar hasta MAX_RETRIES veces
                valid_response = None
                retry_count = 0
                internal_prompt = prompt
                
                while retry_count < MAX_RETRIES and not valid_response:
                    response = st.session_state.chat_session.send_message(internal_prompt)
                    data = json.loads(response.text)
                    
                    # Si pide info o no es cotizacion, aceptar directamente
                    if data.get("needs_info") or not data.get("is_quote"):
                        valid_response = data
                        break
                    
                    # Si es cotizacion, validar cada quote
                    if data.get("quotes"):
                        all_valid = True
                        accumulated_errors = []
                        
                        for quote in data["quotes"]:
                            is_valid, errors, details = validate_quote(quote, st.session_state.user_budget)
                            
                            if not is_valid:
                                all_valid = False
                                accumulated_errors.extend(errors)
                        
                        if all_valid:
                            valid_response = data
                        else:
                            retry_count += 1
                            if retry_count < MAX_RETRIES:
                                # Generar feedback interno
                                internal_prompt = generate_retry_prompt(accumulated_errors, details)
                                # Esperar un momento antes de reintentar
                                import time
                                time.sleep(0.5)
                            else:
                                # Maximo de intentos alcanzado
                                st.warning(f"⚠️ Despues de {MAX_RETRIES} intentos, la IA no pudo generar una cotizacion valida. Mostrando la mejor aproximacion:")
                                valid_response = data
                
                # Renderizar respuesta final
                if valid_response:
                    data = valid_response
                    final_text = ""
                    
                    if data.get("needs_info"):
                        final_text = data.get("message", "Por favor, indicame si deseas Solo Torre o PC Completa.")
                    elif data.get("is_quote") and data.get("quotes"):
                        final_text = data.get("message", "He optimizado tu inversion:") + "\n\n---\n"
                        
                        for q in data["quotes"]:
                            total = sum(float(item.get("price", 0)) for item in q.get("components", []))
                            final_text += f"### {q.get('title', 'Opcion')}\n"
                            final_text += f"**Estrategia:** {q.get('strategy', 'Optimizacion balanceada')}\n\n"
                            
                            for item in q.get("components", []):
                                link = f" - [Ver Aqui]({item['url']})" if item.get('url') else ""
                                insight = f"\n  💡 *{item['insight']}*" if item.get('insight') else ""
                                final_text += f"- {item['name']} - S/ {item['price']:,.2f}{link}{insight}\n"
                            
                            # Calcular margen
                            if st.session_state.user_budget:
                                diff = total - st.session_state.user_budget
                                margin_pct = (diff / st.session_state.user_budget) * 100
                                final_text += f"\n**TOTAL: S/ {total:,.2f}** (Margen: {margin_pct:+.1f}%)\n\n---\n"
                            else:
                                final_text += f"\n**TOTAL: S/ {total:,.2f}**\n\n---\n"
                    else:
                        final_text = data.get("message", "Entendido. ¿En que mas puedo ayudarte?")
                    
                    st.markdown(final_text)
                    st.session_state.messages.append({"role": "assistant", "content": final_text})
                
            except Exception as e:
                # Manejo de errores con reintento
                try:
                    initialize_session(force=True)
                    st.markdown("🔄 Conexion restablecida. Por favor, reintenta tu mensaje.")
                except:
                    st.error("❌ Error de conexion. Por favor, pulsa 'Reiniciar Chat' e intenta nuevamente.")
                    st.exception(e)
