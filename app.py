import streamlit as st
import os
import re
import json
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

# --- CSS MIXTO (Header Neón + Chat Limpio + Sidebar Mejorado) ---
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
                                "insight": {"type": "STRING"}
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
1. ANTES DE COTIZAR: Si el usuario no aclara si es "Solo Torre" o "PC Completa", pide la información y marca 'needs_info: true'.
2. CANTIDAD: Debes ofrecer 1 opcion equilibrada en el presupuesto y preguntar luego al usuario si quiere otra opción con otra marca
3. LIMITACIONES: NO des descripciones largas de productos, NO gestiones ventas directas y NO envíes promociones. Tu trabajo es COTIZAR técnicamente lo mas cercano al presupuesto OBLIGATORIAMENTE
4. JERARQUÍA DE INVERSIÓN (De mayor a menor gasto/importancia):
   - Solo Torre: GPU DEBE SER MAS CARO QUE LA CPU > CPU > RAM > Placa Madre (compatible con la cpu) > SSD > Fuente de Poder > Case económico maximo 250 soles
   - PC Completa: GPU DEBE SER MAS CARO QUE LA CPU > CPU > RAM > Monitor > Placa Madre (compatible con la cpu) > SSD > Fuente de Poder > Periféricos > Case económico maximo 250 soles
6. CUELLO DE BOTELLA: Garantiza equilibrio. No satures una GPU potente con un CPU insuficiente.
7. PRESUPUESTO: El total de cada opción no debe desviarse más del 10% del presupuesto indicado.

ESTRUCTURA: Salida en JSON. No calcules totales, Python los calculará."""
        
        return client.caches.create(
            model=MODEL_ID,
            config=types.CreateCachedContentConfig(
                display_name='kiwi_v7_stable_priority',
                system_instruction=sys_prompt,
                contents=[catalog] if catalog else [],
                ttl='7200s'
            )
        ).name, None
    except Exception as e:
        return None, str(e)

def initialize_session(force=False):
    """Inicializa la sesión de chat con verificación de estado para evitar caídas."""
    if "messages" not in st.session_state: 
        st.session_state.messages = []
    
    # Si force es True o la sesión no existe, reiniciamos
    if force or "chat_session" not in st.session_state:
        cache_name, err = setup_kiwi_brain()
        config = types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA
        )
        if cache_name: config.cached_content = cache_name
        st.session_state.chat_session = client.chats.create(model=MODEL_ID, config=config)
        
        if not st.session_state.messages:
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "¡Hola! Soy **Kiwigeek AI**. Dime tu presupuesto y si buscas **Solo Torre** o **PC Completa** para darte opciones optimizadas."
            })

# Llamar siempre al inicio para asegurar que el objeto chat_session esté vivo
initialize_session()

# --- UI (SIDEBAR) ---
with st.sidebar:
    st.image('https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png', use_container_width=True)
    
    # Panel ✅ Lo que SÍ hago
    st.markdown("""
    <div class="info-box"><div class="info-title-yes">✅ Cotizador Especializado</div>
    <ul class="info-list">
        <li>Maximización de GPU/CPU.</li>
        <li>Ahorro inteligente en Case.</li>
        <li>Presupuesto Real (Margen 10%).</li>
    </ul></div>
    """, unsafe_allow_html=True)

    # Panel 🚫 Lo que NO hago (ACTUALIZADO)
    st.markdown("""
    <div class="info-box"><div class="info-title-no">🚫 Cosas que NO hago</div>
    <ul class="info-list">
        <li>Dar descripciones de productos.</li>
        <li>Ventas directas.</li>
        <li>Envío de promociones.</li>
    </ul></div>
    """, unsafe_allow_html=True)

    # Panel 🎁 Promoción
    st.markdown(f"""
    <div class="info-box" style="border: 1px solid #ffd700; background: #fffdf0;">
    <div class="info-title-promo">🎁 ¡Promoción Especial!</div>
    <p style="font-size: 0.85rem;">Compra tu combo <b>CPU + Placa + RAM + GPU</b> y obtén un descuento exclusivo.</p>
    <a href="{WHATSAPP_LINK}" target="_blank" class="promo-btn">📲 Reclamar Descuento</a></div>
    """, unsafe_allow_html=True)
    
    if st.button("🗑️ Reiniciar Chat", use_container_width=True):
        st.session_state.messages = []
        if "chat_session" in st.session_state: del st.session_state["chat_session"]
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

# Input de Chat
if prompt := st.chat_input("Dime tu presupuesto y tipo de PC..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"): st.markdown(prompt)

    with st.chat_message("assistant", avatar=AVATAR_URL):
        with st.spinner("Analizando componentes y optimizando inversión..."):
            try:
                # Verificación de seguridad antes de enviar
                if "chat_session" not in st.session_state:
                    initialize_session(force=True)
                
                response = st.session_state.chat_session.send_message(prompt)
                data = json.loads(response.text)
                final_text = ""
                
                if data.get("needs_info"):
                    final_text = data.get("message", "Por favor, indícame si deseas Solo Torre o PC Completa.")
                elif data.get("is_quote") and data.get("quotes"):
                    final_text = data.get("message", "He maximizado tu inversión en GPU y CPU con estas 3 opciones:") + "\n\n---\n"
                    for q in data["quotes"]:
                        total = sum(float(item.get("price", 0)) for item in q.get("components", []))
                        final_text += f"### {q.get('title', 'Opción')}\n"
                        final_text += f"**Estrategia:** {q.get('strategy', '')}\n\n"
                        for item in q.get("components", []):
                            link = f" - [Ver Aquí]({item['url']})" if item.get('url') else ""
                            insight = f"\n  💡 *{item['insight']}*" if item.get('insight') else ""
                            final_text += f"- {item['name']} - S/ {item['price']:,}{link}{insight}\n"
                        final_text += f"\n**TOTAL CALCULADO: S/ {total:,.2f}**\n\n---\n"
                else:
                    final_text = data.get("message", "Entendido. ¿En qué más puedo ayudarte?")
                
                st.markdown(final_text)
                st.session_state.messages.append({"role": "assistant", "content": final_text})
                
            except Exception:
                # Si algo falla, forzamos reinicio y reintento una sola vez
                try:
                    initialize_session(force=True)
                    response = st.session_state.chat_session.send_message(prompt)
                    data = json.loads(response.text)
                    # Lógica de renderizado repetida para el reintento exitoso
                    if data.get("is_quote"):
                        # ... (simplificado para el catch)
                        st.markdown("Conexión restablecida automáticamente. Por favor vuelve a enviar el mensaje para procesar la cotización.")
                except:
                    st.error("La conexión se ha interrumpido por inactividad. Por favor, pulsa 'Reiniciar Chat' o intenta enviar el mensaje nuevamente.")

