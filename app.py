import streamlit as st
import os
import json
import random
import re
import ast # Importado para reparaciones de emergencia
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

# --- MOTORES DE LÓGICA (EXTRACTOR BLINDADO V32) ---

def extract_json_from_text(text):
    """
    Intenta reparar y extraer JSON incluso si la IA lo envía mal formado.
    """
    text_clean = text
    try:
        # 1. Intentar capturar el bloque JSON más grande posible
        # Buscamos desde la primera llave abierta hasta la última cerrada
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            text_clean = match.group(0)
        
        # 2. LIMPIEZA QUIRÚRGICA
        # Eliminar comentarios JS (// ...)
        text_clean = re.sub(r'//.*?\n', '\n', text_clean)
        # Corregir comas finales en objetos/listas (Error muy común: {a:1,})
        text_clean = re.sub(r',\s*\}', '}', text_clean)
        text_clean = re.sub(r',\s*\]', ']', text_clean)
        # Normalizar booleanos y nulos (Python vs JSON)
        text_clean = text_clean.replace("True", "true").replace("False", "false").replace("None", "null")
        
        # 3. Intentar parsear como JSON estándar
        return json.loads(text_clean)
    except:
        # 4. PLAN B: Intentar parsear como estructura de Python (ast)
        # Esto ayuda si la IA usó comillas simples o True/False
        try:
            # Revertimos a formato Python para ast.literal_eval
            text_python = text_clean.replace("true", "True").replace("false", "False").replace("null", "None")
            return ast.literal_eval(text_python)
        except:
            pass
    return None

def render_vertical_option(option):
    """Renderiza UNA opción en formato vertical limpio."""
    title = option.get('title', 'Opción')
    strategy = option.get('strategy', '')
    
    # ORDENAMIENTO: Confianza total en el orden que envía la IA
    components = option.get('components', []) 
    
    total = sum(float(c.get('price', 0)) for c in components)
    
    rows_html = ""
    for c in components:
        # Normalizar nombres de categoría para mostrar
        cat_raw = c.get('category', 'Componente').upper()
        cat_display = cat_raw
        # Pequeño mapa de visualización para que se vea prolijo
        if "PROCESADOR" in cat_raw or "CPU" in cat_raw: cat_display = "PROCESADOR"
        elif "PLACA" in cat_raw: cat_display = "PLACA MADRE"
        elif "VIDEO" in cat_raw or "GPU" in cat_raw: cat_display = "TARJETA VIDEO"
        elif "RAM" in cat_raw: cat_display = "MEMORIA RAM"
        elif "FUENTE" in cat_raw: cat_display = "FUENTE PODER"
        elif "ALMACENAMIENTO" in cat_raw or "SSD" in cat_raw: cat_display = "ALMACENAMIENTO"
        
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
    
    # Si sigue sin ser válido, mostramos mensaje de error en lugar de texto crudo
    if not data or not isinstance(data, dict): 
        return """
        <div style="background:#330000; color:#ffcccc; padding:15px; border-radius:8px;">
            ⚠️ <b>Error de Formato:</b> La IA generó una respuesta que no se pudo procesar visualmente.
            Por favor, intenta preguntar de nuevo.
        </div>
        """
        
    if not data.get("is_quote"): return data.get("message", text)
    
    html = f"<div style='margin-bottom:20px; color:#ddd;'>{data.get('intro','')}</div>"
    
    # Renderizar opciones
    for opt in data.get('options', []):
        html += render_vertical_option(opt)
    
    # Mensaje de filtrado
    if filtered_count > 0:
        html += f"""
        <div style="background:#332200; border:1px solid #664400; color:#ffcc00; padding:10px; border-radius:8px; font-size:0.9rem; margin-top:10px;">
            ⚠️ <b>Nota:</b> Se ocultaron {filtered_count} opción(es) porque excedían tu presupuesto. 
            ¿Deseas ver opciones más económicas?
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
            "ERES KIWIGEEK AI. TU OBJETIVO: GENERAR JSON PERFECTO Y ORDENADO.\n"
            "INPUT: Usuario pide PC y da presupuesto.\n"
            "OUTPUT: JSON estricto sin comentarios.\n\n"
            "--- VALIDACIÓN ---\n"
            "Si falta 'Solo Torre' o 'PC Completa', pregunta primero.\n"
            "{ \"is_quote\": false, \"message\": \"...\" }\n\n"
            "--- COTIZACIÓN ---\n"
            "Genera 3 opciones (A, B, C).\n"
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
            "         {\"category\": \"PROCESADOR\", \"name\": \"...\", \"price\": 0, \"url\": \"...\"},\n"
            "         {\"category\": \"PLACA\", \"name\": \"...\", \"price\": 0, \"url\": \"...\"}\n"
            "      ]\n"
            "    }\n"
            "  ],\n"
            "  \"outro\": \"...\"\n"
            "}\n"
            "```\n"
            "REGLAS CRÍTICAS:\n"
            "1. NO COMENTARIOS (//). JSON PURO.\n"
            "2. ORDEN VISUAL ES TU RESPONSABILIDAD: Debes ordenar la lista 'components' así:\n"
            "   1. PROCESADOR\n"
            "   2. PLACA MADRE\n"
            "   3. RAM\n"
            "   4. GPU\n"
            "   5. SSD\n"
            "   6. FUENTE\n"
            "   7. CASE\n"
            "   8. (MONITOR/PERIFÉRICOS)\n"
        )
        
        return client.caches.create(
            model=MODEL_ID,
            config=types.CreateCachedContentConfig(
                display_name='kiwigeek_v32_bulletproof_json',
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
        <p style='color:#666;'>Ingeniería de Hardware v32.0</p>
    </div>
""", unsafe_allow_html=True)

