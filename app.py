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

# --- CSS TEMA CLARO ---
def apply_custom_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        * { 
            font-family: 'Inter', sans-serif !important; 
        }
        
        /* Fondo blanco global */
        .stApp {
            background-color: #ffffff !important;
        }
        
        .neon-title {
            color: #00b833 !important;
            text-align: center;
            font-weight: 900 !important;
            font-size: 3.5rem !important;
            margin: 0;
        }
        
        /* Mensajes del chat */
        .stChatMessage { 
            background: transparent !important; 
        }
        
        [data-testid="stChatMessageAssistant"] { 
            background: #f8f9fa !important; 
            border: 1px solid #dee2e6;
            border-radius: 12px;
        }
        
        [data-testid="stChatMessageUser"] {
            background: #e7f5ff !important;
            border: 1px solid #74c0fc;
            border-radius: 12px;
        }
        
        footer {
            visibility: hidden;
        }
        
        /* Tarjetas de opciones */
        .option-card {
            background: #ffffff;
            border: 2px solid #00b833;
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .option-header {
            background: #00b833;
            color: #ffffff;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 800;
            font-size: 1.3rem;
            margin-bottom: 15px;
            text-align: center;
        }
        
        .strategy-box {
            background: #e8f5e9;
            border-left: 4px solid #00b833;
            padding: 12px 16px;
            margin-bottom: 20px;
            border-radius: 6px;
            color: #1b5e20;
            font-weight: 600;
        }
        
        .component-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            margin: 8px 0;
            background: #f8f9fa;
            border-left: 3px solid #dee2e6;
            border-radius: 6px;
            transition: all 0.2s;
        }
        
        .component-row:hover {
            border-left-color: #00b833;
            background: #e8f5e9;
            transform: translateX(3px);
        }
        
        .component-info {
            flex: 1;
            color: #212529;
        }
        
        .component-category {
            color: #00b833;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }
        
        .component-name {
            color: #212529;
            font-size: 0.95rem;
            font-weight: 500;
            line-height: 1.4;
        }
        
        .component-price {
            color: #00b833;
            font-size: 1rem;
            font-weight: 700;
            margin: 0 15px;
            white-space: nowrap;
        }
        
        .component-link {
            background: #00b833;
            color: white !important;
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none !important;
            font-weight: 600;
            font-size: 0.85rem;
            white-space: nowrap;
            transition: all 0.2s;
        }
        
        .component-link:hover {
            background: #009929;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0,184,51,0.3);
        }
        
        .insight-box {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px 14px;
            margin: 8px 0 8px 20px;
            border-radius: 6px;
            font-size: 0.9rem;
            color: #856404;
        }
        
        .total-box {
            background: #212529;
            color: white;
            padding: 16px 20px;
            border-radius: 8px;
            margin-top: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .total-label {
            font-size: 1rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .total-amount {
            font-size: 1.8rem;
            font-weight: 900;
            color: #00b833;
        }
        
        .btn-whatsapp {
            display: block;
            width: 100%;
            background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
            color: white !important;
            text-align: center;
            padding: 16px;
            border-radius: 10px;
            font-weight: 800;
            font-size: 1.1rem;
            text-decoration: none !important;
            margin-top: 24px;
            transition: all 0.3s;
            box-shadow: 0 4px 12px rgba(37,211,102,0.3);
        }
        
        .btn-whatsapp:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(37,211,102,0.4);
        }
        
        .warning-box {
            background: #fff3cd;
            border: 2px solid #ffc107;
            color: #856404;
            padding: 16px;
            border-radius: 10px;
            font-size: 0.95rem;
            margin: 20px 0;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# --- DATOS DUMMY ---
if not os.path.exists('catalogo_kiwigeek.json'):
    with open('catalogo_kiwigeek.json', 'w') as f:
        import json
        json.dump({"products": []}, f)

# --- PARSER DE RESPUESTA ---
def parse_and_render(text):
    """Convierte el texto de la IA en HTML bonito"""
    
    # Si no es una cotización, mostrar como texto simple
    if "OPCIÓN A" not in text:
        return f"<div style='color:#212529; line-height:1.6;'>{text}</div>"
    
    html_parts = []
    lines = text.split('\n')
    i = 0
    
    current_option = None
    current_components = []
    current_strategy = ""
    current_total = ""
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Detectar inicio de opción
        if "OPCIÓN" in line and ("A:" in line or "B:" in line or "C:" in line):
            # Renderizar opción anterior si existe
            if current_option:
                html_parts.append(render_option_html(
                    current_option, 
                    current_strategy,
                    current_components, 
                    current_total
                ))
            
            # Nueva opción
            current_option = line
            current_components = []
            current_strategy = ""
            current_total = ""
        
        # Estrategia
        elif "Estrategia:" in line or "ESTRATEGIA:" in line:
            current_strategy = line.split(":", 1)[1].strip()
        
        # Componente (lineas con "**CATEGORÍA:**")
        elif line.startswith("- **") or line.startswith("* **"):
            comp_data = parse_component_line(line)
            if comp_data:
                current_components.append(comp_data)
        
        # Insight (💡)
        elif "💡" in line and current_components:
            # Agregar insight al último componente
            insight_text = line.replace("💡", "").strip()
            current_components[-1]['insight'] = insight_text
        
        # Total
        elif "TOTAL" in line.upper() and "S/" in line:
            match = re.search(r'S/\s*([\d,\.]+)', line)
            if match:
                current_total = match.group(1)
        
        i += 1
    
    # Renderizar última opción
    if current_option:
        html_parts.append(render_option_html(
            current_option, 
            current_strategy,
            current_components, 
            current_total
        ))
    
    # Agregar warning y botón WhatsApp
    html_parts.append(f"""
        <div class="warning-box">
            ⚠️ <strong>ATENCIÓN:</strong> Si decides comprar tu PC COMPLETA con nosotros, 
            comunícate al WhatsApp para aplicarte un <strong>DESCUENTO ADICIONAL EXCLUSIVO</strong>.
        </div>
        <a href="{WHATSAPP_LINK}" target="_blank" class="btn-whatsapp">
            🚀 SOLICITAR DESCUENTO EN WHATSAPP
        </a>
    """)
    
    return ''.join(html_parts)

def parse_component_line(line):
    """Extrae información de una línea de componente"""
    # Formato: - **CATEGORÍA:** Nombre - S/ Precio → [Ver Producto](URL)
    
    # Extraer categoría
    cat_match = re.search(r'\*\*([^*]+)\*\*:', line)
    if not cat_match:
        return None
    
    category = cat_match.group(1).strip()
    
    # Extraer precio
    price_match = re.search(r'S/\s*([\d,\.]+)', line)
    price = price_match.group(1) if price_match else "0"
    
    # Extraer URL
    url_match = re.search(r'\[Ver Producto\]\(([^\)]+)\)', line)
    url = url_match.group(1) if url_match else "#"
    
    # Nombre del producto (entre categoría y precio/link)
    name_part = line.split(':', 1)[1] if ':' in line else ""
    # Limpiar el nombre
    name_part = re.sub(r'\[Ver Producto\].*', '', name_part)
    name_part = re.sub(r'→.*', '', name_part)
    name_part = re.sub(r'-\s*S/.*', '', name_part)
    name = name_part.strip()
    
    return {
        'category': category,
        'name': name,
        'price': price,
        'url': url,
        'insight': None
    }

def render_option_html(title, strategy, components, total):
    """Renderiza una opción completa en HTML"""
    
    components_html = ""
    for comp in components:
        components_html += f"""
        <div class="component-row">
            <div class="component-info">
                <div class="component-category">{comp['category']}</div>
                <div class="component-name">{comp['name']}</div>
            </div>
            <div class="component-price">S/ {comp['price']}</div>
            <a href="{comp['url']}" target="_blank" class="component-link">Ver Producto</a>
        </div>
        """
        
        if comp.get('insight'):
            components_html += f"""
            <div class="insight-box">
                💡 {comp['insight']}
            </div>
            """
    
    return f"""
    <div class="option-card">
        <div class="option-header">{title}</div>
        <div class="strategy-box">📋 Estrategia: {strategy}</div>
        {components_html}
        <div class="total-box">
            <span class="total-label">Total Contado</span>
            <span class="total-amount">S/ {total}</span>
        </div>
    </div>
    """

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
    """Configura el cerebro con reglas estrictas"""
    try:
        with open('catalogo_kiwigeek.json', 'r', encoding='utf-8') as f: 
            catalog = f.read()
            
        sys_prompt = """ROL: Eres 'Kiwigeek AI', vendedor experto en PCs.

REGLAS OBLIGATORIAS:
1. SIEMPRE genera EXACTAMENTE 3 OPCIONES (A, B, C)
2. TODOS los componentes DEBEN tener el link [Ver Producto](url)
3. NUNCA uses HTML, solo Markdown simple

--- FORMATO EXACTO ---

OPCIÓN A: AHORRO ÉPICO

Estrategia: Máximo rendimiento recortando lo estético.

- **PROCESADOR:** AMD Ryzen 5 5600 - S/ 422 → [Ver Producto](url_del_json)
- **PLACA:** ASRock B450M Steel Legend - S/ 439 → [Ver Producto](url_del_json)
- **RAM:** Team DDR4 16GB 3200MHz - S/ 250 → [Ver Producto](url_del_json)
- **GPU:** Gigabyte GeForce RTX 3060 - S/ 918 → [Ver Producto](url_del_json)
- **SSD:** Team MP33 512GB - S/ 170 → [Ver Producto](url_del_json)
- **FUENTE:** Seasonic A12 600W - S/ 412 → [Ver Producto](url_del_json)

TOTAL CONTADO: S/ 2,611.00

---

OPCIÓN B: EQUILIBRIO GAMER

Estrategia: Componentes de buena calidad para rendimiento sólido.

- **PROCESADOR:** Intel Core i5-12400F - S/ 570 → [Ver Producto](url)
- **PLACA:** MSI B660M-A DDR4 - S/ 599 → [Ver Producto](url)
  💡 Tecnología 12va Gen: Mejor eficiencia y mayor rendimiento por núcleo
- **RAM:** Corsair Vengeance 16GB - S/ 350 → [Ver Producto](url)
- **GPU:** ASUS TUF RTX 4060 - S/ 1,399 → [Ver Producto](url)
  💡 Potencia Gráfica: Juega en Ultra con Ray Tracing y DLSS 3
- **SSD:** Kingston NV2 1TB - S/ 280 → [Ver Producto](url)
- **FUENTE:** EVGA 650W 80+ Gold - S/ 450 → [Ver Producto](url)

TOTAL CONTADO: S/ 3,648.00

---

OPCIÓN C: MÁXIMA POTENCIA

Estrategia: Exprimir cada sol en GPU y componentes premium.

(componentes con insights en GPU, RAM DDR5, Fuente)

TOTAL CONTADO: S/ 4,200.00

--- LÓGICA DE COTIZACIÓN ---

1. OPCIÓN A: Presupuesto - 10% (Ahorro)
2. OPCIÓN B: Presupuesto exacto (Equilibrio)
3. OPCIÓN C: Presupuesto + 15% (Premium)

CRÍTICO: Si subes GPU en C, DEBES subir la Fuente también.
Orden: CPU → Placa → RAM → GPU → SSD → Fuente → Case (si aplica)

Insights (💡) solo en opciones B y C para: GPU, RAM DDR5, Fuente Premium.
"""
        
        return client.caches.create(
            model=MODEL_ID,
            config=types.CreateCachedContentConfig(
                display_name='kiwigeek_3options_links',
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
    <div style="text-align:center; padding: 20px 0 30px 0;">
        <img src="https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png" height="80">
        <h1 class='neon-title'>KIWIGEEK AI</h1>
        <p style='color:#6c757d; font-size:0.95rem; margin-top:10px;'>Ingeniero de Hardware Inteligente</p>
    </div>
""", unsafe_allow_html=True)

# Renderizar mensajes
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message(msg["role"], avatar=AVATAR_URL):
            st.markdown(parse_and_render(msg["content"]), unsafe_allow_html=True)
    else:
        with st.chat_message("user", avatar="👤"):
            st.markdown(f"<div style='color:#212529;'>{msg['content']}</div>", unsafe_allow_html=True)

# Input
if prompt := st.chat_input("Ej: Tengo S/ 4000 para Solo Torre"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(f"<div style='color:#212529;'>{prompt}</div>", unsafe_allow_html=True)

    with st.chat_message("assistant", avatar=AVATAR_URL):
        with st.spinner("🤖 Analizando catálogo y preparando 3 opciones..."):
            try:
                if "chat_session" not in st.session_state:
                    st.error("Error: Sesión perdida. Recarga la página.")
                    st.stop()
                
                response = st.session_state.chat_session.send_message(prompt)
                raw_text = response.text
                
                # Renderizar
                st.markdown(parse_and_render(raw_text), unsafe_allow_html=True)
                
                # Guardar
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": raw_text
                })
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                if "chat_session" in st.session_state:
                    del st.session_state["chat_session"]
