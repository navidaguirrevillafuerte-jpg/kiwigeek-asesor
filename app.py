import streamlit as st
import os
import re
import json
import time
from google import genai
from google.genai import types

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Kiwigeek AI - Cotizador de Hardware",
    page_icon="https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- CONSTANTES ---
AVATAR_URL = "https://kiwigeekperu.com/wp-content/uploads/2026/01/gatitow.webp"
WHATSAPP_LINK = "https://api.whatsapp.com/send/?phone=51939081940&text=Hola%2C+vengo+del+Chat+AI+y+quiero+reclamar+mi+descuento+especial+por+PC+Completa&type=phone_number&app_absent=0"

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
        #MainMenu, footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# --- CONFIGURACIÓN DE IA ---
def get_api_key():
    try: return st.secrets["GEMINI_API_KEY"]
    except: return os.getenv("GEMINI_API_KEY", "")

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
                                "insight": {"type": "STRING"},
                                "type": {"type": "STRING", "enum": ["CPU", "GPU", "RAM", "MOBO", "SSD", "PSU", "CASE", "MONITOR", "PERIPHERAL"]}
                            }
                        }
                    }
                }
            }
        }
    }
}

@st.cache_resource
def setup_kiwi_brain():
    try:
        catalog = ""
        if os.path.exists('catalogo_kiwigeek.json'):
            with open('catalogo_kiwigeek.json', 'r', encoding='utf-8') as f:
                catalog = f.read()
            
        sys_prompt = """ROL: Eres 'Kiwigeek AI', Ingeniero Senior de Hardware y Cotizador Experto.

REGLAS DE INTERACCIÓN:
1. ANTES DE COTIZAR: Si el usuario no aclara si es "Solo Torre" o "PC Completa", pide la información (needs_info: true).
2. CANTIDAD: Ofrece SIEMPRE 3 opciones que se ajusten estrictamente al presupuesto.
3. LIMITACIONES: NO des descripciones de productos, NO gestiones ventas, NO envíes promociones.

REGLAS DE INGENIERÍA (EXTRICTAS):
4. PRESUPUESTO: Cada opción debe estar entre [Presupuesto - 10%] y [Presupuesto + 10%]. OBLIGATORIO.
5. PRECIO GPU vs CPU: La GPU DEBE ser siempre más cara que la CPU. Nunca igual, nunca menor.
6. ESCATIMAR EN CASE: Máximo S/ 250 para el case. Es lo menos prioritario.
7. JERARQUÍA DE PRIORIDAD:
   - Torre: GPU > CPU > RAM > Placa > SSD > Fuente > Case.
   - Completa: GPU > CPU > RAM > Monitor > Placa > SSD > Fuente > Periféricos > Case.

ESTRUCTURA: Salida JSON puro. No calcules totales."""
        
        return client.caches.create(
            model=MODEL_ID,
            config=types.CreateCachedContentConfig(
                display_name='kiwi_v8_validation_layer',
                system_instruction=sys_prompt,
                contents=[catalog] if catalog else [],
                ttl='7200s'
            )
        ).name, None
    except Exception as e:
        return None, str(e)

def initialize_session(force=False):
    if "messages" not in st.session_state: st.session_state.messages = []
    if force or "chat_session" not in st.session_state:
        cache_name, err = setup_kiwi_brain()
        config = types.GenerateContentConfig(temperature=0.1, response_mime_type="application/json", response_schema=RESPONSE_SCHEMA)
        if cache_name: config.cached_content = cache_name
        st.session_state.chat_session = client.chats.create(model=MODEL_ID, config=config)
        if not st.session_state.messages:
            st.session_state.messages.append({"role": "assistant", "content": "¡Hola! Soy **Kiwigeek AI**. Dime tu presupuesto y si buscas **Solo Torre** o **PC Completa**."})

initialize_session()

# --- LÓGICA DE VALIDACIÓN ---
def extract_budget(text):
    numbers = re.findall(r"S/ ?(\d+[\d,.]*)", text)
    if not numbers: numbers = re.findall(r"(\d+[\d,.]*)", text)
    if numbers:
        try: return float(numbers[0].replace(',', ''))
        except: return None
    return None