# Renderizar mensajes anteriores
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message(msg["role"], avatar=AVATAR_URL):
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
                
                # 2. FILTRO Y AUDITORÍA (LOOP DE CORRECCIÓN)
                max_retries = 3 
                attempt = 0
                final_json = None
                filtered_count = 0
                
                while attempt < max_retries:
                    data = extract_json_from_text(raw)
                    
                    if not data or not isinstance(data, dict): 
                        attempt += 1
                        print("Error formato JSON. Reintentando...")
                        msg = "ERROR: JSON INVALID. Return ONLY valid JSON. Check brackets and commas."
                        raw = st.session_state.chat_session.send_message(msg).text
                        continue 
                    
                    if not data.get("is_quote"):
                        final_json = json.dumps(data)
                        break
                    
                    budget = float(data.get("detected_budget", 0))
                    # Respaldo de presupuesto
                    if budget == 0:
                        nums = re.findall(r'\d+', prompt.replace(',', ''))
                        if nums: budget = float(max(nums, key=len))
                    
                    valid_options = []
                    filtered_in_this_run = 0
                    
                    if budget > 0:
                        for opt in data.get('options', []):
                            total = sum(float(c.get('price', 0)) for c in opt.get('components', []))
                            limit = budget * 1.15
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
                            msg = f"ERROR: All options too expensive (Budget: {budget}). Regenerate CHEAPER options."
                            raw = st.session_state.chat_session.send_message(msg).text
                            continue
                    else:
                        final_json = json.dumps(data)
                        break
                
                # Si falló todo, mostramos mensaje de error
                if final_json is None: 
                    final_json = raw # Guardamos lo que haya para debug, pero el render mostrará error
                
                # 3. Renderizar
                final_html = process_response(final_json, filtered_count)
                placeholder.markdown(final_html, unsafe_allow_html=True)
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": final_json,
                    "filtered_count": filtered_count
                })
                
            except Exception as e:
                st.error(f"Error crítico: {str(e)}")
                if "chat_session" in st.session_state: del st.session_state["chat_session"]
                # st.rerun()
