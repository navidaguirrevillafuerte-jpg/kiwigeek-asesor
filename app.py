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
BUDGET_MARGIN = 0.10  # ±10%
CASE_MIN_PERCENTAGE = 0.03  # 3%
CASE_MAX_PERCENTAGE = 0.05  # 5%
ABSOLUTE_MAX_CASE = 500  # S/500 limite absoluto

# --- FUNCIONES DE VALIDACION TECNICA ---

def extract_budget(text):
    """
    Extrae el presupuesto numerico del mensaje del usuario.
    Soporta formatos: "S/ 5000", "5,000 soles", "presupuesto de 5000"
    """
    patterns = [
        r'(?:presupuesto|budget|tengo|dispongo|cuento con)\s*(?:de|es|:)?\s*[sS]?/?\.?\s*(\d{1,3}(?:[,.]?\d{3})*)',
        r'[sS]/?\.?\s*(\d{1,3}(?:[,.]?\d{3})*)',
        r'(\d{1,3}(?:[,.]?\d{3})*)\s*(?:soles?|nuevos soles|pen)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            budget_str = match.group(1).replace(',', '').replace('.', '')
            try:
                budget = float(budget_str)
                if 500 <= budget <= 50000:  # Rango razonable
                    return budget
            except ValueError:
                continue
    return None

def calculate_gpu_cpu_multiplier(gpu_price, cpu_price):
    """
    Calcula el multiplicador M = Precio GPU / Precio CPU
    Retorna 0 si no se puede calcular
    """
    if cpu_price > 0:
        return gpu_price / cpu_price
    return 0

def get_multiplier_range(budget):
    """
    Retorna el rango permitido de multiplicador GPU/CPU segun el presupuesto.
    Retorna: (min_multiplier, max_multiplier, critical_max)
    """
    if budget < 5000:
        return (1.7, 2.0, 2.5)  # Gama baja: balance conservador
    elif 5000 <= budget <= 10000:
        return (2.2, 3.0, 4.0)  # Gama media: GPU puede ser mas fuerte
    else:
        return (2.5, 5.0, 6.0)  # Gama alta: GPU dominante permitida

def extract_component_prices(components):
    """
    Extrae precios de GPU, CPU y Case de la lista de componentes.
    Retorna: dict con gpu_price, cpu_price, case_price
    """
    gpu_price = 0
    cpu_price = 0
    case_price = 0
    
    gpu_keywords = ["rtx", "gtx", "radeon", "rx ", "gpu", "grafica", "video", "nvidia", "amd rx"]
    cpu_keywords = ["ryzen", "intel", "core i", "processor", "cpu", "i3", "i5", "i7", "i9"]
    case_keywords = ["case", "gabinete", "torre", "caja", "chasis"]
    
    for item in components:
        name_lower = item.get("name", "").lower()
        price = float(item.get("price", 0))
        
        # Detectar GPU
        if any(keyword in name_lower for keyword in gpu_keywords):
            gpu_price = max(gpu_price, price)
        
        # Detectar CPU
        if any(keyword in name_lower for keyword in cpu_keywords):
            cpu_price = max(cpu_price, price)
        
        # Detectar Case
        if any(keyword in name_lower for keyword in case_keywords):
            case_price = max(case_price, price)
    
    return {
        "gpu_price": gpu_price,
        "cpu_price": cpu_price,
        "case_price": case_price
    }

def validate_build(budget, components):
    """
    Validador matematico de hardware con reglas de ingenieria.
    
    Parametros:
    - budget: Presupuesto del usuario (P)
    - components: Lista de componentes con 'name' y 'price'
    
    Retorna: (es_valida: bool, errores: list, detalles: dict)
    """
    errors = []
    details = {}
    
    if not components:
        errors.append("No se proporcionaron componentes para validar.")
        return False, errors, details
    
    # 1. CALCULAR TOTAL
    total = sum(float(item.get("price", 0)) for item in components)
    details["total"] = total
    details["budget"] = budget
    
    # 2. VALIDAR MARGEN DE PRESUPUESTO (±10%)
    min_budget = budget * (1 - BUDGET_MARGIN)
    max_budget = budget * (1 + BUDGET_MARGIN)
    
    if total < min_budget:
        diff = min_budget - total
        percentage_diff = ((min_budget - total) / budget) * 100
        errors.append(
            f"PRESUPUESTO SUBUTILIZADO: Faltan usar S/ {diff:.2f} ({percentage_diff:.1f}% por debajo). "
            f"Objetivo: S/ {budget:,.0f} | Rango valido: S/ {min_budget:,.0f} - S/ {max_budget:,.0f}. "
            f"Mejora GPU o CPU para aprovechar el presupuesto."
        )
    elif total > max_budget:
        diff = total - max_budget
        percentage_diff = ((total - max_budget) / budget) * 100
        errors.append(
            f"PRESUPUESTO EXCEDIDO: Te pasaste S/ {diff:.2f} ({percentage_diff:.1f}% por encima). "
            f"Maximo permitido: S/ {max_budget:,.0f}. Reduce costos en componentes secundarios."
        )
    
    # 3. EXTRAER PRECIOS DE COMPONENTES CRITICOS
    prices = extract_component_prices(components)
    gpu_price = prices["gpu_price"]
    cpu_price = prices["cpu_price"]
    case_price = prices["case_price"]
    
    details["gpu_price"] = gpu_price
    details["cpu_price"] = cpu_price
    details["case_price"] = case_price
    
    # 4. VALIDAR MULTIPLICADOR GPU/CPU (M)
    if gpu_price > 0 and cpu_price > 0:
        multiplier = calculate_gpu_cpu_multiplier(gpu_price, cpu_price)
        details["multiplier"] = multiplier
        
        min_m, max_m, critical_m = get_multiplier_range(budget)
        details["min_multiplier"] = min_m
        details["max_multiplier"] = max_m
        
        if multiplier < min_m:
            # GPU muy barata para el CPU
            needed_gpu_price = cpu_price * min_m
            diff = needed_gpu_price - gpu_price
            errors.append(
                f"DESBALANCE CRITICO: GPU muy debil. Multiplicador actual: {multiplier:.2f}x "
                f"(Minimo requerido: {min_m}x para presupuesto S/ {budget:,.0f}). "
                f"GPU: S/ {gpu_price:,.0f} | CPU: S/ {cpu_price:,.0f}. "
                f"Aumenta GPU en ~S/ {diff:.0f} o reduce CPU."
            )
        elif multiplier > critical_m:
            # Cuello de botella: CPU muy debil
            needed_cpu_price = gpu_price / max_m
            diff = needed_cpu_price - cpu_price
            errors.append(
                f"CUELLO DE BOTELLA: CPU insuficiente para GPU. Multiplicador: {multiplier:.2f}x "
                f"(Maximo critico: {critical_m}x). "
                f"GPU: S/ {gpu_price:,.0f} | CPU: S/ {cpu_price:,.0f}. "
                f"Aumenta CPU en ~S/ {diff:.0f} o reduce GPU para evitar desperdicio."
            )
        elif multiplier > max_m:
            # Advertencia: fuera de rango optimo
            errors.append(
                f"ADVERTENCIA: Multiplicador {multiplier:.2f}x esta sobre el optimo ({max_m}x). "
                f"GPU: S/ {gpu_price:,.0f} | CPU: S/ {cpu_price:,.0f}. "
                f"Considera mejorar CPU para aprovechar mejor la GPU."
            )
    else:
        if gpu_price == 0:
            errors.append("ERROR CRITICO: No se detecto GPU en la cotizacion.")
        if cpu_price == 0:
            errors.append("ERROR CRITICO: No se detecto CPU en la cotizacion.")
    
    # 5. VALIDAR PRIORIDAD DEL CASE (3-5% del presupuesto)
    if case_price > 0:
        case_percentage = (case_price / budget) * 100
        details["case_percentage"] = case_percentage
        
        min_case_price = budget * CASE_MIN_PERCENTAGE
        max_case_price = min(budget * CASE_MAX_PERCENTAGE, ABSOLUTE_MAX_CASE)
        
        if case_price > max_case_price:
            diff = case_price - max_case_price
            errors.append(
                f"CASE SOBREVALORADO: Case cuesta S/ {case_price:,.0f} ({case_percentage:.1f}% del presupuesto). "
                f"Maximo permitido: S/ {max_case_price:.0f} ({CASE_MAX_PERCENTAGE*100:.0f}% o S/ {ABSOLUTE_MAX_CASE}). "
                f"Reduce S/ {diff:.0f} y reasigna a GPU/CPU."
            )
        elif case_price < min_case_price:
            errors.append(
                f"CASE INFRAUTILIZADO: Case muy economico (S/ {case_price:,.0f}, {case_percentage:.1f}%). "
                f"Considera usar al menos S/ {min_case_price:.0f} ({CASE_MIN_PERCENTAGE*100:.0f}%) para mejor calidad."
            )
    
    return len(errors) == 0, errors, details

def generate_feedback_prompt(errors, details, attempt_num):
    """
    Genera un mensaje de feedback tecnico para la IA cuando falla la validacion.
    """
    feedback = f"=== VALIDACION FALLIDA (Intento {attempt_num}/{MAX_RETRIES}) ===\n\n"
    feedback += "Debes corregir los siguientes errores tecnicos:\n\n"
    
    for i, error in enumerate(errors, 1):
        feedback += f"{i}. {error}\n\n"
    
    feedback += "--- Diagnostico Actual ---\n"
    feedback += f"• Total cotizado: S/ {details.get('total', 0):,.2f}\n"
    feedback += f"• Presupuesto objetivo: S/ {details.get('budget', 0):,.2f}\n"
    feedback += f"• GPU: S/ {details.get('gpu_price', 0):,.2f}\n"
    feedback += f"• CPU: S/ {details.get('cpu_price', 0):,.2f}\n"
    
    if details.get('multiplier'):
        feedback += f"• Multiplicador GPU/CPU: {details['multiplier']:.2f}x "
        feedback += f"(Rango optimo: {details.get('min_multiplier', 0):.1f}x - {details.get('max_multiplier', 0):.1f}x)\n"
    
    if details.get('case_price'):
        feedback += f"• Case: S/ {details.get('case_price', 0):,.2f} ({details.get('case_percentage', 0):.1f}% del presupuesto)\n"
    
    feedback += "\n--- INSTRUCCIONES DE CORRECCION ---\n"
    feedback += "1. Ajusta los precios para cumplir el multiplicador GPU/CPU correcto\n"
    feedback += "2. Mantén el total dentro del ±10% del presupuesto\n"
    feedback += "3. Case debe ser 3-5% del presupuesto (max S/500)\n"
    feedback += "4. Prioriza GPU > CPU > RAM > Placa > SSD > Fuente > Case\n\n"
    feedback += "Genera una nueva cotizacion corregida en formato JSON."
    
    return feedback

# --- CSS ---
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
        
        .validation-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: bold;
            margin-left: 8px;
        }
        .badge-valid { background: #d4edda; color: #155724; }
        .badge-warning { background: #fff3cd; color: #856404; }
        
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
            
        sys_prompt = """IDENTIDAD: Eres 'Kiwigeek AI', un cotizador tecnico especializado en hardware de PC.

LIMITACIONES ESTRICTAS:
- NO das descripciones largas de productos
- NO realizas ventas directas
- NO envias promociones
- Tu unico trabajo es COTIZAR tecnicamente

PROTOCOLO OBLIGATORIO:
1. Antes de cotizar, SIEMPRE pregunta: "¿Solo Torre o PC Completa?"
2. Si el usuario no lo aclara, marca 'needs_info: true' y pregunta

REGLAS MATEMATICAS DE INGENIERIA:

1. MULTIPLICADOR GPU/CPU (M = Precio GPU / Precio CPU):
   - Presupuesto < S/5,000 (Gama Baja):
     * M debe estar entre 1.7x y 2.0x
     * Ejemplo: Si CPU = S/800, GPU debe estar entre S/1,360 y S/1,600
     * Si M > 2.5x, hay cuello de botella (CPU muy debil)
   
   - Presupuesto S/5,000 - S/10,000 (Gama Media):
     * M debe estar entre 2.2x y 3.0x
     * Ejemplo: Si CPU = S/1,500, GPU debe estar entre S/3,300 y S/4,500
     * Si M > 4.0x, cuello de botella critico
   
   - Presupuesto > S/10,000 (Gama Alta):
     * M puede llegar hasta 5.0x
     * Ejemplo: Si CPU = S/3,000, GPU puede llegar a S/15,000
     * La GPU es el componente dominante

2. PRESUPUESTO (±10%):
   - Si presupuesto = S/6,000, rango valido: S/5,400 - S/6,600
   - NO te alejes mas del 10% del presupuesto solicitado

3. PRIORIDAD DEL CASE:
   - El Case debe representar 3-5% del presupuesto total
   - Limite absoluto: S/500 (nunca exceder)
   - Ejemplo: Si presupuesto = S/8,000, Case = S/240-400
   - Si presupuesto = S/3,000, Case = S/90-150 (no uses S/500)

JERARQUIA DE INVERSION:
1. GPU (componente mas caro, 30-40% del presupuesto)
2. CPU (segundo mas caro, 20-25% del presupuesto)
3. RAM (12-15%)
4. Monitor (solo PC Completa, 10-15%)
5. Placa Madre (8-10%, DEBE ser compatible con CPU)
6. SSD (5-8%)
7. Fuente de Poder (5-7%)
8. Perifericos (solo PC Completa, 3-5%)
9. Case (3-5%, max S/500)

FORMATO DE SALIDA:
- Responde SIEMPRE en JSON
- No calcules totales (Python lo hara)
- Incluye 'name' y 'price' para cada componente
- Usa multiplicadores correctos segun el presupuesto"""
        
        return client.caches.create(
            model=MODEL_ID,
            config=types.CreateCachedContentConfig(
                display_name='kiwi_v9_math_validator',
                system_instruction=sys_prompt,
                contents=[catalog] if catalog else [],
                ttl='7200s'
            )
        ).name, None
    except Exception as e:
        return None, str(e)

def initialize_session(force=False):
    """Inicializa la sesion con persistencia robusta."""
    if "messages" not in st.session_state: 
        st.session_state.messages = []
    
    if "user_budget" not in st.session_state:
        st.session_state.user_budget = None
    
    if "pc_type" not in st.session_state:
        st.session_state.pc_type = None  # "Torre" o "Completa"
    
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
                "content": "¡Hola! Soy **Kiwigeek AI**, tu cotizador tecnico de hardware.\n\nDime tu presupuesto y si necesitas **Solo Torre** o **PC Completa** para generar opciones optimizadas con balance GPU/CPU perfecto."
            })

