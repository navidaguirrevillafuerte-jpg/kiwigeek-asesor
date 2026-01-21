import streamlit as st
import os
from google import genai
from google.genai import types

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Kiwigeek AI",
    page_icon="🥝",
    layout="wide"
)

# --- CSS PERSONALIZADO CON COLORES DE MARCA ---
st.markdown("""
    <style>
    /* Colores de marca Kiwigeek */
    :root {
        --kiwi-green: #00FF41;
        --kiwi-blue: #0066FF;
        --kiwi-black: #1a1a1a;
        --kiwi-gray: #4a4a4a;
        --kiwi-light-gray: #2d2d2d;
    }
    
    /* Tipografía global - Similar a tu web */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    
    /* Fondo principal */
    .stApp {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    }
    
    /* Contenedor principal más ancho */
    .main .block-container {
        max-width: 900px;
        padding-top: 1rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }
    
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1.5rem;
            padding-right: 1.5rem;
        }
    }
    
    /* Título principal con efecto neón */
    h1 {
        color: #00FF41 !important;
        text-shadow: 0 0 10px #00FF41, 0 0 20px #00FF41, 0 0 30px #00FF41;
        font-weight: 700 !important;
        text-align: center;
        padding: 10px 0;
        animation: pulse 2s ease-in-out infinite;
        font-size: 2.5em !important;
        letter-spacing: -0.5px;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    /* Subtítulo */
    h3 {
        color: #0066FF !important;
        text-align: center;
        font-weight: 600 !important;
        letter-spacing: -0.3px;
    }
    
    /* Texto en cajas info */
    .stInfo {
        background: linear-gradient(135deg, #0066FF22 0%, #00FF4122 100%) !important;
        border-left: 4px solid #00FF41 !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(0, 255, 65, 0.2);
        font-weight: 500 !important;
    }
    
    .stInfo p {
        font-size: 0.95em !important;
        line-height: 1.6 !important;
    }
    
    /* Mensajes del chat */
    .stChatMessage {
        background: #2d2d2d !important;
        border-radius: 12px !important;
        border: 1px solid #4a4a4a !important;
        margin: 12px 0 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        font-size: 0.95em !important;
    }
    
    /* Avatar personalizado para el asistente */
    .stChatMessage[data-testid="assistant-message"] img {
        content: url('https://kiwigeekperu.com/wp-content/uploads/2026/01/gatitow.webp') !important;
        border-radius: 8px !important;
    }
    
    /* Mensajes del usuario */
    .stChatMessage[data-testid="user-message"] {
        background: linear-gradient(135deg, #0066FF28 0%, #0066FF18 100%) !important;
        border-left: 3px solid #0066FF !important;
    }
    
    /* Mensajes del asistente */
    .stChatMessage[data-testid="assistant-message"] {
        background: linear-gradient(135deg, #00FF4118 0%, #00FF4108 100%) !important;
        border-left: 3px solid #00FF41 !important;
    }
    
    /* Input del chat */
    .stChatInput {
        background: #2d2d2d !important;
        border: 2px solid #00FF4144 !important;
        border-radius: 20px !important;
        box-shadow: 0 0 12px rgba(0, 255, 65, 0.25);
    }
    
    .stChatInput input {
        color: #e0e0e0 !important;
        font-weight: 500 !important;
        font-size: 0.95em !important;
    }
    
    .stChatInput input::placeholder {
        color: #6a6a6a !important;
        font-weight: 400 !important;
    }
    
    /* Botones */
    .stButton > button {
        background: linear-gradient(135deg, #0066FF 0%, #00FF41 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 10px 30px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 15px rgba(0, 255, 65, 0.4);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 255, 65, 0.6);
    }
    
    /* Spinner personalizado */
    .stSpinner > div {
        border-top-color: #00FF41 !important;
        border-right-color: #0066FF !important;
    }
    
    /* Enlaces */
    a {
        color: #0066FF !important;
        text-decoration: none !important;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    a:hover {
        color: #00FF41 !important;
        text-shadow: 0 0 10px #00FF41;
    }
    
    /* Texto general */
    p, li, span {
        color: #e0e0e0 !important;
        line-height: 1.6 !important;
    }
    
    /* Texto del chat más legible */
    .stChatMessage p {
        font-size: 0.95em !important;
        line-height: 1.65 !important;
        font-weight: 400 !important;
    }
    
    /* Scrollbar personalizado */
    ::-webkit-scrollbar {
        width: 10px;
        background: #1a1a1a;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #00FF41 0%, #0066FF 100%);
        border-radius: 10px;
    }
    
    /* Error messages */
    .stError {
        background: #ff000022 !important;
        border-left: 4px solid #ff0000 !important;
        color: #ff6b6b !important;
    }
    
    /* Markdown en mensajes */
    .stMarkdown {
        color: #e0e0e0 !important;
    }
    
    /* Headers en respuestas */
    h2, h4 {
        color: #00FF41 !important;
        font-weight: 700 !important;
    }
    
    /* Code blocks */
    code {
        background: #1a1a1a !important;
        color: #00FF41 !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        border: 1px solid #00FF4133 !important;
    }
    
    /* Divider */
    hr {
        border-color: #00FF41 !important;
        opacity: 0.3;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER CON LOGO ---
st.markdown("<div style='text-align: center; padding: 15px 0 20px 0;'>", unsafe_allow_html=True)
st.markdown("""
    <img src='https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png' 
         alt='Kiwigeek Logo'
         style='max-width: 340px; width: 100%; filter: drop-shadow(0 0 30px rgba(0, 255, 65, 0.4));'>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- TÍTULO Y PRESENTACIÓN ---
st.markdown("""
    <h1 style='margin-top: 0; padding-top: 0;'>
        <img src='https://kiwigeekperu.com/wp-content/uploads/2026/01/gatitow.webp' 
             style='width: 55px; vertical-align: middle; margin-right: 12px;'>
        Kiwigeek AI
    </h1>
""", unsafe_allow_html=True)

st.markdown("<div style='text-align: center; color: #6a6a6a; font-size: 1em; margin-bottom: 25px; font-weight: 500;'>Tu Ingeniero de Hardware Personal</div>", unsafe_allow_html=True)

# --- GESTIÓN DE LA LLAVE DE SEGURIDAD ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = "PON_AQUI_TU_LLAVE_SI_PRUEBAS_EN_LOCAL"

client = genai.Client(api_key=API_KEY)
MODELO_USADO = 'models/gemini-2.0-flash'

# --- FUNCIÓN: CARGAR CEREBRO ---
@st.cache_resource
def iniciar_cerebro_kiwigeek():
    try:
        if not os.path.exists('catalogo_kiwigeek.json'):
            return None

        with open('catalogo_kiwigeek.json', 'r', encoding='utf-8') as f:
            datos = f.read()

        system_prompt = (
            "ROL: Eres 'Kiwigeek AI', Ingeniero y Vendedor Experto. Tu misión es EDUCAR y VENDER.\n"
            "CONTEXTO: Tienes un inventario con LINKS. Úsalos siempre.\n"
            "--- PASO 0: FILTRO DE ALCANCE ---\n"
            "1. Si el cliente no especifica 'Solo Torre' o 'PC Completa', PREGUNTA PRIMERO.\n"
            "2. Si ya especificó, avanza.\n"
            "--- PASO 1: LÓGICA DE COMPONENTES ---\n"
            "1. CASE: Manténlo económico para priorizar rendimiento.\n"
            "2. FUENTE: Si subes GPU, sube la Fuente obligatoriamente.\n"
            "--- PASO 2: ALGORITMOS DE COTIZACIÓN ---\n"
            "1. OPCIÓN A (AHORRO): [P - 10%]. Recorta Case y lujos.\n"
            "2. OPCIÓN B (IDEAL): [P Exacto]. Equilibrio.\n"
            "3. OPCIÓN C (POTENCIA PURA): [P + 15%]. Invierte en GPU -> Fuente -> RAM -> CPU.\n"
            "--- PASO 3: ARGUMENTACIÓN DE VENTAS ---\n"
            "En la OPCIÓN C, usa '💡' para explicar la mejora (FPS, Seguridad, Futuro).\n"
            "--- FORMATO VISUAL (LINKS LIMPIOS) ---\n"
            "Usa este formato EXACTO:\n"
            "=== OPCIÓN [A/B/C] - [NOMBRE] ===\n"
            "> ESTRATEGIA: [Resumen de 1 línea]\n"
            "* [CATEGORÍA]: [Nombre Producto] ... S/ [Precio] -> [Ver Producto](URL_DEL_JSON)\n"
            "  (Añade aquí la línea 💡 si corresponde)\n"
            "... (Lista resto de componentes) ...\n"
            "----------------------------------\n"
            "TOTAL: S/ [SUMA EXACTA]\n\n"
            "--- CIERRE DE VENTA ---\n"
            "Finaliza con:\n"
            "'⚠ **ATENCIÓN:** Si decides comprar tu **PC COMPLETA** con nosotros, comunícate al WhatsApp para aplicarte un **DESCUENTO ADICIONAL EXCLUSIVO**.'"
        )

        cache = client.caches.create(
            model=MODELO_USADO,
            config=types.CreateCachedContentConfig(
                display_name='kiwigeek_web_v15',
                system_instruction=system_prompt,
                contents=[datos],
                ttl='7200s',
            )
        )
        return cache.name
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# --- INICIO DEL CHAT ---
if "chat" not in st.session_state:
    id_cache = iniciar_cerebro_kiwigeek()
    if id_cache:
        st.session_state.chat = client.chats.create(
            model=MODELO_USADO,
            config=types.GenerateContentConfig(
                cached_content=id_cache,
                temperature=0.15,
                top_p=0.85,
                max_output_tokens=8192
            )
        )
        st.session_state.messages = []
        # Mensaje de bienvenida inicial
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "¡Hola, entusiasta Kiwigeek! 🐱✨\n\n**¡Hagamos realidad tu PC!** 💻 Cuéntame tu presupuesto o qué tipo de máquina necesitas, y armaremos la configuración perfecta para ti.\n\n*Ejemplo: 'Tengo 5000 soles para una PC gamer'*"
        })
    else:
        st.error("❌ No se encontró el catálogo. Verifica que 'catalogo_kiwigeek.json' esté subido.")
        st.stop()

