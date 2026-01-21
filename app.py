import streamlit as st
import os
import json
import random
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
COLORS = {
    "kiwi_green": "#00FF41",
    "bg_card": "#1E1E1E",
    "border": "#333"
}
AVATAR_URL = "https://kiwigeekperu.com/wp-content/uploads/2026/01/gatitow.webp"
WHATSAPP_LINK = "https://api.whatsapp.com/send/?phone=51939081940&text=Hola%2C+me+gustar%C3%ADa+saber+m%C3%A1s+de+sus+productos&type=phone_number&app_absent=0"

USER_AVATARS = ["🧑‍💻", "👨‍💻", "👩‍💻", "🦸", "🦹", "🧙", "🧚", "🧛", "🧜", "🧝"]

# --- CSS LIMPIO Y ORDENADO ---
def apply_custom_styles():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        * {{ font-family: 'Inter', sans-serif !important; }}
        
        /* Título Neón */
        .neon-title {{
            color: {COLORS['kiwi_green']} !important;
            text-shadow: 0 0 15px rgba(0,255,65,0.4);
            text-align: center;
            font-weight: 900 !important;
            font-size: 3rem !important;
            margin: 0;
            line-height: 1;
        }}

        /* Tarjeta de Opción (Vertical y Limpia) */
        .quote-container {{
            background-color: #222;
            border: 1px solid #444;
            border-radius: 8px;
            margin-bottom: 25px;
            overflow: hidden;
        }}
        .quote-header {{
            background-color: {COLORS['kiwi_green']};
            color: #000;
            padding: 10px 15px;
            font-weight: 800;
            font-size: 1.1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .quote-strategy {{
            font-size: 0.8rem; 
            color: #222; 
            font-weight: 500;
        }}
        
        /* Tabla de Componentes */
        .comp-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .comp-row {{
            border-bottom: 1px solid #333;
            display: flex;
            padding: 8px 15px;
            align-items: center;
        }}
        .comp-row:last-child {{ border-bottom: none; }}
        
        .c-label {{
            width: 30%;
            color: #888;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .c-val {{
            width: 50%;
            color: #eee;
            font-size: 0.95rem;
        }}
        .c-val a {{ color: #fff; text-decoration: none; font-weight:500; }}
        .c-val a:hover {{ text-decoration: underline; color: {COLORS['kiwi_green']}; }}
        
        .c-price {{
            width: 20%;
            text-align: right;
            color: {COLORS['kiwi_green']};
            font-weight: 700;
            font-size: 0.95rem;
        }}
        
        .quote-total {{
            background-color: #111;
            padding: 12px 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid #444;
        }}
        .t-num {{
            color: {COLORS['kiwi_green']};
            font-size: 1.3rem;
            font-weight: 900;
        }}

        /* Botón WhatsApp */
        .btn-whatsapp {{
            display: block;
            width: 100%;
            background-color: #25D366;
            color: white !important;
            text-align: center;
            padding: 12px;
            border-radius: 8px;
            font-weight: 700;
            text-decoration: none !important;
            margin-top: 20px;
            transition: background 0.3s;
        }}
        .btn-whatsapp:hover {{ background-color: #1ebc57; }}
        
        /* Ajustes UI */
        .stChatMessage {{ background: transparent !important; }}
        [data-testid="stChatMessageAssistant"] {{ background: rgba(255,255,255,0.03) !important; border: 1px solid #333; }}
        footer {{visibility: hidden;}}
        </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# --- DATOS DUMMY ---
if not os.path.exists('catalogo_kiwigeek.json'):
    with open('catalogo_kiwigeek.json', 'w') as f: json.dump({"products": []}, f)

# --- MOTORES DE LÓGICA ---

def extract_json_from_text(text):
    """Extrae JSON limpio y repara errores comunes de IA (CIRUJANO DE CÓDIGO)."""
    try:
        # 1. Buscar bloque de código ```json ... ```
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        content = json_match.group(1) if json_match else text
        
        # 2. Limpieza agresiva: Encontrar primer { y último }
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1:
            json_str = content[start:end+1]
            
            # --- CIRUGÍA PLÁSTICA DE DATOS ---
            # 1. Eliminar comentarios de estilo JS que la IA a veces pone (// ...)
            json_str = re.sub(r'//.*', '', json_str)
            # 2. Eliminar comas traicioneras al final de listas u objetos (error común: {a:1,})
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            
            return json.loads(json_str)
    except:
        pass
    return None

def render_vertical_option(option):
    """Renderiza UNA opción en formato vertical limpio."""
    title = option.get('title', 'Opción')
    strategy = option.get('strategy', '')
    
    # --- CAMBIO V28: ORDENAMIENTO POR IA (Python respeta el orden del JSON) ---
    components = option.get('components', []) 
    
    total = sum(float(c.get('price', 0)) for c in components)
    
    rows_html = ""
    for c in components:
        # Normalizar nombres de categoría para mostrar
        cat_raw = c.get('category', 'Componente').upper()
        cat_display = cat_raw
        if "PROCESADOR" in cat_raw or "CPU" in cat_raw: cat_display = "PROCESADOR"
        elif "PLACA" in cat_raw: cat_display = "PLACA MADRE"
        elif "VIDEO" in cat_raw or "GPU" in cat_raw: cat_display = "TARJETA VIDEO"
        elif "RAM" in cat_raw: cat_display = "MEMORIA RAM"
        elif "FUENTE" in cat_raw: cat_display = "FUENTE PODER"
        
        name = c.get('name', 'Producto')
        url = c.get('url', '#')
        price = float(c.get('price', 0))
        
        rows_html += f"""
        <div class="comp-row">
            <div class="c-label">{cat_display}</div>
            <div class="c-val"><a href="{url}" target="_blank">{name}</a></div>
            <div class="c-price">S/ {price:,.0f}</div>
        </div>
        """
        
    return f"""
    <div class="quote-container">
        <div class="quote-header">
            <span>{title}</span>
            <span class="quote-strategy">{strategy}</span>
        </div>
        <div class="comp-table">
            {rows_html}
        </div>
        <div class="quote-total">
            <span style="color:#aaa; font-weight:600;">TOTAL CONTADO</span>
            <span class="t-num">S/ {total:,.2f}</span>
        </div>
    </div>
    """

def process_response(text, filtered_count=0):
    """Renderiza la respuesta final."""
    data = extract_json_from_text(text)
    
    # Si no es JSON válido (o es texto plano), lo mostramos limpio sin el disfraz de código
    if not data or not isinstance(data, dict): 
        # Limpieza de emergencia: Si quedó como código, quítale el disfraz para que se lea bien
        clean_text = text.replace("```json", "").replace("```", "")
        return clean_text
        
    if not data.get("is_quote"): return data.get("message", text)
    
    html = f"<div style='margin-bottom:20px; color:#ddd;'>{data.get('intro','')}</div>"
    
    # Renderizar solo las opciones válidas (que ya fueron filtradas en el loop principal)
    for opt in data.get('options', []):
        html += render_vertical_option(opt)
    
    # Mensaje si se filtraron opciones
    if filtered_count > 0:
        html += f"""
        <div style="background:#332200; border:1px solid #664400; color:#ffcc00; padding:10px; border-radius:8px; font-size:0.9rem; margin-top:10px;">
            ⚠️ <b>Nota:</b> Se ocultaron {filtered_count} opción(es) porque excedían demasiado tu presupuesto. 
            ¿Te gustaría ver opciones más económicas o ajustar el presupuesto?
        </div>
        """
    
    html += f"""
    <div style='margin-top:20px; color:#ddd;'>{data.get('outro','')}</div>
    <a href="{WHATSAPP_LINK}" target="_blank" class="btn-whatsapp">
        🚀 SOLICITAR DESCUENTO EXCLUSIVO EN WHATSAPP
    </a>
    """
    return html

# --- CONFIGURACIÓN DE IA ---
def get_api_key():
    try: return st.secrets["GEMINI_API_KEY"]
    except: return os.getenv("GEMINI_API_KEY", "")

api_key = get_api_key()
if not api_key:
    with st.sidebar:
        st.warning("⚠️ API Key no encontrada")
        st.stop()

client = genai.Client(api_key=api_key)
MODEL_ID = 'models/gemini-2.0-flash'

@st.cache_resource
def setup_kiwi_brain():
    try:
        with open('catalogo_kiwigeek.json', 'r', encoding='utf-8') as f: 
            catalog = f.read()
            
        sys_prompt = (
            "ERES KIWIGEEK AI. TU OBJETIVO: GENERAR JSON PERFECTO PARA COTIZAR PC.\n"
            "INPUT: Usuario pide PC y da presupuesto.\n"
            "OUTPUT: JSON estricto sin comentarios //.\n\n"
            "--- FASE 1: VALIDACIÓN ---\n"
            "Si el usuario NO dice si quiere 'Solo Torre' o 'PC Completa', devuelve:\n"
            "{ \"is_quote\": false, \"message\": \"👋 Hola, para ajustarme a tu presupuesto, ¿necesitas solo la torre (CPU) o la PC completa con monitor?\" }\n\n"
            "--- FASE 2: GENERACIÓN (3 OPCIONES) ---\n"
            "Genera SIEMPRE 3 opciones (A, B, C) intentando acercarte al presupuesto.\n"
            "JSON OBLIGATORIO:\n"
            "```json\n"
            "{\n"
            "  \"is_quote\": true,\n"
            "  \"detected_budget\": 0,\n"
            "  \"intro\": \"Texto breve...\",\n"
            "  \"options\": [\n"
            "    {\n"
            "      \"title\": \"Opción A\", \"strategy\": \"...\",\n"
            "      \"components\": [\n"
            "         {\"category\": \"CPU\", \"name\": \"...\", \"price\": 0, \"url\": \"...\"},\n"
            "         {\"category\": \"PLACA\", \"name\": \"...\", \"price\": 0, \"url\": \"...\"}\n"
            "      ]\n"
            "    }\n"
            "  ],\n"
            "  \"outro\": \"...\"\n"
            "}\n"
            "```\n"
            "REGLAS:\n"
            "1. NO sumes totales. Solo precios unitarios.\n"
            "2. Incluye TODOS los componentes necesarios.\n"
            "3. ORDENA OBLIGATORIAMENTE la lista 'components' así: PROCESADOR -> PLACA -> RAM -> GPU -> SSD -> FUENTE -> CASE -> (MONITOR/PERIFÉRICOS).\n"
        )
        
        return client.caches.create(
            model=MODEL_ID,
            config=types.CreateCachedContentConfig(
                display_name='kiwigeek_v28_ai_sort_prompt',
                system_instruction=sys_prompt,
                contents=[catalog],
                ttl='7200s'
            )
        ).name, None
    except Exception as e:
        return None, str(e)

# --- APP MAIN LOOP ---
if "messages" not in st.session_state: st.session_state.messages = []
if "chat_session" not in st.session_state:
    cache_name, err = setup_kiwi_brain()
    if err and "catalogo" not in err: st.error(err); st.stop()
    
    config = types.GenerateContentConfig(temperature=0.1, top_p=0.8, max_output_tokens=8192)
    if cache_name: config.cached_content = cache_name
    
    st.session_state.chat_session = client.chats.create(model=MODEL_ID, config=config)
    
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
        del st.session_state["chat_session"]
        st.rerun()

st.markdown("""
    <div style="text-align:center; padding-bottom: 20px;">
        <img src="https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png" height="80">
        <h1 class='neon-title'>AI</h1>
        <p style='color:#666;'>Ingeniería de Hardware v28.0</p>
    </div>
""", unsafe_allow_html=True)

# Renderizar mensajes anteriores
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message(msg["role"], avatar=AVATAR_URL):
            # Recuperamos metadata si existe
            filtered = msg.get("filtered_count", 0)
            st.markdown(process_response(msg["content"], filtered), unsafe_allow_html=True)
    else:
        with st.chat_message("user", avatar=random.choice(USER_AVATARS)):
            st.markdown(msg["content"])

if prompt := st.chat_input("Ej: Tengo S/ 3800 para PC Completa..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=random.choice(USER_AVATARS)):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=AVATAR_URL):
        placeholder = st.empty()
        with st.spinner("🤖 Analizando y auditando opciones..."):
            try:
                # 1. Generación
                if "chat_session" not in st.session_state: raise Exception("Reload")
                response = st.session_state.chat_session.send_message(prompt)
                raw = response.text
                
                # 2. FILTRO Y AUDITORÍA
                max_retries = 2
                attempt = 0
                final_json = None
                filtered_count = 0
                
                while attempt < max_retries:
                    data = extract_json_from_text(raw)
                    
                    if not data or not isinstance(data, dict): 
                        final_json = raw # Fallback a texto limpio
                        break
                    
                    if not data.get("is_quote"):
                        final_json = json.dumps(data)
                        break
                    
                    budget = float(data.get("detected_budget", 0))
                    if budget == 0: 
                        final_json = json.dumps(data)
                        break
                    
                    valid_options = []
                    filtered_in_this_run = 0
                    
                    for opt in data.get('options', []):
                        total = sum(float(c['price']) for c in opt['components'])
                        limit = budget * 1.10
                        if total <= limit:
                            valid_options.append(opt)
                        else:
                            filtered_in_this_run += 1
                    
                    if len(valid_options) > 0:
                        data['options'] = valid_options
                        final_json = json.dumps(data)
                        filtered_count = filtered_in_this_run
                        break 
                    else:
                        attempt += 1
                        msg = f"ERROR: All options exceeded budget S/ {budget}. REGENERATE CHEAPER options."
                        raw = st.session_state.chat_session.send_message(msg).text
                
                if final_json is None: final_json = raw.replace("```json", "").replace("```", "")
                
                # 3. Renderizar
                final_html = process_response(final_json, filtered_count)
                placeholder.markdown(final_html, unsafe_allow_html=True)
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": final_json,
                    "filtered_count": filtered_count
                })
                
            except:
                st.error("Conexión perdida. Reiniciando cerebro...")
                if "chat_session" in st.session_state: del st.session_state["chat_session"]
                st.rerun()
