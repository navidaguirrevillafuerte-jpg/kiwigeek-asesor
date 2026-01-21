import streamlit as st
import os
from google import genai
from google.genai import types

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Kiwigeek AI",
    page_icon="🥝",
    layout="centered"
)

# --- TÍTULO Y PRESENTACIÓN ---
st.title("🥝 Kiwigeek AI")
st.markdown("### Tu Ingeniero de Hardware Personal")
st.info("💡 **Tip:** Dime tu presupuesto (ej: *'PC de 4000 soles'*) o pide componentes específicos.")

# --- GESTIÓN DE LA LLAVE DE SEGURIDAD ---
# Intentamos tomar la llave de los "Secretos" de la nube. 
# Si falla (estás en local), usa tu llave directa.
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = "PON_AQUI_TU_LLAVE_SI_PRUEBAS_EN_LOCAL"

client = genai.Client(api_key=API_KEY)
MODELO_USADO = 'models/gemini-2.0-flash'

# --- FUNCIÓN: CARGAR CEREBRO (Solo se ejecuta 1 vez) ---
@st.cache_resource
def iniciar_cerebro_kiwigeek():
    try:
        if not os.path.exists('catalogo_kiwigeek.json'):
            return None

        with open('catalogo_kiwigeek.json', 'r', encoding='utf-8') as f:
            datos = f.read()

        # AQUÍ ESTÁ TU PROMPT MAESTRO V15 (COMPLETO)
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
                ttl='7200s', # 2 horas de vida en caché
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
    else:
        st.error("❌ No se encontró el catálogo. Verifica que 'catalogo_kiwigeek.json' esté subido.")
        st.stop()

# --- MOSTRAR MENSAJES ANTERIORES ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- CAPTURAR NUEVO MENSAJE ---
if prompt := st.chat_input("¿Qué PC estás buscando hoy?"):
    # 1. Guardar y mostrar mensaje usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generar respuesta IA
    with st.chat_message("assistant"):
        with st.spinner("Kiwigeek está calculando la mejor configuración..."):
            try:
                response = st.session_state.chat.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Ocurrió un error: {e}")