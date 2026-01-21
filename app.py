import streamlit as st
import os
import re
from google import genai
from google.genai import types

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Kiwigeek AI - Hardware Engineer",
    page_icon="https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CONSTANTES ---
AVATAR_URL = "https://kiwigeekperu.com/wp-content/uploads/2026/01/gatitow.webp"
WHATSAPP_LINK = "https://api.whatsapp.com/send/?phone=51939081940&text=Hola%2C+me+gustar%C3%ADa+saber+m%C3%A1s+de+sus+productos&type=phone_number&app_absent=0"

# --- CSS SIMPLE Y EFECTIVO ---
def apply_custom_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        * { 
            font-family: 'Inter', sans-serif !important; 
        }
        
        .neon-title {
            color: #00FF41 !important;
            text-shadow: 0 0 20px rgba(0,255,65,0.5);
            text-align: center;
            font-weight: 900 !important;
            font-size: 3.5rem !important;
            margin: 0;
        }
        
        .stChatMessage { 
            background: transparent !important; 
        }
        
        [data-testid="stChatMessageAssistant"] { 
            background: rgba(255,255,255,0.02) !important; 
            border: 1px solid #333; 
            border-radius: 12px;
        }
        
        footer {
            visibility: hidden;
        }
        
        /* Markdown mejorado */
        .stMarkdown h3 {
            color: #00FF41 !important;
            border-bottom: 2px solid #00FF41;
            padding-bottom: 8px;
            margin-top: 20px;
        }
        
        .stMarkdown h4 {
            color: #00FF41 !important;
            font-size: 1.1rem;
        }
        
        .stMarkdown ul {
            list-style: none;
            padding-left: 0;
        }
        
        .stMarkdown li {
            background: #1e1e1e;
            padding: 10px 15px;
            margin: 8px 0;
            border-left: 3px solid #444;
            border-radius: 6px;
        }
        
        .stMarkdown li:hover {
            border-left-color: #00FF41;
            background: #252525;
        }
        
        .stMarkdown a {
            color: #00FF41 !important;
            text-decoration: none;
            font-weight: 600;
        }
        
        .stMarkdown a:hover {
            text-decoration: underline;
        }
        
        .stMarkdown strong {
            color: #00FF41;
        }
        
        .stMarkdown blockquote {
            border-left: 4px solid #00FF41;
            background: rgba(0,255,65,0.1);
            padding: 10px 15px;
            margin: 15px 0;
            border-radius: 6px;
        }
        </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# --- DATOS DUMMY ---
if not os.path.exists('catalogo_kiwigeek.json'):
    with open('catalogo_kiwigeek.json', 'w') as f:
        import json
        json.dump({"products": []}, f)

