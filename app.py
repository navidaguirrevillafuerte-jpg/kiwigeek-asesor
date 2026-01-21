import streamlit as st
import os
import json
import random
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

# --- LISTA DE AVATARES RANDOM PARA USUARIO ---
USER_AVATARS = [
    "🧑‍💻", "👨‍💻", "👩‍💻", "🦸", "🦹", "🧙", "🧚", "🧛", "🧜", "🧝", 
    "🧞", "🧟", "💆", "💇", "🚶", "🏃", "💃", "🕺", "🕴", "👯", 
    "🧖", "🧗", "🤺", "🏇", "⛷", "🏂", "🏌️", "🏄", "🚣", "🏊", 
    "⛹️", "🏋️", "🚴", "🚵", "🤸", "🤼", "🤽", "🤾", "🤹", "🧘", 
    "🛀", "🛌", "🧑", "🧒", "👦", "👧", "🧑‍🦱", "👨‍🦱", "👩‍🦱", "🧑‍🦰",
    "😎", "🤓", "🤠", "🥳", "👽", "🤖", "👮", "🕵️", "💂", "👷"
]

# --- CSS MEJORADO (VERSIÓN FORZADA) ---
def apply_custom_styles():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        * {{ font-family: 'Inter', sans-serif !important; }}
        
        .neon-title {{
            color: {COLORS['kiwi_green']} !important;
            text-shadow: 0 0 10px {COLORS['kiwi_green']}55, 0 0 20px {COLORS['kiwi_green']}33;
            text-align: center;
            font-weight: 800 !important;
            font-size: 2.8rem !important;
            margin-bottom: 0px;
        }}

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

        .stChatInputContainer {{
            padding-bottom: 20px !important;
            background: transparent !important;
        }}

        div[data-testid="stChatInput"] {{
            border-radius: 15px !important;
            background-color: #e8e8e8 !important;
            border: 2px solid transparent !important;
            color: #333 !important;
            box-shadow: none !important;
        }}

        div[data-testid="stChatInput"]:focus-within {{
            background-color: #ffffff !important;
            border: 2px solid #000000 !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
        }}

        div[data-testid="stChatInput"] > div, div[data-baseweb="base-input"] {{
            border: none !important;
            background-color: transparent !important;
            box-shadow: none !important;
        }}

        textarea[data-testid="stChatInputTextArea"] {{
            background-color: transparent !important;
            color: #333333 !important;
            caret-color: #000000 !important;
        }}
        
        textarea[data-testid="stChatInputTextArea"]::placeholder {{
            color: #666666 !important;
        }}
        
        .block-container {{
            max-width: 680px !important; 
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }}

        .stChatInput {{
            max-width: 680px !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }}

        footer {{visibility: hidden;}}
        
        [data-testid="stSidebarCollapsedControl"] {{display: none !important;}}
        section[data-testid="stSidebar"] > div > div:first-child button {{display: none !important;}}
        .stDeployButton {{display: none !important;}}
        
        [data-testid="stToolbar"] {{visibility: visible !important;}}
        </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# --- HELPER: CREAR ARCHIVO DUMMY SI NO EXISTE ---
