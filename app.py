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
    initial_sidebar_state="expanded"  # Sidebar abierto por defecto para ver las indicaciones
)

# --- CONSTANTES ---
AVATAR_URL = "https://kiwigeekperu.com/wp-content/uploads/2026/01/gatitow.webp"
WHATSAPP_LINK = "https://api.whatsapp.com/send/?phone=51939081940&text=Hola%2C+me+gustar%C3%ADa+saber+m%C3%A1s+de+sus+productos&type=phone_number&app_absent=0"

# --- CSS MIXTO (Header Neón + Chat Limpio + Sidebar Mejorado) ---
def apply_custom_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
        
        /* Fuente general */
        * { 
            font-family: 'Inter', sans-serif !important; 
        }
        
        /* --- ESTILO NEÓN PARA EL HEADER (Aumentado) --- */
        .neon-title {
            color: #00FF41 !important;
            text-shadow: 0 0 30px rgba(0,255,65,0.6);
            text-align: center;
            font-weight: 900 !important;
            font-size: 6rem !important;
            margin: 0;
            line-height: 1;
        }

        /* --- ESTILO LIMPIO PARA EL CHAT --- */
        .stChatMessage { 
            background: transparent !important; 
            border: none !important;
        }

        .stMarkdown h3 {
            margin-top: 20px;
            font-size: 1.2rem;
            font-weight: bold;
            color: #000 !important; 
        }
        
        .stMarkdown a {
            color: #0066cc !important;
            text-decoration: underline;
        }

        .stMarkdown li {
            background: transparent !important;
            padding: 5px 0 !important;
            margin: 0 !important;
            border: none !important;
            list-style-type: disc !important;
            color: #000 !important;
        }
        
        .stMarkdown p {
            color: #000 !important;
        }

        /* --- ESTILO PARA EL SIDEBAR (Indicaciones) --- */
        [data-testid="stSidebar"] {
            background-color: #f8f9fa; 
        }
        
        /* Caja genérica */
        .info-box {
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        
        /* Título VERDE (Lo que SÍ hago) */
        .info-title-yes {
            color: #28a745; 
            font-weight: bold;
            font-size: 1.1rem;
            margin-bottom: 10px;
            border-bottom: 2px solid #28a745;
            padding-bottom: 5px;
        }

        /* Título ROJO (Lo que NO hago) */
        .info-title-no {
            color: #d9534f;
            font-weight: bold;
            font-size: 1.1rem;
            margin-bottom: 10px;
            border-bottom: 2px solid #d9534f;
            padding-bottom: 5px;
        }
        
        .info-list {
            padding-left: 20px; 
            color: #333; 
            font-size: 0.9rem;
            margin-bottom: 0;
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
            
        sys_prompt = """ROL: Eres 'Kiwigeek AI', vendedor de hardware especializado en armar PCs.
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
        temperature=0.1, 
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

# --- UI (SIDEBAR MODIFICADO) ---
with st.sidebar:
    st.image('https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png', use_container_width=True)
    
    # Panel ✅ Lo que SÍ hago
    st.markdown("""
    <div class="info-box">
        <div class="info-title-yes">✅ Lo que SÍ hago</div>
        <ul class="info-list">
            <li><b>Cotizo PCs a medida</b> (Gaming/Trabajo).</li>
            <li><b>Verifico compatibilidad</b> de piezas.</li>
            <li><b>Doy precios y links</b> directos.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Panel 🚫 Lo que NO hago
    st.markdown("""
    <div class="info-box">
        <div class="info-title-no">🚫 Lo que NO hago</div>
        <ul class="info-list">
            <li><b>No doy soporte técnico</b> ni reparaciones.</li>
            <li><b>No acepto trade-ins</b> (partes en pago).</li>
            <li><b>No doy crédito</b> directo.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    
    if st.button("🗑️ Reiniciar Chat", use_container_width=True):
        st.session_state.messages = []
        if "chat_session" in st.session_state:
            del st.session_state["chat_session"]
        st.rerun()

# HEADER AUMENTADO (Logo y Texto Grandes)
st.markdown("""
    <div style="display: flex; align-items: center; justify-content: center; gap: 20px; padding-bottom: 20px; padding-top: 10px;">
        <img src="https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png" height="120">
        <h1 class='neon-title'>AI</h1>
    </div>
    <div style="text-align:center; padding-bottom: 20px;">
        <p style='color:#666; font-size:1rem; margin: 0;'>Cotizador Simple & Directo</p>
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
