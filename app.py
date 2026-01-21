import streamlit as st
import os
import json
import random
import re # Importamos expresiones regulares para detectar el JSON
from google import genai
from google.genai import types

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Kiwigeek AI - Hardware Engineer",
    page_icon="🐱",
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
WHATSAPP_LINK = "https://api.whatsapp.com/send/?phone=51939081940&text=Hola%2C+me+gustar%C3%ADa+saber+m%C3%A1s+de+sus+productos&type=phone_number&app_absent=0"

# --- LISTA DE AVATARES RANDOM PARA USUARIO ---
USER_AVATARS = [
    "🧑‍💻", "👨‍💻", "👩‍💻", "🦸", "🦹", "🧙", "🧚", "🧛", "🧜", "🧝", 
    "🧞", "🧟", "💆", "💇", "🚶", "🏃", "💃", "🕺", "🕴", "👯", 
    "🧖", "🧗", "🤺", "🏇", "⛷", "🏂", "🏌️", "🏄", "🚣", "🏊", 
    "⛹️", "🏋️", "🚴", "🚵", "🤸", "🤼", "🤽", "🤾", "🤹", "🧘", 
    "🛀", "🛌", "🧑", "🧒", "👦", "👧", "🧑‍🦱", "👨‍🦱", "👩‍🦱", "🧑‍🦰",
    "😎", "🤓", "🤠", "🥳", "👽", "🤖", "👮", "🕵️", "💂", "👷"
]

# --- CSS MEJORADO ---
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

# --- FUNCIONES DE PARSEO Y AUDITORÍA ---
def extract_json_from_text(text):
    """Extrae el bloque JSON crudo del texto."""
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if not json_match:
        json_match = re.search(r'^\s*(\{.*\})\s*$', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except:
            return None
    return None

def parse_and_render_response(text):
    """Renderiza la respuesta JSON a Markdown bonito."""
    data = extract_json_from_text(text)
    if data and data.get("is_quote"):
        try:
            output = f"{data.get('intro', '')}\n\n"
            for opt in data.get('options', []):
                total_real = 0.0
                output += f"### {opt['title']}\n"
                output += f"> *{opt['strategy']}*\n\n"
                for item in opt['components']:
                    try:
                        price = float(item['price'])
                        total_real += price
                        icon = "💡" if item.get('highlight') else "🔹"
                        highlight_text = f" - *{item['highlight']}*" if item.get('highlight') else ""
                        output += f"{icon} **{item['category']}**: [{item['name']}]({item['url']}) ... S/ {price:.2f}{highlight_text}\n"
                    except: continue
                output += f"\n**💰 TOTAL EXACTO: S/ {total_real:,.2f}**\n"
                output += "---" + "\n\n"
            output += f"{data.get('outro', '')}\n\n"
            output += f"⚠ **ATENCIÓN:** Si decides comprar tu **PC COMPLETA** con nosotros, haz clic aquí para un **[DESCUENTO ADICIONAL EXCLUSIVO EN WHATSAPP]({WHATSAPP_LINK})**."
            return output
        except: return text
    return text

# --- LÓGICA DE CLIENTE Y CACHE ---
def get_api_key():
    try: return st.secrets["GEMINI_API_KEY"]
    except: return os.getenv("GEMINI_API_KEY", "")

api_key = get_api_key()
if not api_key:
    with st.sidebar:
        st.warning("⚠️ API Key no encontrada")
        api_key = st.text_input("Ingresa tu Gemini API Key:", type="password")
        if not api_key: st.stop()

client = genai.Client(api_key=api_key)
MODEL_ID = 'models/gemini-2.0-flash'

@st.cache_resource
def setup_kiwi_brain():
    """Inicializa con SISTEMA DE AUDITORÍA (V18)"""
    try:
        path = 'catalogo_kiwigeek.json'
        if not os.path.exists(path): return None, "Error: Archivo no encontrado."
        with open(path, 'r', encoding='utf-8') as f: catalog_data = f.read()

        system_instruction = (
            "ROL: Kiwigeek AI, Ingeniero experto. Responde SOLO en JSON para cotizaciones.\n"
            "CONTEXTO: Inventario con LINKS. Úsalos.\n\n"
            "--- JSON ESTRICTO ---\n"
            "Cuando te pidan PC, responde:\n"
            "```json\n"
            "{\n"
            '  "is_quote": true,\n'
            '  "detected_budget": 0,  // PON AQUÍ EL PRESUPUESTO QUE DETECTASTE (Número)\n'
            '  "intro": "...",\n'
            '  "options": [\n'
            '    {\n'
            '      "title": "Opción A", "strategy": "...",\n'
            '      "components": [{"category": "CPU", "name": "...", "price": 0, "url": "..."}]\n'
            '    }\n'
            '  ],\n'
            '  "outro": "..."\n'
            "}\n"
            "```\n"
            "REGLA DE ORO: Si el usuario dice 'S/ 3000', tus opciones deben sumar cerca de 3000. "
            "Máximo +15% de margen. Si te pasas, serás auditado y rechazado.\n"
        )

        try:
            cache = client.caches.create(
                model=MODEL_ID,
                config=types.CreateCachedContentConfig(
                    display_name='kiwigeek_v18_auditor',
                    system_instruction=system_instruction,
                    contents=[catalog_data],
                    ttl='7200s',
                )
            )
            return cache.name, None
        except:
            fallback = f"{system_instruction}\n\nCATÁLOGO:\n{catalog_data}"
            return None, fallback
    except Exception as e: return None, str(e)

# --- INICIO DE SESIÓN ---
if "messages" not in st.session_state: st.session_state.messages = []
if "is_cached_active" not in st.session_state: st.session_state.is_cached_active = False

if "chat_session" not in st.session_state:
    cache_name, fallback = setup_kiwi_brain()
    if fallback and fallback.startswith("Error"): st.error(fallback); st.stop()
    
    config = types.GenerateContentConfig(temperature=0.1, top_p=0.85, max_output_tokens=8192)
    if cache_name: config.cached_content = cache_name; st.session_state.is_cached_active = True
    else: config.system_instruction = fallback; st.session_state.is_cached_active = False
    
    st.session_state.chat_session = client.chats.create(model=MODEL_ID, config=config)

    if not st.session_state.messages:
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "¡Hola! Soy el asistente de **Kiwigeek**. 🐱\n\n¿Buscas una PC para gaming, diseño o trabajo pesado? Dime tu presupuesto y diseñaremos la mejor configuración para ti."
        })