def ensure_catalog_exists():
    path = 'catalogo_kiwigeek.json'
    if not os.path.exists(path):
        dummy_data = {
            "products": [
                {"category": "GPU", "name": "NVIDIA RTX 4060", "price": 1200, "url": "https://kiwigeekperu.com"},
                {"category": "CPU", "name": "Intel Core i5 13400F", "price": 800, "url": "https://kiwigeekperu.com"},
                {"category": "RAM", "name": "16GB DDR4 3200MHz", "price": 200, "url": "https://kiwigeekperu.com"}
            ]
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(dummy_data, f)

ensure_catalog_exists()

# --- LÓGICA DE CLIENTE Y CACHE ---
def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except:
        return os.getenv("GEMINI_API_KEY", "")

api_key = get_api_key()
if not api_key:
    with st.sidebar:
        st.warning("⚠️ API Key no encontrada")
        api_key = st.text_input("Ingresa tu Gemini API Key:", type="password")
        if not api_key:
            st.info("Por favor configura tu API key.")
            st.stop()

client = genai.Client(api_key=api_key)
MODEL_ID = 'models/gemini-2.0-flash'

@st.cache_resource
def setup_kiwi_brain():
    """Inicializa el contenido con FALLBACK INTELIGENTE (Prioriza Caché, pero no muere sin él)"""
    try:
        path = 'catalogo_kiwigeek.json'
        if not os.path.exists(path):
            return None, "Error: Archivo de catálogo no encontrado."

        with open(path, 'r', encoding='utf-8') as f:
            catalog_data = f.read()

        system_instruction = (
            "ROL: Eres 'Kiwigeek AI', Ingeniero y Vendedor Experto. Tu misión es EDUCAR y VENDER.\n"
            "CONTEXTO: Tienes un inventario con LINKS. Úsalos siempre.\n\n"
            "--- PASO 0: FILTRO DE ALCANCE ---\n"
            "1. Si el cliente no especifica 'Solo Torre' o 'PC Completa', PREGUNTA PRIMERO.\n"
            "2. Si ya especificó, avanza.\n\n"
            "--- PASO 1: LÓGICA DE COMPONENTES ---\n"
            "1. CASE: Manténlo económico (incluso en opciones caras) para priorizar rendimiento.\n"
            "2. FUENTE: Si subes GPU, sube la Fuente (Watts/Certificación) obligatoriamente.\n\n"
            "--- PASO 2: ALGORITMOS DE COTIZACIÓN ---\n"
            "1. OPCIÓN A (AHORRO): [P - 10%]. Recorta Case, Placa y lujos.\n"
            "2. OPCIÓN B (IDEAL): [P Exacto]. Equilibrio.\n"
            "3. OPCIÓN C (POTENCIA PURA): [P + 15%]. Invierte en GPU -> Fuente -> RAM -> CPU.\n\n"
            "--- PASO 3: ARGUMENTACIÓN DE VENTAS ---\n"
            "En la OPCIÓN C (y B si aplica), usa el icono '💡' para explicar la mejora:\n"
            "- GPU: '💡 Potencia Gráfica: Juega en Ultra con más FPS.'\n"
            "- DDR5: '💡 Tecnología Next-Gen: Velocidad superior a prueba de futuro.'\n"
            "- 32GB RAM: '💡 Multitarea: Olvídate de cerrar pestañas.'\n"
            "- FUENTE: '💡 Seguridad: Protege tu inversión ante picos.'\n\n"
            "--- FORMATO VISUAL (LINKS LIMPIOS) ---\n"
            "Usa este formato EXACTO. NO repitas la URL en el texto del link:\n"
            "\n"
            "=== OPCIÓN [A/B/C] - [NOMBRE] ===\n"
            "> ESTRATEGIA: [Resumen de 1 línea]\n"
            "* [CATEGORÍA]: [Nombre Producto] ... S/ [Precio] -> [Ver Producto](URL_DEL_JSON)\n"
            "  (Añade aquí la línea 💡 si corresponde)\n"
            "... (Lista resto de componentes) ...\n"
            "----------------------------------\n"
            "TOTAL: S/ [SUMA EXACTA]\n"
            "\n"
            "--- CIERRE DE VENTA ---\n"
            "Finaliza con:\n"
            "'⚠ **ATENCIÓN:** Si decides comprar tu **PC COMPLETA** con nosotros, comunícate al WhatsApp para aplicarte un **DESCUENTO ADICIONAL EXCLUSIVO**.'"
        )

        try:
            # Intentamos crear el caché
            cache = client.caches.create(
                model=MODEL_ID,
                config=types.CreateCachedContentConfig(
                    display_name='kiwigeek_v15_linkfix',
                    system_instruction=system_instruction,
                    contents=[catalog_data],
                    ttl='7200s',
                )
            )
            return cache.name, None # Éxito: (nombre_cache, sin_error)
            
        except Exception as e:
            # FALLBACK: Si falla, usamos el modo estándar
            fallback_instruction = f"{system_instruction}\n\nCATÁLOGO DE PRODUCTOS:\n{catalog_data}"
            return None, fallback_instruction 

    except Exception as e:
        return None, f"Error crítico de archivo: {str(e)}"

# --- INICIALIZACIÓN DE SESIÓN ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Variable de estado para controlar el indicador de caché
if "is_cached_active" not in st.session_state:
    st.session_state.is_cached_active = False

if "chat_session" not in st.session_state:
    cache_name, fallback_instruction = setup_kiwi_brain()
    
    # Si hay un error crítico (de archivo), detenemos.
    if fallback_instruction and fallback_instruction.startswith("Error crítico"):
         st.error(f"⛔ {fallback_instruction}")
         st.stop()

    try:
        if cache_name:
            # MODO 1: CACHÉ (Barato / Optimizado)
            st.session_state.is_cached_active = True
            st.session_state.chat_session = client.chats.create(
                model=MODEL_ID,
                config=types.GenerateContentConfig(
                    cached_content=cache_name,
                    temperature=0.15, 
                    top_p=0.85,       
                    max_output_tokens=8192 
                )
            )
        else:
            # MODO 2: ESTÁNDAR (Gratis pero consume límites, o Pago por uso alto)
            st.session_state.is_cached_active = False
            st.session_state.chat_session = client.chats.create(
                model=MODEL_ID,
                config=types.GenerateContentConfig(
                    system_instruction=fallback_instruction,
                    temperature=0.15,
                    top_p=0.85,
                    max_output_tokens=8192
                )
            )
            
    except Exception as e:
        st.error(f"Error al conectar con Gemini: {e}")
        st.stop()

    if not st.session_state.messages:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "¡Hola! Soy el asistente de **Kiwigeek**. 🐱\n\n¿Buscas una PC para gaming, diseño o trabajo pesado? Dime tu presupuesto y diseñaremos la mejor configuración para ti."
        })

