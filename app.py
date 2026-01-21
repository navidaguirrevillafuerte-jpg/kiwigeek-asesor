import streamlit as st
import os
import json
import random
from google import genai
from google.genai import types

# --- CONFIGURACIÓN DE LA PÁGINA ---
# Debe ser siempre el primer comando de Streamlit
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
        /* Force reload styles v5.0 - Ultimate Black Border Fix */
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

        /* --- ESTILOS DEL INPUT DE CHAT (REFORZADO V5) --- */
        
        /* Contenedor flotante del input */
        .stChatInputContainer {{
            padding-bottom: 20px !important; /* Ajustado para que no quede tan alto si no es necesario */
            background: transparent !important;
        }}

        /* ESTRATEGIA: Targetear el CONTENEDOR, no solo la caja de texto */
        div[data-testid="stChatInput"] {{
            border-radius: 15px !important;
            background-color: #e8e8e8 !important; /* Gris por defecto */
            border: 2px solid transparent !important; /* Sin borde por defecto */
            color: #333 !important;
            box-shadow: none !important;
        }}

        /* AL HACER CLICK (FOCUS): Usamos focus-within en el padre */
        div[data-testid="stChatInput"]:focus-within {{
            background-color: #ffffff !important; /* Fondo blanco al escribir */
            border: 2px solid #000000 !important; /* BORDE NEGRO PURO */
            box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
        }}

        /* Limpiar estilos internos de Streamlit que causan el borde rojo */
        div[data-testid="stChatInput"] > div, div[data-baseweb="base-input"] {{
            border: none !important;
            background-color: transparent !important;
            box-shadow: none !important;
        }}

        /* El área de texto en sí misma */
        textarea[data-testid="stChatInputTextArea"] {{
            background-color: transparent !important;
            color: #333333 !important;
            caret-color: #000000 !important; /* Cursor negro */
        }}
        
        textarea[data-testid="stChatInputTextArea"]::placeholder {{
            color: #666666 !important;
        }}
        
        /* --- AJUSTE CRÍTICO DE ANCHO Y CENTRADO --- */
        
        /* 1. Ancho del contenedor principal (Mensajes) */
        .block-container {{
            max-width: 680px !important; 
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }}

        /* 2. Ancho de la barra de entrada de chat (Input) */
        .stChatInput {{
            max-width: 680px !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }}

        /* Solo ocultamos el Footer (Made with Streamlit), mostramos el resto */
        footer {{visibility: hidden;}}
        
        /* --- ELIMINACIÓN AGRESIVA DEL BOTÓN SIDEBAR --- */
        [data-testid="stSidebarCollapsedControl"] {{
            display: none !important;
        }}
        section[data-testid="stSidebar"] > div > div:first-child button {{
            display: none !important;
        }}
        .stDeployButton {{display: none !important;}}
        
        /* Mantenemos visible el menú de opciones (tres puntos) */
        [data-testid="stToolbar"] {{visibility: visible !important;}}
        </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# --- HELPER: CREAR ARCHIVO DUMMY SI NO EXISTE ---
# Esto evita que el código falle si no tienes el JSON a mano
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

# Aseguramos que el archivo exista antes de leerlo
ensure_catalog_exists()

# --- LÓGICA DE CLIENTE Y CACHE ---
def get_api_key():
    # Intenta obtener de secrets, luego variables de entorno, o string vacío
    try:
        return st.secrets["GEMINI_API_KEY"]
    except:
        return os.getenv("GEMINI_API_KEY", "")

# Manejo robusto de la API Key
api_key = get_api_key()
if not api_key:
    # Si no hay API key, pedimos una temporalmente en el sidebar para que no crashee
    with st.sidebar:
        st.warning("⚠️ API Key no encontrada")
        api_key = st.text_input("Ingresa tu Gemini API Key:", type="password")
        if not api_key:
            st.info("Por favor configura tu API key en .streamlit/secrets.toml o ingrésala aquí.")
            st.stop()

client = genai.Client(api_key=api_key)
MODEL_ID = 'models/gemini-2.0-flash'

@st.cache_resource
def setup_kiwi_brain():
    """Inicializa el contenido cacheado para ahorrar tokens."""
    # Retorna: (cache_name, fallback_system_instruction)
    try:
        path = 'catalogo_kiwigeek.json'
        # Verificación redundante, pero segura
        if not os.path.exists(path):
            return None, "Error: Archivo de catálogo no encontrado."

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

        try:
            # Intentar crear cache con TTL de 2 horas
            cache = client.caches.create(
                model=MODEL_ID,
                config=types.CreateCachedContentConfig(
                    display_name='kiwigeek_v1',
                    system_instruction=system_instruction,
                    contents=[catalog_data],
                    ttl='7200s',
                )
            )
            # Si tiene éxito, devolvemos el nombre del cache y None como fallback
            return cache.name, None
            
        except Exception as e:
            # Fallback silencioso si falla el caché (ej. API gratuita)
            print(f"Advertencia: No se pudo crear el caché ({e}). Usando modo estándar.")
            # Combinamos la instrucción y los datos para el modo estándar
            fallback_instruction = f"{system_instruction}\n\nCATÁLOGO DE PRODUCTOS:\n{catalog_data}"
            return None, fallback_instruction

    except Exception as e:
        return None, f"Error crítico: {str(e)}"