# --- INTERFAZ ---
with st.sidebar:
    st.image('https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png')
    if st.session_state.is_cached_active: st.success("⚡ **Caché Activo**")
    else: st.warning("⚠️ **Modo Estándar**")
    st.markdown("---")
    if st.button("🗑️ Limpiar Conversación", use_container_width=True):
        st.session_state.messages = []
        if "chat_session" in st.session_state: del st.session_state["chat_session"]
        st.rerun()

st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; gap: 10px; padding-bottom: 10px;">
        <img src="https://kiwigeekperu.com/wp-content/uploads/2025/06/Diseno-sin-titulo-24.png" 
             style="height: 90px; object-fit: contain; filter: drop-shadow(0 0 5px rgba(0, 255, 65, 0.3));">
        <h1 class='neon-title' style='margin: 0; padding: 0; font-size: 3.5rem !important; display: inline-block;'>AI</h1>
    </div>
""", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Ingeniería de hardware de alto nivel</p>", unsafe_allow_html=True)

# Renderizado Historial
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message(msg["role"], avatar=AVATAR_URL):
            st.markdown(parse_and_render_response(msg["content"]))
    else:
        with st.chat_message(msg["role"], avatar=msg.get("avatar", USER_AVATARS[0])):
            st.markdown(msg["content"])

# INPUT Y LÓGICA PRINCIPAL CON AUDITORÍA
if prompt := st.chat_input("Ej: Tengo S/ 4000 para una PC de Streaming..."):
    current_avatar = random.choice(USER_AVATARS)
    st.session_state.messages.append({"role": "user", "content": prompt, "avatar": current_avatar})
    
    with st.chat_message("user", avatar=current_avatar):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=AVATAR_URL):
        placeholder = st.empty()
        with st.spinner("🔍 Analizando stock y auditando precios..."):
            try:
                if "chat_session" not in st.session_state: raise Exception("Sesión perdida")
                
                # 1. GENERACIÓN INICIAL
                response = st.session_state.chat_session.send_message(prompt)
                raw_text = response.text
                
                # 2. BUCLE DE AUDITORÍA Y CORRECCIÓN (MÁXIMO 2 INTENTOS)
                max_retries = 2
                attempt = 0
                
                while attempt < max_retries:
                    data = extract_json_from_text(raw_text)
                    
                    # Si no es JSON de cotización, salimos del bucle (es charla normal)
                    if not data or not data.get("is_quote") or not data.get("detected_budget"):
                        break
                        
                    budget = float(data.get("detected_budget", 0))
                    if budget == 0: break # Si no detectó presupuesto, no podemos auditar

                    feedback = []
                    needs_fix = False
                    
                    # Auditar cada opción
                    for opt in data.get('options', []):
                        total_real = sum(float(c['price']) for c in opt['components'] if str(c['price']).replace('.', '', 1).isdigit())
                        
                        # REGLA MAESTRA: 15% MARGEN MÁXIMO
                        limit = budget * 1.15 
                        
                        if total_real > limit:
                            needs_fix = True
                            diff = total_real - budget
                            feedback.append(f"• Opción '{opt['title']}' suma S/ {total_real:.2f} (Excede tu límite de S/ {limit:.2f} por S/ {diff:.2f}).")

                    if needs_fix:
                        attempt += 1
                        error_msg = (
                            f"AUDITORÍA DE PRECIOS FALLIDA: El presupuesto del cliente es S/ {budget}. "
                            f"Tus cotizaciones exceden el margen permitido del 15%:\n" + "\n".join(feedback) + 
                            "\n\nACCIÓN REQUERIDA: Recalcula INMEDIATAMENTE. Reduce GPU, baja a i3/Ryzen 5 si es necesario, "
                            "o quita componentes secundarios. ¡El total real calculado por Python no miente! Envía JSON corregido."
                        )
                        # Feedback invisible al usuario, solo interno para la IA
                        print(f"🔄 CORRIGIENDO (Intento {attempt}): {error_msg}")
                        response = st.session_state.chat_session.send_message(error_msg)
                        raw_text = response.text
                    else:
                        break # Auditoría aprobada

                # 3. MOSTRAR RESULTADO FINAL (Aprobado o el mejor esfuerzo tras reintentos)
                final_display = parse_and_render_response(raw_text)
                placeholder.markdown(final_display)
                st.session_state.messages.append({"role": "assistant", "content": raw_text})

            except Exception as e:
                # Recovey básico si todo falla
                st.error("Reiniciando conexión...")
                del st.session_state["chat_session"]
                st.rerun()

st.markdown("<br><hr><p style='text-align: center; color: #555;'>© 2025 Kiwigeek Perú - Hardware for Professionals</p>", unsafe_allow_html=True)