# --- INTERFAZ ---
with st.sidebar:
    st.image('https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png')
    
    # --- INDICADOR DE ESTADO INTELIGENTE ---
    if st.session_state.is_cached_active:
        st.success("⚡ **Caché Activo**\n\nSistema optimizado para bajo costo.")
    else:
        st.warning("⚠️ **Modo Estándar**\n\nEl caché falló (o expiró). Funcionando en modo compatibilidad.")

    st.markdown("---")
    
    if st.button("🗑️ Limpiar Conversación", use_container_width=True):
        st.session_state.messages = []
        if "chat_session" in st.session_state:
            del st.session_state["chat_session"]
        st.rerun()

st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; gap: 10px; padding-bottom: 10px;">
        <img src="https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png" 
             style="height: 90px; object-fit: contain; filter: drop-shadow(0 0 5px rgba(0, 255, 65, 0.3));">
        <h1 class='neon-title' style='margin: 0; padding: 0; font-size: 3.5rem !important; display: inline-block;'>AI</h1>
    </div>
""", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Ingeniería de hardware de alto nivel</p>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message(msg["role"], avatar=AVATAR_URL):
            st.markdown(msg["content"])
    else:
        user_avatar = msg.get("avatar", random.choice(USER_AVATARS))
        with st.chat_message(msg["role"], avatar=user_avatar):
            st.markdown(msg["content"])

if prompt := st.chat_input("Ej: Tengo S/ 4000 para una PC de Streaming..."):
    current_user_avatar = random.choice(USER_AVATARS)
    
    st.session_state.messages.append({
        "role": "user", 
        "content": prompt, 
        "avatar": current_user_avatar
    })
    
    with st.chat_message("user", avatar=current_user_avatar):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=AVATAR_URL):
        placeholder = st.empty()
        with st.spinner("🔍 Analizando stock y compatibilidad..."):
            
            # --- SISTEMA DE AUTO-RECUPERACIÓN (AUTO-HEALING) ---
            try:
                # Verificamos si existe la sesión, si no, lanzamos error para activar el recovery
                if "chat_session" not in st.session_state:
                    raise Exception("Sesión perdida por inactividad")
                
                # INTENTO 1: Envío normal
                response = st.session_state.chat_session.send_message(prompt)
                full_response = response.text

            except Exception as e:
                # Si falla (Socket cerrado, Caché expirado, Timeout), iniciamos recuperación
                print(f"⚠️ Conexión perdida ({e}). Iniciando protocolo de reconexión...")
                
                try:
                    # 1. Recuperamos configuración fresca
                    cache_name, fallback_instruction = setup_kiwi_brain()
                    
                    # 2. Reconstruimos el objeto de Chat
                    new_chat = None
                    if cache_name:
                        new_chat = client.chats.create(
                            model=MODEL_ID,
                            config=types.GenerateContentConfig(
                                cached_content=cache_name,
                                temperature=0.15, top_p=0.85, max_output_tokens=8192
                            )
                        )
                    else:
                        new_chat = client.chats.create(
                            model=MODEL_ID,
                            config=types.GenerateContentConfig(
                                system_instruction=fallback_instruction,
                                temperature=0.15, top_p=0.85, max_output_tokens=8192
                            )
                        )

                    # 3. RESTAURACIÓN DE MEMORIA (CRÍTICO)
                    # Convertimos el historial visual de Streamlit al formato de Gemini
                    history_for_gemini = []
                    for msg in st.session_state.messages[:-1]: # Excluimos el último (el prompt actual)
                        if msg["role"] == "user":
                            history_for_gemini.append(types.Content(role="user", parts=[types.Part(text=msg["content"])]))
                        elif msg["role"] == "assistant":
                            history_for_gemini.append(types.Content(role="model", parts=[types.Part(text=msg["content"])]))
                    
                    # Inyectamos la memoria en el nuevo chat
                    new_chat.history = history_for_gemini
                    
                    # Guardamos el nuevo chat restaurado en la sesión
                    st.session_state.chat_session = new_chat

                    # 4. INTENTO 2: Reenviamos el mensaje
                    response = st.session_state.chat_session.send_message(prompt)
                    full_response = response.text
                    
                except Exception as e2:
                    # Si falla el intento de recuperación, ahí sí mostramos error
                    st.error(f"Error de conexión persistente. Por favor actualiza la página. ({e2})")
                    st.stop()
            
            # Mostrar respuesta exitosa
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

st.markdown("<br><hr><p style='text-align: center; color: #555;'>© 2025 Kiwigeek Perú - Hardware for Professionals</p>", unsafe_allow_html=True)
