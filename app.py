import streamlit as st
import os
import re
import json
from google import genai
from google.genai import types

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Kiwigeek AI - Cotizador Simple",
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

        .stChatMessage { background: transparent !important; border: none !important; }
        .stMarkdown h3 { margin-top: 20px; font-size: 1.2rem; font-weight: bold; color: #000 !important; }
        .stMarkdown a { color: #0066cc !important; text-decoration: underline; }
        .stMarkdown li { background: transparent !important; padding: 2px 0 !important; border: none !important; color: #000 !important; }
        .stMarkdown p { color: #000 !important; }

        [data-testid="stSidebar"] { background-color: #f8f9fa; }
        .info-box { background: #fff; border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 15px; }
        .info-title-yes { color: #28a745; font-weight: bold; border-bottom: 2px solid #28a745; }
        .info-title-no { color: #d9534f; font-weight: bold; border-bottom: 2px solid #d9534f; }
        .info-title-promo { color: #d4ac0d; font-weight: bold; border-bottom: 2px solid #ffd700; }
        
        .promo-btn {
            display: block; width: 100%; text-align: center; background-color: #25D366;
            color: white !important; padding: 8px 0; border-radius: 5px; text-decoration: none !important;
            font-weight: bold; margin-top: 10px;
        }
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

# Esquema para la respuesta estructurada
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "is_quote": {"type": "BOOLEAN"},
        "greeting": {"type": "STRING"},
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
        # Intentar leer catálogo si existe
        catalog = ""
        if os.path.exists('catalogo_kiwigeek.json'):
            with open('catalogo_kiwigeek.json', 'r', encoding='utf-8') as f:
                catalog = f.read()
            
        sys_prompt = """ROL: Eres 'Kiwigeek AI', Ingeniero de Hardware Senior.
OBJETIVO: Generar 3 opciones de PC optimizadas.

REGLAS DE INGENIERÍA (CRÍTICO):
1. COMPATIBILIDAD: Verifica que el Socket del CPU coincida con la Placa, que la RAM sea compatible (DDR4/DDR5) y que la Fuente (PSU) tenga los Watts suficientes.
2. OPTIMIZACIÓN: Evita cuellos de botella (bottlenecks). No pongas un i9 con una GTX 1650, ni un i3 con una RTX 4090.
3. PRESUPUESTO: Las 3 opciones deben estar dentro del rango (+15% máx).
4. ESTRUCTURA: Devuelve la respuesta en formato JSON puro.

No calcules el total. Python lo hará. Asegúrate de que cada componente tenga su precio individual real."""
        
        return client.caches.create(
            model=MODEL_ID,
            config=types.CreateCachedContentConfig(
                display_name='kiwi_v3_structured',
                system_instruction=sys_prompt,
                contents=[catalog] if catalog else [],
                ttl='7200s'
            )
        ).name, None
    except Exception as e:
        return None, str(e)

def initialize_session():
    if "messages" not in st.session_state: st.session_state.messages = []
    if "chat_session" not in st.session_state:
        cache_name, err = setup_kiwi_brain()
        config = types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA
        )
        if cache_name: config.cached_content = cache_name
        st.session_state.chat_session = client.chats.create(model=MODEL_ID, config=config)
        if not st.session_state.messages:
            st.session_state.messages.append({"role": "assistant", "content": "Hola. Soy Kiwigeek AI. ¿Qué presupuesto tienes para tu nueva PC?"})

initialize_session()

# --- SIDEBAR ---
with st.sidebar:
    st.image('https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png', use_container_width=True)
    st.markdown("""
    <div class="info-box"><div class="info-title-yes">✅ Lo que SÍ hago</div>
    <ul class="info-list"><li>Cotizo PCs compatibles.</li><li>Evito cuellos de botella.</li><li>Precios actualizados.</li></ul></div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="info-box" style="border: 1px solid #ffd700; background: #fffdf0;">
    <div class="info-title-promo">🎁 ¡Promoción Especial!</div>
    <p style="font-size: 0.85rem;">Compra <b>CPU + Placa + RAM + GPU</b> y obtén un descuento exclusivo.</p>
    <a href="{WHATSAPP_LINK}" target="_blank" class="promo-btn">📲 Reclamar Descuento</a></div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box"><div class="info-title-no">🚫 Lo que NO hago</div>
    <ul class="info-list"><li>No hago reparaciones físicas.</li><li>No aceptamos partes en pago.</li></ul></div>
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

# --- CHAT DISPLAY ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=AVATAR_URL if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])

# --- CHAT LOGIC ---
if prompt := st.chat_input("Ej: Tengo S/ 3500 para una PC de diseño..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"): st.markdown(prompt)

    with st.chat_message("assistant", avatar=AVATAR_URL):
        with st.spinner("Ingeniería en proceso..."):
            try:
                response = st.session_state.chat_session.send_message(prompt)
                data = json.loads(response.text)
                
                final_text = ""
                if data.get("greeting"):
                    final_text += data["greeting"] + "\n\n"
                
                if data.get("is_quote") and data.get("quotes"):
                    final_text += "Aquí tienes 3 opciones optimizadas para tu presupuesto:\n\n---\n"
                    for q in data["quotes"]:
                        total = sum(item["price"] for item in q["components"])
                        final_text += f"### {q['title']}\n"
                        final_text += f"**Estrategia:** {q['strategy']}\n\n"
                        for item in q["components"]:
                            link_part = f" - [Ver Aquí]({item['url']})" if item.get('url') else ""
                            insight_part = f"\n  💡 *{item['insight']}*" if item.get('insight') else ""
                            final_text += f"- {item['name']} - S/ {item['price']:,}{link_part}{insight_part}\n"
                        
                        final_text += f"\n**TOTAL CALCULADO: S/ {total:,.2f}**\n\n---\n"
                
                if not final_text: final_text = "Entendido. ¿En qué más puedo ayudarte con tu hardware?"
                
                st.markdown(final_text)
                st.session_state.messages.append({"role": "assistant", "content": final_text})
                
            except Exception as e:
                st.error(f"Error técnico: {str(e)}. Intenta reiniciar el chat.")
