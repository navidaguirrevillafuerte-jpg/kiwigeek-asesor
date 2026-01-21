import streamlit as st
import os
import re
from google import genai
from google.genai import types

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Kiwigeek AI - Cotizador Simple",
    page_icon="https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CONSTANTES ---
AVATAR_URL = "https://kiwigeekperu.com/wp-content/uploads/2026/01/gatitow.webp"
WHATSAPP_LINK = "https://api.whatsapp.com/send/?phone=51939081940&text=Hola%2C+me+gustar%C3%ADa+saber+m%C3%A1s+de+sus+productos&type=phone_number&app_absent=0"

# --- CSS MIXTO (Header Neón + Chat Limpio) ---
def apply_custom_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
        
        /* Fuente general */
        * { 
            font-family: 'Inter', sans-serif !important; 
        }
        
        /* --- ESTILO NEÓN PARA EL HEADER (Recuperado) --- */
        .neon-title {
            color: #00FF41 !important;
            text-shadow: 0 0 20px rgba(0,255,65,0.5);
            text-align: center;
            font-weight: 900 !important;
            font-size: 3.5rem !important;
            margin: 0;
            line-height: 1.2;
        }

        /* --- ESTILO LIMPIO PARA EL CHAT --- */
        
        /* Ajustes para que el chat se vea limpio */
        .stChatMessage { 
            background: transparent !important; 
            border: none !important;
        }

        /* Eliminar estilos extraños de Markdown */
        .stMarkdown h3 {
            margin-top: 20px;
            font-size: 1.2rem;
            font-weight: bold;
            color: #000 !important; /* Títulos del chat en negro */
        }
        
        /* Links simples y subrayados */
        .stMarkdown a {
            color: #0066cc !important; /* Azul estándar de link */
            text-decoration: underline;
        }

        /* Listas simples sin cajas */
        .stMarkdown li {
            background: transparent !important;
            padding: 5px 0 !important;
            margin: 0 !important;
            border: none !important;
            list-style-type: disc !important;
            color: #000 !important; /* Texto de lista en negro */
        }
        
        /* Texto normal en negro */
        .stMarkdown p {
            color: #000 !important;
        }
        </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# --- DATOS DUMMY (Crea el archivo si no existe) ---
if not os.path.exists('catalogo_kiwigeek.json'):
    with open('catalogo_kiwigeek.json', 'w') as f:
        import json
        json.dump({"products": []}, f)

# --- LIMPIEZA DE RESPUESTA ---
def clean_response(text):
    """Limpia cualquier código HTML que la IA intente generar"""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('```html', '').replace('```', '')
    return text.strip()

# --- CONFIGURACIÓN DE IA ---
def get_api_key():
    try: 
        return st.secrets["GEMINI_API_KEY"]
    except: 
        return os.getenv("GEMINI_API_KEY", "")

api_key = get_api_key()
if not api_key:
    with st.sidebar:
        st.warning("⚠️ API Key no encontrada")
        st.stop()

client = genai.Client(api_key=api_key)
MODEL_ID = 'models/gemini-2.0-flash'

@st.cache_resource
def setup_kiwi_brain():
    """Configura el cerebro con instrucciones para RESPUESTAS PLANAS"""
    try:
        with open('catalogo_kiwigeek.json', 'r', encoding='utf-8') as f: 
            catalog = f.read()
            
        sys_prompt = """ROL: Eres 'Kiwigeek AI', vendedor de hardware.
OBJETIVO: Dar cotizaciones directas, simples y sin adornos.

REGLAS DE FORMATO (ESTRICTAS):
1. NO uses negritas (**) para todo, solo para títulos de sección.
2. NO uses cursivas ni bloques de código.
3. Formato de línea de producto: "Nombre del Producto - Precio - [Ver Link](url)"
4. Usa listas simples (-).
5. Mantén un tono profesional y directo.

EJEMPLO DE RESPUESTA DESEADA:
Hola, aquí tienes una opción para tu presupuesto:

Opción Económica:
- Procesador AMD Ryzen 5 5600G - S/ 450 - [Ver Aquí](url)
- Placa Asus Prime A520M - S/ 280 - [Ver Aquí](url)
- Memoria Ram 8GB 3200Mhz - S/ 120 - [Ver Aquí](url)
- Disco SSD 500GB NVMe - S/ 150 - [Ver Aquí](url)
- Case con Fuente 500W - S/ 180 - [Ver Aquí](url)

Total: S/ 1,180

Si deseas comprar, escríbenos al WhatsApp.
"""
        
        return client.caches.create(
            model=MODEL_ID,
            config=types.CreateCachedContentConfig(
                display_name='kiwigeek_simple_text',
                system_instruction=sys_prompt,
                contents=[catalog],
                ttl='7200s'
            )
        ).name, None
    except Exception as e:
        return None, str(e)

# --- APP MAIN LOOP ---
if "messages" not in st.session_state: 
    st.session_state.messages = []

if "chat_session" not in st.session_state:
    cache_name, err = setup_kiwi_brain()
    if err and "catalogo" not in err: 
        st.error(err)
        st.stop()
    
    config = types.GenerateContentConfig(
        temperature=0.1, # Temperatura baja para ser más "robot" y directo
        top_p=0.80, 
        max_output_tokens=8192
    )
    if cache_name: 
        config.cached_content = cache_name
    
    st.session_state.chat_session = client.chats.create(model=MODEL_ID, config=config)
    
    # Mensaje de bienvenida simple
    if not st.session_state.messages:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hola. Dime qué necesitas cotizar y te daré los precios y links."
        })

# --- UI ---
with st.sidebar:
    st.image('https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png')
    if st.button("🗑️ Reiniciar Chat", use_container_width=True):
        st.session_state.messages = []
        if "chat_session" in st.session_state:
            del st.session_state["chat_session"]
        st.rerun()

# HEADER CON LOGO Y NEON AI (Actualizado: Lado a Lado)
st.markdown("""
    <div style="display: flex; align-items: center; justify-content: center; gap: 15px; padding-bottom: 10px;">
        <img src="https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png" height="80">
        <h1 class='neon-title'>AI</h1>
    </div>
    <div style="text-align:center; padding-bottom: 20px;">
        <p style='color:#666; font-size:0.9rem; margin: 0;'>Cotizador Simple</p>
    </div>
""", unsafe_allow_html=True)

# Renderizar mensajes anteriores
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message(msg["role"], avatar=AVATAR_URL):
            clean_text = clean_response(msg["content"])
            st.markdown(clean_text)
    else:
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["content"])

# Input del usuario
if prompt := st.chat_input("Escribe aquí tu consulta..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=AVATAR_URL):
        with st.spinner("Consultando precios..."):
            try:
                if "chat_session" not in st.session_state:
                    st.error("Error: Sesión perdida. Recarga la página.")
                    st.stop()
                
                response = st.session_state.chat_session.send_message(prompt)
                raw_text = response.text
                
                clean_text = clean_response(raw_text)
                
                # Agregar botón WhatsApp simple al final
                if "WhatsApp" not in clean_text:
                    clean_text += f"\n\n[Escribir al WhatsApp]({WHATSAPP_LINK})"
                
                st.markdown(clean_text)
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": clean_text
                })
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
