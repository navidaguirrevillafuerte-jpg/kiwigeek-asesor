import streamlit as st
import os
import json
from google import genai
from google.genai import types

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Kiwigeek AI - Hardware Engineer",
    page_icon="🥝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CONSTANTES DE MARCA ---
COLORS = {
    "kiwi_green": "#00FF41",
    "kiwi_blue": "#0066FF",
    "bg_dark": "#1a1a1a",
    "bg_card": "#2d2d2d"
}
AVATAR_URL = "https://kiwigeekperu.com/wp-content/uploads/2026/01/gatitow.webp"

# --- CSS MEJORADO ---
def apply_custom_styles():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        * {{ font-family: 'Inter', sans-serif !important; }}
        
        /* Título Neón Animado */
        .neon-title {{
            color: {COLORS['kiwi_green']} !important;
            text-shadow: 0 0 10px {COLORS['kiwi_green']}55, 0 0 20px {COLORS['kiwi_green']}33;
            text-align: center;
            font-weight: 800 !important;
            font-size: 2.8rem !important;
            margin-bottom: 0px;
        }}

        /* Contenedores de Mensajes */
        .stChatMessage {{
            border-radius: 15px !important;
            border: 1px solid #333 !important;
            padding: 15px !important;
            margin-bottom: 10px !important;
        }}
        
        [data-testid="stChatMessageAssistant"] {{
            background: rgba(0, 255, 65, 0.05) !important;
            border-left: 4px solid {COLORS['kiwi_green']} !important;
        }}

        [data-testid="stChatMessageUser"] {{
            background: rgba(0, 102, 255, 0.05) !important;
            border-left: 4px solid {COLORS['kiwi_blue']} !important;
        }}

        /* Input del Chat */
        .stChatInputContainer {{
            padding-bottom: 20px !important;
        }}

        /* Botón de reset */
        .reset-btn {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
        }}
        </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# --- LÓGICA DE CLIENTE Y CACHE ---
def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except:
        # Fallback para desarrollo local
        return os.getenv("GEMINI_API_KEY", "")

client = genai.Client(api_key=get_api_key())
MODEL_ID = 'models/gemini-2.0-flash'

@st.cache_resource
def setup_kiwi_brain():
    """Inicializa el contenido cacheado para ahorrar tokens."""
    try:
        path = 'catalogo_kiwigeek.json'
        if not os.path.exists(path):
            return None, "Archivo de catálogo no encontrado."

        with open(path, 'r', encoding='utf-8') as f:
            catalog_data = f.read()

        system_instruction = (
            "ROL: Eres 'Kiwigeek AI', Ingeniero de Hardware y experto en optimización de presupuestos.\n"
            "OBJETIVO: Ayudar al usuario a configurar su PC ideal usando estrictamente el catálogo adjunto.\n\n"
            "REGLAS CRÍTICAS:\n"
            "1. FORMATO: Usa tablas o listas con negritas para precios.\n"
            "2. LINKS: Cada producto debe incluir su URL de compra directa.\n"
            "3. ESTRATEGIA: Presenta siempre 3 opciones (Económica, Equilibrada, Máximo Rendimiento).\n"
            "4. UPSELLING: Si el presupuesto lo permite, justifica por qué subir a una mejor GPU o Fuente de poder.\n"
            "5. CIERRE: Recuerda el descuento exclusivo por PC completa al final."
        )

        # Crear cache con TTL de 2 horas
        cache = client.caches.create(
            model=MODEL_ID,
            config=types.CreateCachedContentConfig(
                display_name='kiwigeek_v1',
                system_instruction=system_instruction,
                contents=[catalog_data],
                ttl='7200s',
            )
        )
        return cache.name, None
    except Exception as e:
        return None, str(e)

# --- INICIALIZACIÓN DE SESIÓN ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_session" not in st.session_state:
    cache_name, error = setup_kiwi_brain()
    if error:
        st.error(f"⚠️ Error de Configuración: {error}")
        st.stop()
    
    st.session_state.chat_session = client.chats.create(
        model=MODEL_ID,
        config=types.GenerateContentConfig(
            cached_content=cache_name,
            temperature=0.2,
            top_p=0.9
        )
    )
    # Mensaje de bienvenida
    st.session_state.messages.append({
        "role": "assistant",
        "content": "¡Hola! Soy el asistente de **Kiwigeek**. 🐱\n\n¿Buscas una PC para gaming, diseño o trabajo pesado? Dime tu presupuesto y diseñaremos la mejor configuración para ti."
    })

# --- INTERFAZ ---
# Sidebar para acciones
with st.sidebar:
    st.image('https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png')
    st.markdown("---")
    if st.button("🗑️ Limpiar Conversación", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Header Principal
st.markdown("<h1 class='neon-title'>KIWIGEEK AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Ingeniería de hardware de alto nivel</p>", unsafe_allow_html=True)

# Mostrar historial
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message(msg["role"], avatar=AVATAR_URL):
            st.markdown(msg["content"])
    else:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Entrada de usuario
if prompt := st.chat_input("Ej: Tengo S/ 4000 para una PC de Streaming..."):
    # Añadir mensaje de usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Respuesta de la IA
    with st.chat_message("assistant", avatar=AVATAR_URL):
        placeholder = st.empty()
        with st.spinner("🔍 Analizando stock y compatibilidad..."):
            try:
                response = st.session_state.chat_session.send_message(prompt)
                full_response = response.text
                placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Error en la respuesta: {e}")

# Footer
st.markdown("<br><hr><p style='text-align: center; color: #555;'>© 2025 Kiwigeek Perú - Hardware for Professionals</p>", unsafe_allow_html=True)
