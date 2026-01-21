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

# --- CSS MEJORADO (Estilo Moderno y Limpio) ---
def apply_custom_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        * { 
            font-family: 'Inter', sans-serif !important; 
        }
        
        /* Título Principal */
        .neon-title {
            color: #00FF41 !important;
            text-shadow: 0 0 20px rgba(0,255,65,0.5);
            text-align: center;
            font-weight: 900 !important;
            font-size: 3.5rem !important;
            margin: 0;
            letter-spacing: -1px;
        }
        
        /* Tarjetas de Cotización */
        .quote-card {
            background: linear-gradient(135deg, #1a1a1a 0%, #252525 100%);
            border: 2px solid #00FF41;
            border-radius: 16px;
            padding: 24px;
            margin: 20px 0;
            box-shadow: 0 8px 32px rgba(0,255,65,0.15);
        }
        
        .quote-header {
            background: #00FF41;
            color: #000;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 800;
            font-size: 1.3rem;
            margin-bottom: 16px;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .quote-strategy {
            background: #2a2a2a;
            color: #00FF41;
            padding: 10px 16px;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 20px;
            border-left: 4px solid #00FF41;
        }
        
        /* Items de Componentes */
        .component-item {
            background: #1e1e1e;
            border-left: 3px solid #444;
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 6px;
            transition: all 0.3s;
        }
        
        .component-item:hover {
            border-left-color: #00FF41;
            background: #252525;
            transform: translateX(4px);
        }
        
        .component-category {
            color: #00FF41;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 4px;
        }
        
        .component-name {
            color: #fff;
            font-size: 1rem;
            font-weight: 500;
            margin-bottom: 4px;
        }
        
        .component-name a {
            color: #fff;
            text-decoration: none;
            transition: color 0.3s;
        }
        
        .component-name a:hover {
            color: #00FF41;
            text-decoration: underline;
        }
        
        .component-price {
            color: #00FF41;
            font-size: 1.1rem;
            font-weight: 700;
        }
        
        .insight-box {
            background: rgba(0,255,65,0.1);
            border-left: 4px solid #00FF41;
            padding: 10px 14px;
            margin: 8px 0 8px 20px;
            border-radius: 6px;
            font-size: 0.9rem;
            color: #ccc;
        }
        
        /* Total */
        .quote-total {
            background: #000;
            border: 2px solid #00FF41;
            border-radius: 10px;
            padding: 16px;
            margin-top: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .total-label {
            color: #aaa;
            font-size: 1rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .total-amount {
            color: #00FF41;
            font-size: 2rem;
            font-weight: 900;
            text-shadow: 0 0 15px rgba(0,255,65,0.4);
        }
        
        /* Botón WhatsApp */
        .btn-whatsapp {
            display: block;
            width: 100%;
            background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
            color: white !important;
            text-align: center;
            padding: 16px;
            border-radius: 12px;
            font-weight: 800;
            font-size: 1.1rem;
            text-decoration: none !important;
            margin-top: 24px;
            transition: all 0.3s;
            box-shadow: 0 6px 20px rgba(37,211,102,0.3);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .btn-whatsapp:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(37,211,102,0.5);
        }
        
        /* Warning Box */
        .warning-box {
            background: #332200;
            border: 2px solid #ffcc00;
            color: #ffcc00;
            padding: 16px;
            border-radius: 10px;
            font-size: 0.95rem;
            margin: 20px 0;
        }
        
        /* Ajustes UI */
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
        </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# --- DATOS DUMMY ---
if not os.path.exists('catalogo_kiwigeek.json'):
    with open('catalogo_kiwigeek.json', 'w') as f:
        import json
        json.dump({"products": []}, f)

# --- FUNCIÓN PARA CONVERTIR MARKDOWN A HTML ---
def markdown_to_html(text):
    """Convierte el formato Markdown de la IA a HTML bonito"""
    
    # Detectar si es una respuesta simple (no cotización)
    if not "===" in text:
        return f"<div style='color:#ddd; line-height:1.6;'>{text}</div>"
    
    html_parts = []
    current_option = None
    current_components = []
    current_insights = []
    
    lines = text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Detectar inicio de opción
        if line.startswith('===') and 'OPCIÓN' in line:
            # Guardar opción anterior si existe
            if current_option:
                html_parts.append(render_option_card(
                    current_option, 
                    current_components, 
                    current_insights
                ))
            
            # Nueva opción
            match = re.search(r'OPCIÓN ([ABC]) - (.+?) ===', line)
            if match:
                current_option = {
                    'letter': match.group(1),
                    'title': match.group(2).strip(),
                    'strategy': '',
                    'total': 0
                }
                current_components = []
                current_insights = []
        
        # Estrategia
        elif line.startswith('> ESTRATEGIA:'):
            if current_option:
                current_option['strategy'] = line.replace('> ESTRATEGIA:', '').strip()
        
        # Componente
        elif line.startswith('*'):
            component_data = parse_component_line(line)
            if component_data:
                current_components.append(component_data)
        
        # Insight (💡)
        elif '💡' in line:
            insight_text = line.replace('💡', '').strip()
            if insight_text:
                current_insights.append(insight_text)
        
        # Total
        elif line.startswith('TOTAL:'):
            if current_option:
                match = re.search(r'S/\s*([\d,\.]+)', line)
                if match:
                    current_option['total'] = match.group(1)
        
        i += 1
    
    # Guardar última opción
    if current_option:
        html_parts.append(render_option_card(
            current_option, 
            current_components, 
            current_insights
        ))
    
    # Agregar botón WhatsApp
    html_parts.append(f"""
        <a href="{WHATSAPP_LINK}" target="_blank" class="btn-whatsapp">
            🚀 Solicitar Descuento Exclusivo en WhatsApp
        </a>
    """)
    
    return ''.join(html_parts)

def parse_component_line(line):
    """Extrae información de una línea de componente"""
    # Formato: * [CATEGORÍA]: [Nombre] ... S/ [Precio] -> [Ver Producto](URL)
    
    # Extraer categoría
    cat_match = re.search(r'\*\s*\[([^\]]+)\]:', line)
    if not cat_match:
        return None
    
    category = cat_match.group(1).strip()
    
    # Extraer precio
    price_match = re.search(r'S/\s*([\d,\.]+)', line)
    price = price_match.group(1) if price_match else "0"
    
    # Extraer nombre y URL
    link_match = re.search(r'\[Ver Producto\]\(([^\)]+)\)', line)
    url = link_match.group(1) if link_match else "#"
    
    # Nombre del producto (entre categoría y precio)
    name_part = line.split(']:', 1)[1] if ']:' in line else ""
    name_part = name_part.split('...')[0].strip() if '...' in name_part else name_part
    name_part = name_part.split('S/')[0].strip()
    name = name_part[:100]  # Limitar longitud
    
    return {
        'category': category,
        'name': name,
        'price': price,
        'url': url
    }

def render_option_card(option, components, insights):
    """Renderiza una tarjeta de opción completa"""
    
    components_html = ""
    insight_index = 0
    
    for comp in components:
        components_html += f"""
        <div class="component-item">
            <div class="component-category">{comp['category']}</div>
            <div class="component-name">
                <a href="{comp['url']}" target="_blank">{comp['name']}</a>
            </div>
            <div class="component-price">S/ {comp['price']}</div>
        </div>
        """
        
        # Agregar insight si corresponde a este componente
        if insight_index < len(insights):
            # Los insights suelen ir después de GPU, RAM, Fuente, etc.
            if any(keyword in comp['category'].upper() for keyword in ['GPU', 'RAM', 'FUENTE', 'DDR5']):
                components_html += f"""
                <div class="insight-box">
                    💡 {insights[insight_index]}
                </div>
                """
                insight_index += 1
    
    return f"""
    <div class="quote-card">
        <div class="quote-header">
            Opción {option['letter']}: {option['title']}
        </div>
        <div class="quote-strategy">
            📋 Estrategia: {option['strategy']}
        </div>
        {components_html}
        <div class="quote-total">
            <span class="total-label">Total Contado</span>
            <span class="total-amount">S/ {option['total']}</span>
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
    """Configura el cerebro de Kiwigeek con el prompt original (Markdown)"""
    try:
        with open('catalogo_kiwigeek.json', 'r', encoding='utf-8') as f: 
            catalog = f.read()
            
        sys_prompt = (
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
            "Usa este formato EXACTO. NO repitas la URL en el texto del link:\n\n"
            "=== OPCIÓN [A/B/C] - [NOMBRE] ===\n"
            "> ESTRATEGIA: [Resumen de 1 línea]\n"
            "* [CATEGORÍA]: [Nombre Producto] ... S/ [Precio] -> [Ver Producto](URL_DEL_JSON)\n"
            "  💡 [Insight si aplica]\n"
            "... (Lista resto de componentes) ...\n"
            "----------------------------------\n"
            "TOTAL: S/ [SUMA EXACTA]\n\n"
            
            "--- CIERRE DE VENTA ---\n"
            "Finaliza con:\n"
            "'⚠ **ATENCIÓN:** Si decides comprar tu **PC COMPLETA** con nosotros, comunícate al WhatsApp para aplicarte un **DESCUENTO ADICIONAL EXCLUSIVO**.'\n"
        )
        
        return client.caches.create(
            model=MODEL_ID,
            config=types.CreateCachedContentConfig(
                display_name='kiwigeek_markdown_style',
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
            "content": "¡Hola! Soy **Kiwigeek AI**. 🥝\n\nDime tu presupuesto y si buscas **Solo Torre** o **PC Completa**."
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
        <p style='color:#666; font-size:0.9rem;'>Ingeniería de Hardware - Estilo Markdown</p>
    </div>
""", unsafe_allow_html=True)

# Renderizar mensajes anteriores
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message(msg["role"], avatar=AVATAR_URL):
            st.markdown(markdown_to_html(msg["content"]), unsafe_allow_html=True)
    else:
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["content"])

# Input del usuario
if prompt := st.chat_input("Ej: Tengo S/ 3800 para PC Completa..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=AVATAR_URL):
        with st.spinner("🤖 Analizando catálogo y preparando opciones..."):
            try:
                if "chat_session" not in st.session_state:
                    st.error("Error: Sesión perdida. Por favor recarga la página.")
                    st.stop()
                
                response = st.session_state.chat_session.send_message(prompt)
                raw_text = response.text
                
                # Renderizar directamente
                st.markdown(markdown_to_html(raw_text), unsafe_allow_html=True)
                
                # Guardar en historial
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": raw_text
                })
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                if "chat_session" in st.session_state:
                    del st.session_state["chat_session"]