# Inicializar sesion
initialize_session()

# --- UI (SIDEBAR) ---
with st.sidebar:
    st.image('https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png', use_container_width=True)
    
    # Panel informativo
    st.markdown("""
    <div class="info-box"><div class="info-title-yes">✅ Validacion Tecnica</div>
    <ul class="info-list">
        <li>Multiplicador GPU/CPU matematico</li>
        <li>Balance por rango de presupuesto</li>
        <li>Case: 3-5% del presupuesto (max S/500)</li>
        <li>Margen ±10% garantizado</li>
        <li>Anti cuello de botella automatico</li>
    </ul></div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box"><div class="info-title-no">🚫 Limitaciones</div>
    <ul class="info-list">
        <li>No doy descripciones de productos</li>
        <li>No gestiono ventas directas</li>
        <li>Solo cotizacion tecnica</li>
    </ul></div>
    """, unsafe_allow_html=True)

    # Mostrar estado
    if st.session_state.user_budget:
        min_m, max_m, _ = get_multiplier_range(st.session_state.user_budget)
        st.success(f"💰 Presupuesto: S/ {st.session_state.user_budget:,.0f}")
        st.info(f"🔧 Multiplicador optimo: {min_m}x - {max_m}x")
    
    if st.session_state.pc_type:
        st.info(f"🖥️ Tipo: {st.session_state.pc_type}")
    
    # Promocion
    st.markdown(f"""
    <div class="info-box" style="border: 1px solid #ffd700; background: #fffdf0;">
    <div class="info-title-promo">🎁 Promocion Especial</div>
    <p style="font-size: 0.85rem;">Combo <b>CPU + Placa + RAM + GPU</b> con descuento exclusivo</p>
    <a href="{WHATSAPP_LINK}" target="_blank" class="promo-btn">📲 Reclamar Descuento</a></div>
    """, unsafe_allow_html=True)
    
    if st.button("🗑️ Reiniciar Chat", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
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

# --- INPUT CON LOGICA DE REINTENTO ---
if prompt := st.chat_input("Ej: Tengo S/ 6000 para una PC Completa"):
    # Extraer presupuesto
    detected_budget = extract_budget(prompt)
    if detected_budget and not st.session_state.user_budget:
        st.session_state.user_budget = detected_budget
    
    # Detectar tipo de PC
    prompt_lower = prompt.lower()
    if "completa" in prompt_lower or "pc completa" in prompt_lower:
        st.session_state.pc_type = "PC Completa"
    elif "torre" in prompt_lower or "solo torre" in prompt_lower:
        st.session_state.pc_type = "Solo Torre"
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"): 
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=AVATAR_URL):
        with st.spinner("Calculando multiplicadores GPU/CPU y validando balance..."):
            try:
                if "chat_session" not in st.session_state:
                    initialize_session(force=True)
                
                # BUCLE DE REINTENTO CON VALIDACION
                valid_response = None
                retry_count = 0
                current_prompt = prompt
                
                while retry_count < MAX_RETRIES and not valid_response:
                    response = st.session_state.chat_session.send_message(current_prompt)
                    data = json.loads(response.text)
                    
                    # Si pide info o no es cotizacion, aceptar
                    if data.get("needs_info") or not data.get("is_quote"):
                        valid_response = data
                        break
                    
                    # Si es cotizacion, VALIDAR con matematica de ingenieria
                    if data.get("quotes") and st.session_state.user_budget:
                        all_valid = True
                        accumulated_errors = []
                        last_details = {}
                        
                        for quote in data["quotes"]:
                            is_valid, errors, details = validate_build(
                                st.session_state.user_budget,
                                quote.get("components", [])
                            )
                            
                            if not is_valid:
                                all_valid = False
                                accumulated_errors.extend(errors)
                                last_details = details
                        
                        if all_valid:
                            valid_response = data
                        else:
                            retry_count += 1
                            if retry_count < MAX_RETRIES:
                                # Generar feedback tecnico interno
                                current_prompt = generate_feedback_prompt(
                                    accumulated_errors,
                                    last_details,
                                    retry_count
                                )
                                import time
                                time.sleep(0.3)
                            else:
                                # Max intentos alcanzado
                                st.warning(f"⚠️ Despues de {MAX_RETRIES} intentos, la validacion tecnica no paso. Mostrando mejor aproximacion con advertencias:")
                                for err in accumulated_errors[:3]:  # Mostrar primeros 3 errores
                                    st.error(f"🔧 {err}")
                                valid_response = data
                    else:
                        # Sin presupuesto detectado, aceptar
                        valid_response = data
                
                # RENDERIZAR RESPUESTA FINAL
                if valid_response:
                    data = valid_response
                    final_text = ""
                    
                    if data.get("needs_info"):
                        final_text = data.get("message", "Por favor, indicame tu presupuesto y si necesitas Solo Torre o PC Completa.")
                    elif data.get("is_quote") and data.get("quotes"):
                        final_text = data.get("message", "He optimizado tu build con validacion matematica:") + "\n\n---\n"
                        
                        for q in data["quotes"]:
                            components = q.get("components", [])
                            total = sum(float(item.get("price", 0)) for item in components)
                            
                            # Calcular metricas de validacion
                            prices = extract_component_prices(components)
                            gpu_price = prices["gpu_price"]
                            cpu_price = prices["cpu_price"]
                            case_price = prices["case_price"]
                            
                            multiplier = calculate_gpu_cpu_multiplier(gpu_price, cpu_price) if cpu_price > 0 else 0
                            
                            # Encabezado de la opcion
                            final_text += f"### {q.get('title', 'Opcion')}\n"
                            final_text += f"**Estrategia:** {q.get('strategy', 'Balance optimizado')}\n\n"
                            
                            # Listar componentes
                            for item in components:
                                link = f" - [Ver Aqui]({item['url']})" if item.get('url') else ""
                                insight = f"\n  💡 *{item['insight']}*" if item.get('insight') else ""
                                final_text += f"- {item['name']} - S/ {item['price']:,.2f}{link}{insight}\n"
                            
                            # Totales y metricas
                            final_text += f"\n**💰 TOTAL: S/ {total:,.2f}**"
                            
                            if st.session_state.user_budget:
                                diff = total - st.session_state.user_budget
                                margin_pct = (diff / st.session_state.user_budget) * 100
                                
                                if abs(margin_pct) <= 10:
                                    badge = "✅ Dentro del margen"
                                elif margin_pct > 10:
                                    badge = "⚠️ Sobre presupuesto"
                                else:
                                    badge = "⚠️ Bajo presupuesto"
                                
                                final_text += f" ({margin_pct:+.1f}%) {badge}\n"
                            else:
                                final_text += "\n"
                            
                            # Mostrar multiplicador GPU/CPU
                            if multiplier > 0:
                                min_m, max_m, critical_m = get_multiplier_range(st.session_state.user_budget or 5000)
                                
                                if min_m <= multiplier <= max_m:
                                    status = "✅ Balance optimo"
                                elif multiplier < min_m:
                                    status = "⚠️ GPU debil"
                                elif multiplier > critical_m:
                                    status = "❌ Cuello de botella"
                                else:
                                    status = "⚠️ Fuera de rango"
                                
                                final_text += f"**🔧 Multiplicador GPU/CPU:** {multiplier:.2f}x {status}\n"
                                final_text += f"   • GPU: S/ {gpu_price:,.2f} | CPU: S/ {cpu_price:,.2f}\n"
                            
                            # Info del case
                            if case_price > 0 and st.session_state.user_budget:
                                case_pct = (case_price / st.session_state.user_budget) * 100
                                final_text += f"**🏠 Case:** S/ {case_price:,.2f} ({case_pct:.1f}% del presupuesto)\n"
                            
                            final_text += "\n---\n"
                    else:
                        final_text = data.get("message", "Entendido. ¿En que mas puedo ayudarte?")
                    
                    st.markdown(final_text)
                    st.session_state.messages.append({"role": "assistant", "content": final_text})
                
            except json.JSONDecodeError as e:
                st.error("❌ Error al procesar respuesta de la IA. Por favor, reintenta.")
                st.exception(e)
            except Exception as e:
                try:
                    initialize_session(force=True)
                    st.markdown("🔄 Conexion restablecida automaticamente. Por favor, reintenta tu mensaje.")
                except:
                    st.error("❌ Error de conexion. Pulsa 'Reiniciar Chat' e intenta nuevamente.")
                    st.exception(e)