def validate_response(data, target_budget):
    if not data.get("is_quote") or not data.get("quotes"): return True, ""
    
    errors = []
    for i, q in enumerate(data["quotes"]):
        total = sum(float(c.get("price", 0)) for c in q.get("components", []))
        
        # Validación Presupuesto (10% margen)
        if target_budget:
            diff = abs(total - target_budget) / target_budget
            if diff > 0.10:
                errors.append(f"Opción {i+1}: El total S/ {total:,.2f} se desvía más del 10% de S/ {target_budget:,.2f}.")

        # Validación GPU > CPU
        cpu_price = 0
        gpu_price = 0
        for c in q.get("components", []):
            ctype = c.get("type", "").upper()
            if "CPU" in ctype or "PROCESADOR" in c.get("name", "").upper(): cpu_price = float(c.get("price", 0))
            if "GPU" in ctype or "TARJETA" in c.get("name", "").upper() or "VIDEO" in c.get("name", "").upper(): gpu_price = float(c.get("price", 0))
        
        if gpu_price > 0 and cpu_price > 0 and gpu_price <= cpu_price:
            errors.append(f"Opción {i+1}: La GPU (S/ {gpu_price}) debe ser más cara que la CPU (S/ {cpu_price}).")
            
    if errors: return False, "\n".join(errors)
    return True, ""

# --- UI SIDEBAR ---
with st.sidebar:
    st.image('https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png', use_container_width=True)
    st.markdown("""
    <div class="info-box"><div class="info-title-yes">✅ Cotizador Especializado</div>
    <ul class="info-list"><li>Maximización de GPU/CPU.</li><li>Ingeniería de Hardware Real.</li><li>Validación de Presupuesto.</li></ul></div>
    <div class="info-box"><div class="info-title-no">🚫 Cosas que NO hago</div>
    <ul class="info-list"><li>Descripciones de productos.</li><li>Ventas directas.</li><li>Envío de promociones.</li></ul></div>
    """, unsafe_allow_html=True)
    if st.button("🗑️ Reiniciar Chat", use_container_width=True):
        st.session_state.messages = []
        if "chat_session" in st.session_state: del st.session_state["chat_session"]
        st.rerun()

# --- HEADER ---
st.markdown('<div style="text-align:center;"><img src="https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png" height="120"><h1 class="neon-title">AI</h1></div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=AVATAR_URL if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])

if prompt := st.chat_input("Dime tu presupuesto y tipo de PC..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"): st.markdown(prompt)
    
    target_budget = extract_budget(prompt) or st.session_state.get("last_budget")
    if target_budget: st.session_state.last_budget = target_budget

    with st.chat_message("assistant", avatar=AVATAR_URL):
        with st.spinner("Verificando compatibilidad y precios..."):
            try:
                if "chat_session" not in st.session_state: initialize_session(force=True)
                
                # Bucle de validación (máximo 3 reintentos)
                current_prompt = prompt
                valid = False
                attempts = 0
                while not valid and attempts < 3:
                    response = st.session_state.chat_session.send_message(current_prompt)
                    data = json.loads(response.text)
                    
                    is_ok, err_msg = validate_response(data, target_budget)
                    if is_ok:
                        valid = True
                    else:
                        attempts += 1
                        current_prompt = f"La cotización anterior tiene errores: {err_msg}. Por favor, corrígela siguiendo las reglas: 3 opciones, GPU > CPU y total +/- 10% de S/ {target_budget}."
                
                final_text = ""
                if data.get("needs_info"):
                    final_text = data.get("message")
                elif data.get("is_quote") and data.get("quotes"):
                    final_text = data.get("message", "Aquí tienes 3 opciones optimizadas:") + "\n\n---\n"
                    for q in data["quotes"]:
                        total = sum(float(item.get("price", 0)) for item in q.get("components", []))
                        final_text += f"### {q.get('title')}\n**Estrategia:** {q.get('strategy')}\n\n"
                        for item in q.get("components", []):
                            link = f" - [Ver Aquí]({item['url']})" if item.get('url') else ""
                            insight = f"\n  💡 *{item['insight']}*" if item.get('insight') else ""
                            final_text += f"- {item['name']} - S/ {item.get('price', 0):,}{link}{insight}\n"
                        final_text += f"\n**TOTAL CALCULADO: S/ {total:,.2f}**\n\n---\n"
                else:
                    final_text = data.get("message", "Entendido. ¿Alguna otra consulta?")

                st.markdown(final_text)
                st.session_state.messages.append({"role": "assistant", "content": final_text})
                
            except Exception as e:
                st.error("Error de conexión. Intenta enviar tu mensaje de nuevo.")
                initialize_session(force=True)