# --- SEPARADOR VISUAL ---
st.markdown("""
    <div style='margin: 25px 0 20px 0;'>
        <div style='height: 1px; background: linear-gradient(90deg, transparent, #00FF4144, transparent);'></div>
    </div>
""", unsafe_allow_html=True)

# --- MOSTRAR MENSAJES ANTERIORES ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- CAPTURAR NUEVO MENSAJE ---
if prompt := st.chat_input("¿Qué PC estás buscando hoy? 💻"):
    # 1. Guardar y mostrar mensaje usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generar respuesta IA
    with st.chat_message("assistant"):
        with st.spinner("🥝 Kiwigeek está calculando la mejor configuración..."):
            try:
                response = st.session_state.chat.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Ocurrió un error: {e}")

# --- FOOTER ---
st.markdown("""
    <div style='margin: 50px 0 0 0;'>
        <div style='height: 1px; background: linear-gradient(90deg, transparent, #00FF4144, transparent);'></div>
    </div>
""", unsafe_allow_html=True)

st.markdown(
    "<p style='text-align: center; color: #4a4a4a; font-size: 0.95em; margin-top: 20px;'>"
    "<img src='https://kiwigeekperu.com/wp-content/uploads/2026/01/gatitow.webp' style='width: 26px; vertical-align: middle; margin-right: 8px;'>"
    "<strong style='color: #00FF41;'>Kiwigeek</strong> - Equipamos tu poder"
    "</p>",
    unsafe_allow_html=True
)
