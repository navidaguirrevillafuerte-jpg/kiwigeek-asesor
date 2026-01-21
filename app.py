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
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CONSTANTES DE MARCA ---
COLORS = {
    "kiwi_green": "#00FF41",
    "kiwi_blue": "#0066FF",
    "bg_dark": "#1a1a1a",
    "bg_card": "#2d2d2d",
    "text_white": "#ffffff",
    "border_gray": "#444"
}
AVATAR_URL = "https://kiwigeekperu.com/wp-content/uploads/2026/01/gatitow.webp"
WHATSAPP_LINK = "https://api.whatsapp.com/send/?phone=51939081940&text=Hola%2C+me+gustar%C3%ADa+saber+m%C3%A1s+de+sus+productos&type=phone_number&app_absent=0"

# --- ORDEN LÓGICO DE COMPONENTES (TABLA BOLETA) ---
COMPONENT_PRIORITY = {
    "PROCESADOR": 1, "CPU": 1,
    "PLACA MADRE": 2, "MOTHERBOARD": 2, "PLACA": 2,
    "MEMORIA RAM": 3, "RAM": 3, "MEMORIA": 3,
    "TARJETA DE VIDEO": 4, "GPU": 4, "VIDEO": 4,
    "ALMACENAMIENTO": 5, "SSD": 5, "DISCO": 5, "M.2": 5,
    "FUENTE DE PODER": 6, "PSU": 6, "FUENTE": 6,
    "CASE": 7, "GABINETE": 7, "CHASIS": 7,
    "REFRIGERACIÓN": 8, "COOLER": 8, "LIQUIDA": 8,
    "MONITOR": 9, "PANTALLA": 9,
    "TECLADO": 10, "MOUSE": 11, "AUDIFONOS": 12,
    "OTROS": 99
}

# --- LISTA DE AVATARES RANDOM PARA USUARIO ---
USER_AVATARS = [
    "🧑‍💻", "👨‍💻", "👩‍💻", "🦸", "🦹", "🧙", "🧚", "🧛", "🧜", "🧝", 
    "🧞", "🧟", "💆", "💇", "🚶", "🏃", "💃", "🕺", "🕴", "👯", 
    "🧖", "🧗", "🤺", "🏇", "⛷", "🏂", "🏌️", "🏄", "🚣", "🏊", 
    "⛹️", "🏋️", "🚴", "🚵", "🤸", "🤼", "🤽", "🤾", "🤹", "🧘", 
    "🛀", "🛌", "🧑", "🧒", "👦", "👧", "🧑‍🦱", "👨‍🦱", "👩‍🦱", "🧑‍🦰",
    "😎", "🤓", "🤠", "🥳", "👽", "🤖", "👮", "🕵️", "💂", "👷"
]