# --- LIMPIEZA DE RESPUESTA ---
def clean_response(text):
    """Limpia cualquier código HTML que la IA intente generar"""
    # Eliminar bloques de código HTML
    text = re.sub(r'<[^>]+>', '', text)
    # Eliminar etiquetas markdown de código
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
    """Configura el cerebro con instrucciones CLARAS: SOLO TEXTO"""
    try:
        with open('catalogo_kiwigeek.json', 'r', encoding='utf-8') as f: 
            catalog = f.read()
            
        sys_prompt = """ROL: Eres 'Kiwigeek AI', vendedor experto en PCs.

REGLA ABSOLUTA: NUNCA generes código HTML, ni etiquetas <div>, <span>, <table>, ni nada de código.
SOLO escribe texto normal con formato Markdown simple.

--- FORMATO DE RESPUESTA ---

Cuando cotices, usa EXACTAMENTE este formato:

### OPCIÓN A: AHORRO ÉPICO

**Estrategia:** Máximo rendimiento en juegos recortando en lo estético.

- **PROCESADOR:** AMD Ryzen 5 5600 - S/ 422 → [Ver Producto](url)
- **PLACA:** ASRock B450M Steel Legend - S/ 439
- **RAM:** Team DDR4 16GB 3200MHz - S/ 250
- **GPU:** Gigabyte GeForce RTX 3060 - S/ 918
- **SSD:** Team MP33 512GB - S/ 170
- **FUENTE:** Seasonic A12 600W - S/ 412

**TOTAL CONTADO: S/ 4,820.47**

---

### OPCIÓN B: EQUILIBRIO GAMER

**Estrategia:** Componentes de buena calidad para rendimiento sólido y duradero.

- **PROCESADOR:** Intel Core i5-12400F - S/ 570
- **PLACA:** MSI B660M-A DDR4 - S/ 599
  💡 **Tecnología 12va Gen:** Mejor eficiencia y mayor rendimiento por núcleo
- **RAM:** Corsair Vengeance 16GB DDR4 - S/ 350
- **GPU:** ASUS TUF RTX 4060 - S/ 1,399
  💡 **Potencia Gráfica:** Juega en Ultra con Ray Tracing y DLSS 3
- **SSD:** Kingston NV2 1TB - S/ 280
- **FUENTE:** EVGA 650W 80+ Gold - S/ 450

**TOTAL CONTADO: S/ 5,370.85**

---

### OPCIÓN C: MÁXIMA POTENCIA

**Estrategia:** Exprimir cada sol en rendimiento gráfico y componentes clave.

(componentes...)

**TOTAL CONTADO: S/ 6,827.43**

---

⚠️ **ATENCIÓN:** Si decides comprar tu PC COMPLETA con nosotros, comunícate al WhatsApp para aplicarte un **DESCUENTO ADICIONAL EXCLUSIVO**.

[🚀 Solicitar Descuento en WhatsApp](link)

--- REGLAS ---
1. NO uses HTML bajo ninguna circunstancia
2. Solo Markdown: ###, **, -, links con []()
3. Precios siempre con "S/" y comas (ej: S/ 1,399)
4. Links SIEMPRE en formato [Texto](url)
5. Insights (💡) solo en opciones B y C para componentes premium
6. Orden de componentes: CPU → Placa → RAM → GPU → SSD → Fuente → Case (si aplica)
"""
        
        return client.caches.create(
            model=MODEL_ID,
            config=types.CreateCachedContentConfig(
                display_name='kiwigeek_pure_text',
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
        temperature=0.15, 
        top_p=0.85, 
        max_output_tokens=8192
    )
    if cache_name: 
        config.cached_content = cache_name
    
    st.session_state.chat_session = client.chats.create(model=MODEL_ID, config=config)
    
    # Mensaje de bienvenida
    if not st.session_state.messages:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "¡Hola! Soy **Kiwigeek AI** 🥝\n\nDime tu presupuesto y si buscas **Solo Torre** o **PC Completa**."
        })

# --- UI ---
with st.sidebar:
    st.image('https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png')
    if st.button("🗑️ Reiniciar Chat", use_container_width=True):
        st.session_state.messages = []
        if "chat_session" in st.session_state:
            del st.session_state["chat_session"]
        st.rerun()

st.markdown("""
    <div style="text-align:center; padding-bottom: 20px;">
        <img src="https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png" height="80">
        <h1 class='neon-title'>AI</h1>
        <p style='color:#666; font-size:0.9rem;'>Ingeniería de Hardware - Texto Puro</p>
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
if prompt := st.chat_input("Ej: Tengo S/ 3800 para PC Completa..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=AVATAR_URL):
        with st.spinner("🤖 Analizando catálogo..."):
            try:
                if "chat_session" not in st.session_state:
                    st.error("Error: Sesión perdida. Por favor recarga la página.")
                    st.stop()
                
                response = st.session_state.chat_session.send_message(prompt)
                raw_text = response.text
                
                # Limpiar cualquier HTML que se haya colado
                clean_text = clean_response(raw_text)
                
                # Agregar botón WhatsApp si no está
                if "WhatsApp" not in clean_text and "===" in clean_text:
                    clean_text += f"\n\n[🚀 Solicitar Descuento en WhatsApp]({WHATSAPP_LINK})"
                
                # Renderizar
                st.markdown(clean_text)
                
                # Guardar en historial
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": clean_text
                })
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                if "chat_session" in st.session_state:
                    del st.session_state["chat_session"]
