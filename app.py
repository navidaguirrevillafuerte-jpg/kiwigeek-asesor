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
WHATSAPP_LINK = "https://api.whatsapp.com/send/?phone=51939081940&text=Hola%2C+vengo+del+Chat+AI+y+quiero+reclamar+mi+descuento+especial+por+PC+Completa&type=phone_number&app_absent=0"

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
        
        /* Título DORADO (Promoción) */
        .info-title-promo {
            color: #d4ac0d; 
            font-weight: bold;
            font-size: 1.1rem;
            margin-bottom: 10px;
            border-bottom: 2px solid #ffd700;
            padding-bottom: 5px;
        }
        
        .info-list {
            padding-left: 20px; 
            color: #333; 
            font-size: 0.9rem;
            margin-bottom: 0;
        }
        
        /* Botón de WhatsApp en Sidebar */
        .promo-btn {
            display: block;
            width: 100%;
            text-align: center;
            background-color: #25D366;
            color: white !important;
            padding: 8px 0;
            border-radius: 5px;
            text-decoration: none !important;
            font-weight: bold;
            margin-top: 10px;
            transition: opacity 0.3s;
        }
        .promo-btn:hover {
            opacity: 0.9;
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
OBJETIVO: Dar SIEMPRE 3 opciones de cotización directas, simples y ajustadas al presupuesto.

REGLAS DE PRESUPUESTO (CRÍTICO):
1. Las 3 opciones (A, B y C) deben estar CERCANAS al presupuesto del usuario.
2. NINGUNA opción debe exceder el presupuesto original en más de un 15%.
   - Ejemplo: Si el usuario dice S/ 2000, el máximo absoluto es S/ 2300.
3. Si el presupuesto es muy bajo para 3 opciones, ofrece la mejor opción posible ajustada a ese monto.

REGLAS DE FORMATO (ESTRICTAS):
1. SIEMPRE genera 3 OPCIONES (si el presupuesto lo permite) variando rendimiento.
2. NO uses negritas (**) para todo, solo para títulos de sección.
3. NO uses cursivas ni bloques de código.
4. Formato de línea de producto: "Nombre del Producto - Precio - [Ver Link](url)"
5. Usa listas simples (-).
6. IMPORTANTE: NO expliques las reglas del descuento por PC completa (ya están visibles en la pantalla). Solo da precios y links.

EJEMPLO DE RESPUESTA DESEADA:
Hola, aquí tienes 3 opciones para tu presupuesto:

Opción A - Económica:
- Procesador AMD Ryzen 5 5600G - S/ 450 - [Ver Aquí](url)
- Placa Asus A520M - S/ 280 - [Ver Aquí](url)
- Memoria Ram 8GB - S/ 120 - [Ver Aquí](url)
...
Total: S/ 1,180

Opción B - Balanceada:
- Procesador Intel i5 12400F - S/ 580 - [Ver Aquí](url)
- Placa B660M - S/ 550 - [Ver Aquí](url)
...
Total: S/ 1,250

Opción C - Maximizando tu Presupuesto:
- Procesador Ryzen 7 5700X - S/ 850 - [Ver Aquí](url)
...
Total: S/ 1,320

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

    # Panel 🎁 PROMOCIÓN ESPECIAL (NUEVO)
    st.markdown(f"""
    <div class="info-box" style="border: 1px solid #ffd700; background: #fffdf0;">
        <div class="info-title-promo">🎁 ¡Promoción Especial!</div>
        <p style="font-size: 0.9rem; color: #333; margin-bottom: 10px; line-height: 1.4;">
            Al comprar tu PC completa (<b>Procesador, Video, RAM y Placa</b>) accedes automáticamente a un <b style="color:#d4ac0d;">Descuento Especial</b>.
        </p>
        <a href="{WHATSAPP_LINK}" target="_blank" class="promo-btn">
            📲 Reclamar Descuento
        </a>
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