# --- INICIALIZACIÓN DE SESIÓN (CORREGIDO) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Esta lógica ahora se ejecutará correctamente al resetear la sesión
if "chat_session" not in st.session_state:
    # Obtenemos cache O instrucción fallback
    cache_name, fallback_instruction = setup_kiwi_brain()
    
    # Verificamos si hubo un error crítico (si ambos son strings de error, aunque nuestra lógica devuelve (None, str))
    # Si fallback_instruction empieza con "Error", es un error crítico de archivo
    if fallback_instruction and fallback_instruction.startswith("Error:"):
         st.error(f"⚠️ {fallback_instruction}")
         st.stop()

    try:
        if cache_name:
            # Opción A: Usar Caché Optimizado
            st.session_state.chat_session = client.chats.create(
                model=MODEL_ID,
                config=types.GenerateContentConfig(
                    cached_content=cache_name,
                    temperature=0.2,
                    top_p=0.9
                )
            )
            # Indicador visual discreto de que el caché está activo
            print("Sistema: Caché activo")
        else:
            # Opción B: Modo Estándar (Fallback)
            st.session_state.chat_session = client.chats.create(
                model=MODEL_ID,
                config=types.GenerateContentConfig(
                    system_instruction=fallback_instruction, # Pasamos todo el contexto aquí
                    temperature=0.2,
                    top_p=0.9
                )
            )
            # Indicador visual discreto
            print("Sistema: Modo estándar (sin caché)")
            
    except Exception as e:
        st.error(f"Error al conectar con Gemini: {e}")
        st.stop()

    # Mensaje de bienvenida - Se añade SOLO si la lista de mensajes está vacía
    if not st.session_state.messages:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "¡Hola! Soy el asistente de **Kiwigeek**. 🐱\n\n¿Buscas una PC para gaming, diseño o trabajo pesado? Dime tu presupuesto y diseñaremos la mejor configuración para ti."
        })

# --- INTERFAZ ---
# Sidebar para acciones
with st.sidebar:
    st.image('https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png')
    st.markdown("---")
    
    # --- CORRECCIÓN AQUÍ: BOTÓN DE LIMPIEZA ---
    if st.button("🗑️ Limpiar Conversación", use_container_width=True):
        # 1. Borrar mensajes visuales
        st.session_state.messages = []
        # 2. CRÍTICO: Borrar la sesión del chat para reiniciar la memoria de la IA
        if "chat_session" in st.session_state:
            del st.session_state["chat_session"]
        # 3. Recargar la app para que se ejecute la inicialización de nuevo
        st.rerun()

# Header Principal
st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; gap: 10px; padding-bottom: 10px;">
        <img src="https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png" 
             style="height: 90px; object-fit: contain; filter: drop-shadow(0 0 5px rgba(0, 255, 65, 0.3));">
        <h1 class='neon-title' style='margin: 0; padding: 0; font-size: 3.5rem !important; display: inline-block;'>AI</h1>
    </div>
""", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Ingeniería de hardware de alto nivel</p>", unsafe_allow_html=True)

# Mostrar historial
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message(msg["role"], avatar=AVATAR_URL):
            st.markdown(msg["content"])
    else:
        # Usar el avatar guardado o uno aleatorio si es un mensaje antiguo
        user_avatar = msg.get("avatar", random.choice(USER_AVATARS))
        with st.chat_message(msg["role"], avatar=user_avatar):
            st.markdown(msg["content"])

# Entrada de usuario
if prompt := st.chat_input("Ej: Tengo S/ 4000 para una PC de Streaming..."):
    # Seleccionar avatar aleatorio ÚNICO para este mensaje
    current_user_avatar = random.choice(USER_AVATARS)
    
    # Añadir mensaje de usuario con su avatar específico
    st.session_state.messages.append({
        "role": "user", 
        "content": prompt, 
        "avatar": current_user_avatar
    })
    
    with st.chat_message("user", avatar=current_user_avatar):
        st.markdown(prompt)

    # Respuesta de la IA
    with st.chat_message("assistant", avatar=AVATAR_URL):
        placeholder = st.empty()
        with st.spinner("🔍 Analizando stock y compatibilidad..."):
            try:
                # Asegurarse de que chat_session existe
                if "chat_session" not in st.session_state:
                     st.error("Sesión expirada. Por favor recarga la página.")
                else:
                    response = st.session_state.chat_session.send_message(prompt)
                    full_response = response.text
                    placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Error en la respuesta: {e}")

# Footer
st.markdown("<br><hr><p style='text-align: center; color: #555;'>© 2025 Kiwigeek Perú - Hardware for Professionals</p>", unsafe_allow_html=True)