# --- CSS MEJORADO (TABLAS HTML) ---
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
        
        /* Estilo BOLETA HTML */
        .boleta-container {{
            background-color: #262626;
            border: 1px solid {COLORS['border_gray']};
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}
        .boleta-header {{
            background-color: {COLORS['kiwi_green']};
            color: #000;
            padding: 10px 15px;
            font-weight: 800;
            font-size: 1.1rem;
            border-bottom: 2px solid #000;
        }}
        .boleta-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95rem;
        }}
        .boleta-table th {{
            background-color: #333;
            color: #ccc;
            text-transform: uppercase;
            font-size: 0.8rem;
            padding: 8px 15px;
            text-align: left;
            border-bottom: 1px solid #444;
        }}
        .boleta-table td {{
            padding: 10px 15px;
            border-bottom: 1px solid #333;
            color: #fff;
            vertical-align: middle;
        }}
        .boleta-table tr:last-child td {{
            border-bottom: none;
        }}
        .boleta-total {{
            background-color: #1a1a1a;
            color: {COLORS['kiwi_green']};
            padding: 15px;
            text-align: right;
            font-size: 1.2rem;
            font-weight: bold;
            border-top: 1px solid #444;
        }}
        .component-cat {{
            color: #aaa;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            display: block;
            margin-bottom: 2px;
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
        
        /* Ocultar elementos de Streamlit */
        footer {{visibility: hidden;}}
        [data-testid="stSidebarCollapsedControl"] {{display: none !important;}}
        .stDeployButton {{display: none !important;}}
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

# --- FUNCIONES DE PARSEO Y ORDENAMIENTO (PYTHON AL MANDO) ---
def extract_json_from_text(text):
    """Extrae el bloque JSON crudo del texto de forma robusta."""
    try:
        # Intento 1: Bloque de código json
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # Intento 2: Buscar llaves { } extremas
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = text[start_idx : end_idx + 1]
            return json.loads(json_str)
    except:
        return None
    return None

def get_sort_priority(component):
    """Devuelve un número de prioridad basado en la categoría para ordenar."""
    cat = component.get('category', '').upper().strip()
    # Búsqueda parcial para ser más flexible (ej: "MEMORIA RAM" coincide con "RAM")
    for key, priority in COMPONENT_PRIORITY.items():
        if key in cat:
            return priority
    return 99 

def generate_html_boleta(option_data):
    """Genera una tabla HTML bonita tipo boleta."""
    title = option_data.get('title', 'Opción')
    strategy = option_data.get('strategy', '')
    components = option_data.get('components', [])
    
    # Ordenar componentes
    components_sorted = sorted(components, key=get_sort_priority)
    
    # Iniciar HTML
    html = f"""
    <div class="boleta-container">
        <div class="boleta-header">{title}<br><span style="font-size:0.8rem; font-weight:400; color:#333;">{strategy}</span></div>
        <table class="boleta-table">
            <thead>
                <tr>
                    <th width="20%">Categoría</th>
                    <th width="60%">Producto</th>
                    <th width="20%" style="text-align:right;">Precio</th>
                </tr>
            </thead>
            <tbody>
    """
    
    total_real = 0.0
    for item in components_sorted:
        try:
            price = float(item.get('price', 0))
            total_real += price
            name = item.get('name', 'Producto')
            url = item.get('url', '#')
            cat = item.get('category', 'Componente').upper()
            highlight = item.get('highlight', '')
            
            highlight_html = f'<br><span style="color:#00FF41; font-size:0.8rem;">💡 {highlight}</span>' if highlight else ''
            
            html += f"""
            <tr>
                <td><span class="component-cat">{cat}</span></td>
                <td><a href="{url}" target="_blank" style="color:#fff; text-decoration:none; font-weight:bold;">{name}</a>{highlight_html}</td>
                <td style="text-align:right;">S/ {price:,.2f}</td>
            </tr>
            """
        except: continue

    html += f"""
            </tbody>
        </table>
        <div class="boleta-total">
            TOTAL: S/ {total_real:,.2f}
        </div>
    </div>
    """
    return html

def parse_and_render_response(text):
    """
    Renderiza la respuesta usando HTML puro si es una cotización.
    """
    data = extract_json_from_text(text)
    
    if data and isinstance(data, dict):
        # Si es mensaje simple
        if not data.get("is_quote"):
            return data.get("message", text)

        # Si es cotización
        try:
            intro = data.get('intro', '')
            options = data.get('options', [])
            outro = data.get('outro', '')
            
            # Construir salida final
            final_html = f"<div style='margin-bottom:15px;'>{intro}</div>"
            
            for opt in options:
                final_html += generate_html_boleta(opt)
            
            final_html += f"<div style='margin-top:15px;'>{outro}</div>"
            
            # Botón de WhatsApp
            wa_button = f"""
            <div style="text-align:center; margin-top:20px;">
                <a href="{WHATSAPP_LINK}" target="_blank" style="
                    background-color: #25D366;
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 25px;
                    font-weight: bold;
                    display: inline-block;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                ">
                📲 SOLICITAR DESCUENTO EXCLUSIVO EN WHATSAPP
                </a>
            </div>
            """
            
            return final_html + wa_button
            
        except Exception as e:
            print(f"Error renderizando HTML: {e}")
            return text 
            
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
# Usamos temperatura 0.0 para máxima precisión matemática y de formato
MODEL_ID = 'models/gemini-2.0-flash'

@st.cache_resource
def setup_kiwi_brain():
    """Inicializa con SISTEMA V23: FORMATO ESTRICTO Y COMPLETITUD"""
    try:
        path = 'catalogo_kiwigeek.json'
        if not os.path.exists(path): return None, "Error: Archivo no encontrado."
        with open(path, 'r', encoding='utf-8') as f: catalog_data = f.read()

        system_instruction = (
            "ROL: Kiwigeek AI. Tu ÚNICA función es generar JSON válido.\n"
            "CONTEXTO: Tienes un inventario de hardware. Usa LINKS reales.\n\n"
            "--- FASE 1: FILTRO DE ALCANCE ---\n"
            "Si el usuario NO especifica 'Solo Torre' o 'PC Completa', responde ESTO y NADA MÁS:\n"
            "```json\n"
            "{ \"is_quote\": false, \"message\": \"Hola 👋 Para darte el mejor precio, ¿buscas solo la torre (CPU) o la PC completa con monitor y periféricos?\" }\n"
            "```\n\n"
            "--- FASE 2: GENERACIÓN DE COTIZACIÓN ---\n"
            "Si tienes el alcance, genera 3 opciones (A, B, C) en este formato JSON EXACTO:\n"
            "```json\n"
            "{\n"
            '  "is_quote": true,\n'
            '  "detected_budget": 0,\n'
            '  "intro": "Texto de introducción...",\n'
            '  "options": [\n'
            '    {\n'
            '      "title": "Opción A - Económica", "strategy": "...",\n'
            '      "components": [\n'
            '         {"category": "PROCESADOR", "name": "...", "price": 0, "url": "..."},\n'
            '         {"category": "PLACA MADRE", "name": "...", "price": 0, "url": "..."},\n'
            '         {"category": "MEMORIA RAM", "name": "...", "price": 0, "url": "..."},\n'
            '         {"category": "ALMACENAMIENTO", "name": "...", "price": 0, "url": "..."},\n'
            '         {"category": "TARJETA DE VIDEO", "name": "...", "price": 0, "url": "..."},\n'
            '         {"category": "FUENTE DE PODER", "name": "...", "price": 0, "url": "..."},\n'
            '         {"category": "CASE", "name": "...", "price": 0, "url": "..."}\n'
            '      ]\n'
            '    }\n'
            '    // ... Opción B y C ...\n'
            '  ],\n'
            '  "outro": "Texto final..."\n'
            "}\n"
            "```\n"
            "REGLAS CRÍTICAS:\n"
            "1. **PRESUPUESTO**: La suma de precios NO puede exceder el presupuesto del usuario +10%.\n"
            "2. **COMPLETITUD**: No olvides NINGÚN componente. Si falta uno, la PC no prende.\n"
            "3. **SOLO JSON**: No escribas 'Aquí tienes...' fuera del bloque JSON.\n"
        )

        try:
            cache = client.caches.create(
                model=MODEL_ID,
                config=types.CreateCachedContentConfig(
                    display_name='kiwigeek_v23_strict_boleta',
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
    
    # TEMPERATURA 0.0 PARA PRECISIÓN MÁXIMA
    config = types.GenerateContentConfig(temperature=0.0, top_p=0.8, max_output_tokens=8192)
    
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

# Renderizado Historial (Soporta HTML seguro)
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message(msg["role"], avatar=AVATAR_URL):
            st.markdown(parse_and_render_response(msg["content"]), unsafe_allow_html=True)
    else:
        with st.chat_message(msg["role"], avatar=msg.get("avatar", USER_AVATARS[0])):
            st.markdown(msg["content"])

# INPUT Y LÓGICA PRINCIPAL CON AUDITORÍA
if prompt := st.chat_input("Ej: Tengo S/ 4000..."):
    current_avatar = random.choice(USER_AVATARS)
    st.session_state.messages.append({"role": "user", "content": prompt, "avatar": current_avatar})
    
    with st.chat_message("user", avatar=current_avatar):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=AVATAR_URL):
        placeholder = st.empty()
        with st.spinner("🔍 Diseñando configuración a medida..."):
            try:
                if "chat_session" not in st.session_state: raise Exception("Sesión perdida")
                
                # 1. GENERACIÓN
                response = st.session_state.chat_session.send_message(prompt)
                raw_text = response.text
                
                # 2. AUDITORÍA (LOOP DE CORRECCIÓN)
                max_retries = 2
                attempt = 0
                while attempt < max_retries:
                    data = extract_json_from_text(raw_text)
                    
                    # Si no es JSON válido o es charla simple, salir
                    if not data or not isinstance(data, dict):
                        # Si parece intento de cotización fallido
                        if "Opción" in raw_text:
                            attempt += 1
                            error_msg = "ERROR: Respond in VALID JSON ONLY. No text."
                            response = st.session_state.chat_session.send_message(error_msg)
                            raw_text = response.text
                            continue
                        else:
                            break # Charla normal
                    
                    if not data.get("is_quote"): break # Es pregunta de aclaración
                    
                    budget = float(data.get("detected_budget", 0))
                    if budget == 0: break 
                    
                    feedback = []
                    needs_fix = False
                    for opt in data.get('options', []):
                        # Sumar componentes
                        total_real = sum(float(c.get('price', 0)) for c in opt.get('components', []))
                        # Margen estricto 10%
                        limit = budget * 1.10 
                        if total_real > limit:
                            needs_fix = True
                            feedback.append(f"• Option '{opt.get('title')}' is S/ {total_real:.2f} (Max allowed: S/ {limit:.2f}).")
                    
                    if needs_fix:
                        attempt += 1
                        error_msg = f"AUDIT FAILED: Budget S/ {budget}. Too expensive:\n" + "\n".join(feedback) + "\nREGENERATE JSON CHEAPER."
                        response = st.session_state.chat_session.send_message(error_msg)
                        raw_text = response.text
                    else:
                        break # Todo correcto

                # 3. MOSTRAR RESULTADO
                final_html = parse_and_render_response(raw_text)
                placeholder.markdown(final_html, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": raw_text})

            except Exception as e:
                st.error("Conexión inestable. Reiniciando...")
                if "chat_session" in st.session_state: del st.session_state["chat_session"]
                st.rerun()

st.markdown("<br><hr><p style='text-align: center; color: #555;'>© 2025 Kiwigeek Perú - Hardware for Professionals</p>", unsafe_allow_html=True)
