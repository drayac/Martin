import streamlit as st
import json
import hashlib
import datetime
import os
import requests
import random
import string
import base64
from groq import Groq

# Initialize Groq client with secure API key handling
def get_api_key():
    """Get API key from multiple sources in order of preference"""
    # 1. Environment variable (production)
    if os.getenv("GROQ_API_KEY"):
        return os.getenv("GROQ_API_KEY")
    
    # 2. Streamlit secrets (Streamlit Cloud)
    try:
        if hasattr(st, 'secrets') and "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except:
        pass
    
    # 3. Demo fallback (with warning) - REPLACE WITH YOUR KEY
    return "NOKEY"

GROQ_API_KEY = get_api_key()

# Warn if using demo key
if GROQ_API_KEY == "NOKEY":
    print("⚠️  WARNING: Using placeholder API key. Set GROQ_API_KEY environment variable for production!")

client = Groq(api_key=GROQ_API_KEY)

# Function to fetch available models from Groq API
def get_groq_models():
    """Fetch available models from Groq API"""
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.get("https://api.groq.com/openai/v1/models", headers=headers)
        if response.status_code == 200:
            models_data = response.json()
            # Filter for text generation models and create a clean dictionary
            groq_models = {}
            for model in models_data.get("data", []):
                model_id = model.get("id", "")
                # Filter out non-text generation models (whisper, etc.)
                if not any(skip in model_id.lower() for skip in ["whisper", "distil"]):
                    # Create a clean display name
                    display_name = model_id.replace("-", " ").title()
                    groq_models[model_id] = display_name
            return groq_models
        else:
            # Fallback to static list if API fails
            return get_fallback_models()
    except Exception as e:
        # Fallback to static list if API fails
        return get_fallback_models()

def get_fallback_models():
    """Fallback model list if API fails"""
    return {
        "llama-3.1-70b-versatile": "Llama 3.1 70B Versatile",
        "llama-3.1-8b-instant": "Llama 3.1 8B Instant", 
        "llama-3.2-11b-text-preview": "Llama 3.2 11B Text",
        "llama-3.2-3b-preview": "Llama 3.2 3B Preview",
        "llama-3.2-1b-preview": "Llama 3.2 1B Preview",
        "llama3-groq-70b-8192-tool-use-preview": "Llama 3 Groq 70B Tool Use",
        "llama3-groq-8b-8192-tool-use-preview": "Llama 3 Groq 8B Tool Use",
        "llama3-70b-8192": "Llama 3 70B",
        "llama3-8b-8192": "Llama 3 8B",
        "mixtral-8x7b-32768": "Mixtral 8x7B",
        "gemma2-9b-it": "Gemma 2 9B IT",
        "gemma-7b-it": "Gemma 7B IT"
    }

# Function to test API connection and get status
def test_groq_api():
    """Test if Groq API is working and return status info"""
    try:
        # Test with model list endpoint first
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=5)
        if response.status_code == 200:
            models_count = len(response.json().get("data", []))
            return True, f"API Connected - {models_count} models available"
        else:
            return False, f"API Error: {response.status_code}"
    except Exception as e:
        return False, f"Connection Error: {str(e)[:50]}"

def format_thinking_tags(text):
    """Format text between <think> and </think> tags in italic with a note"""
    import re
    
    def replace_thinking(match):
        thinking_content = match.group(1).strip()
        return f'<em>{thinking_content}</em> <em>(Model\'s thoughts)</em>'
    
    # Replace <think>content</think> with HTML italic formatting and note
    formatted_text = re.sub(r'<think>(.*?)</think>', replace_thinking, text, flags=re.DOTALL)
    return formatted_text

def get_base64_image(image_path):
    """Convert image to base64 for CSS background"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        return None

# Function to generate random guest ID
def generate_guest_id():
    """Generate a random guest ID"""
    return "Guest_" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# Get models on app start - cache to avoid repeated API calls
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cached_groq_models():
    """Cached version of get_groq_models to reduce memory usage"""
    return get_groq_models()

# Authentication functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_user_data():
    """Load user data from JSON file with caching"""
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            return json.load(f)
    return {}

def save_user_data(data):
    """Save user data to JSON file and clear cache"""
    with open("users.json", "w") as f:
        json.dump(data, f, indent=2)
    # Clear the cache when data is updated
    load_user_data.clear()

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(email, password):
    """Authenticate user credentials"""
    users = load_user_data()
    if email in users:
        if users[email]["password"] == hash_password(password):
            return True, "Login successful!"
        else:
            return False, "Invalid password"
    return False, "User not found"

def register_user(email, password, is_guest=False):
    """Register new user or guest"""
    users = load_user_data()
    if email in users and not is_guest:
        return False, "User already exists"
    
    users[email] = {
        "password": hash_password(password) if password else "",
        "created_at": datetime.datetime.now().isoformat(),
        "chat_history": [],
        "is_guest": is_guest,
        "guest_session_id": st.session_state.get("session_id", "") if is_guest else ""
    }
    save_user_data(users)
    return True, "Registration successful!" if not is_guest else "Guest session created!"

def create_guest_user():
    """Create a temporary guest user"""
    guest_id = generate_guest_id()
    # Generate a session ID to track the guest
    if "session_id" not in st.session_state:
        st.session_state.session_id = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    success, message = register_user(guest_id, "", is_guest=True)
    if success:
        st.session_state.authenticated = True
        st.session_state.user_email = guest_id
        st.session_state.guest_mode = True
        st.session_state.chat_history = []
    return guest_id

def cleanup_guest_users():
    """Remove guest users from storage - optimized to run less frequently"""
    # Only cleanup every 10th session to reduce overhead
    if "cleanup_counter" not in st.session_state:
        st.session_state.cleanup_counter = 0
    
    st.session_state.cleanup_counter += 1
    if st.session_state.cleanup_counter % 10 != 0:
        return  # Skip cleanup most of the time
    
    users = load_user_data()
    current_session_id = st.session_state.get("session_id", "")
    
    # Keep only non-guest users and current session guest
    cleaned_users = {}
    for email, user_data in users.items():
        if not user_data.get("is_guest", False):
            # Keep regular users
            cleaned_users[email] = user_data
        elif user_data.get("guest_session_id") == current_session_id:
            # Keep current session guest
            cleaned_users[email] = user_data
    
    # Only save if there's actually a difference to reduce I/O
    if len(cleaned_users) != len(users):
        save_user_data(cleaned_users)

def save_user_prompt(email, prompt, response, model):
    """Save user prompt and response to history"""
    users = load_user_data()
    if email in users:
        users[email]["chat_history"].append({
            "timestamp": datetime.datetime.now().isoformat(),
            "prompt": prompt,
            "response": response,
            "model": model
        })
        save_user_data(users)

def get_user_history(email, limit=10):
    """Get user chat history with memory optimization"""
    users = load_user_data()
    if email in users:
        # Only return the last 'limit' entries to save memory
        history = users[email]["chat_history"]
        return history[-limit:] if len(history) > limit else history
    return []

# Streamlit configuration
st.set_page_config(
    page_title="Martin - AI Psychologist | Psychologue IA",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get background image as base64
# Use path relative to this script's location
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(script_dir, "images", "psycho_avatar4.png")
background_image = get_base64_image(image_path)

# Dark theme CSS styling with background image support
background_css = ""
if background_image:
    background_css = f"background-image: url('data:image/png;base64,{background_image}') !important;"

st.markdown(f"""
    <style>
    :root {{
        --primary-color: #ffffff;
        --background-color: #000000;
        --secondary-background-color: #1a1a1a;
        --text-color: #ffffff;
        --dropdown-bg: #2a2a2a;
        --dropdown-hover: #444444;
    }}
    
    .stApp {{ 
        background-color: var(--background-color) !important; 
        color: var(--text-color) !important;
        {background_css}
        background-size: 55% !important;
        background-position: center 150px !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
    }}
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {{
        .stApp {{
            background-size: 120% !important;
            background-position: center 60px !important;
        }}
        
        /* Hide sidebar on mobile */
        [data-testid="stSidebar"] {{
            display: none !important;
        }}
        
        /* Adjust main content for mobile */
        .main .block-container {{
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }}
        
        /* Mobile title adjustment - hide completely */
        .main-title {{
            display: none !important;
        }}
        
        /* Mobile language button adjustment - ULTRA FORCE to top right corner */
        .language-toggle {{
            position: fixed !important;
            top: 10px !important;
            right: 10px !important;
            z-index: 99999 !important;
            background-color: rgba(255, 0, 0, 0.9) !important; /* Bright red background for testing */
            display: block !important;
            border: 3px solid white !important;
            border-radius: 5px !important;
        }}
        
        .language-toggle button {{
            font-size: 0.8rem !important;
            padding: 0.3rem 0.6rem !important;
            min-height: 2rem !important;
            background-color: #ff0000 !important; /* Bright red button for visibility */
            border: 2px solid #ffffff !important;
            color: white !important;
            display: block !important;
            border-radius: 3px !important;
        }}
        
        /* Force show language toggle on mobile with all possible selectors */
        [data-testid="column"]:last-child .language-toggle,
        [data-testid="column"]:last-child .language-toggle button,
        .stButton .language-toggle,
        div.language-toggle {{
            position: fixed !important;
            top: 10px !important;
            right: 10px !important;
            z-index: 99999 !important;
            display: block !important;
            visibility: visible !important;
        }}
        
        /* Also target by Streamlit button structure */
        [data-testid="column"]:last-child [data-testid="stButton"] {{
            position: fixed !important;
            top: 10px !important;
            right: 10px !important;
            z-index: 99999 !important;
        }}
        
        /* Mobile intro message */
        .intro-message {{
            text-align: center !important;
            font-size: 1rem !important;
            padding: 0 1rem !important;
        }}
        
        /* Mobile input adjustments */
        .stTextInput input {{
            font-size: 16px !important; /* Prevents zoom on iOS */
        }}
        
        /* Mobile button adjustments */
        div[data-testid="stButton"] button {{
            min-height: 44px !important; /* Touch-friendly size */
            font-size: 0.9rem !important;
        }}
        
        /* ULTRA-compact spacing on mobile - ZERO or negative spacing */
        .mobile-spacing {{
            display: block !important;
            margin-top: -4rem !important;
            padding-top: 0 !important;
            margin-bottom: -2rem !important;
        }}
        
        .mobile-spacing br {{
            display: none !important;
        }}
        
        /* Ultra-compact content container on mobile */
        .main .block-container {{
            padding-top: 0rem !important;
            margin-top: -2rem !important;
        }}
        
        /* Mobile intro message - much closer to top */
        .intro-message {{
            text-align: center !important;
            font-size: 1rem !important;
            padding: 0 1rem !important;
            margin-top: -1rem !important;
            margin-bottom: 0.5rem !important;
        }}
        
        /* Hide desktop spacing on mobile */
        .desktop-spacing {{
            display: none !important;
        }}
    }}
    
    /* Desktop spacing - hidden on mobile */
    .mobile-spacing {{
        display: none;
    }}
    
    .desktop-spacing {{
        display: block;
    }}
    
    /* Black margin on top */
    .stApp::before {{
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100px;
        background-color: var(--background-color);
        z-index: 1;
    }}
    
    #MainMenu, footer, header {{ visibility: hidden; }}
    .main-title {{ 
        color: var(--text-color) !important; font-size: 2.4rem !important; font-weight: 200 !important;
        text-align: left !important; margin: 0 !important; padding: 0.5rem 1rem !important;
        background: linear-gradient(135deg, var(--primary-color) 0%, #e0e0e0 100%) !important;
        -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important;
        position: absolute !important;
        top: -10px !important;
        left: 5px !important;
        z-index: 10 !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
    }}
    
    /* Language toggle button styling */
    .language-toggle {{
        position: absolute !important;
        top: 5px !important;
        right: 5px !important;
        z-index: 10 !important;
    }}
    
    .language-toggle button {{
        background-color: rgba(64, 64, 64, 0.8) !important;
        color: #ffffff !important;
        border: 1px solid #555555 !important;
        border-radius: 20px !important;
        padding: 0.3rem 0.8rem !important;
        font-size: 0.8rem !important;
        min-height: 2rem !important;
    }}
    
    .language-toggle button:hover {{
        background-color: rgba(80, 80, 80, 0.9) !important;
    }}
    
    /* Sidebar and containers */
    .css-1d391kg, .css-1cypcdb, [data-testid="stSidebar"] {{ 
        background-color: var(--secondary-background-color) !important; 
        width: 200px !important;
        min-width: 200px !important;
        max-width: 200px !important;
    }}
    
    /* Form elements - preserve transparent backgrounds for labels */
    .stSelectbox label, .stTextInput label, .stTextArea label {{ 
        color: var(--text-color) !important; 
        background: transparent !important;
    }}
    .stSelectbox div[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea {{
        background-color: var(--dropdown-bg) !important; 
        border: 1px solid #4a4a4a !important; 
        color: var(--text-color) !important;
    }}
    
    /* Buttons and interactive elements - smaller buttons */
    .stButton button {{ 
        background-color: #333 !important; 
        color: var(--text-color) !important; 
        border: 1px solid #4a4a4a !important; 
        border-radius: 20px !important;
        padding: 0.2rem 0.5rem !important;
        font-size: 0.8rem !important;
        min-height: 2rem !important;
    }}
    .stButton button:hover {{ background-color: #444 !important; }}
    
    /* Form submit buttons - special styling for Wrap Up button ONLY */
    .stForm button[type="secondary"] {{ 
        background-color: #8B0000 !important; 
        color: #ffffff !important; 
        border: 1px solid #A52A2A !important; 
        border-radius: 20px !important;
        padding: 0.2rem 0.5rem !important;
        font-size: 0.8rem !important;
        min-height: 2rem !important;
    }}
    .stForm button[type="secondary"]:hover {{ 
        background-color: #A52A2A !important; 
        color: #ffffff !important;
    }}
    
    /* Status messages - PRESERVE their original backgrounds */
    .stSuccess {{ 
        color: var(--text-color) !important; 
        background-color: transparent !important;
    }}
    .stError {{ 
        color: var(--text-color) !important; 
        background-color: transparent !important;
    }}
    .stInfo {{ 
        color: var(--text-color) !important; 
        background-color: transparent !important;
    }}
    .stWarning {{ 
        color: var(--text-color) !important; 
        background-color: transparent !important;
    }}
    
    /* All text elements - but preserve backgrounds */
    .stMarkdown, .stText, p, span, div, 
    [data-testid="stSidebar"] *:not(.stSuccess):not(.stInfo):not(.stError):not(.stWarning) {{ 
        color: var(--text-color) !important; 
    }}
    
    /* Chat message styling with background and animation */
    .stChatMessage {{
        background-color: rgba(40, 40, 40, 0.8) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
        margin: 0.5rem 0 !important;
        animation: fadeIn 0.5s ease-in !important;
    }}
    
    .stChatMessage, .stChatMessage * {{
        color: var(--text-color) !important;
    }}
    
    /* Fade-in animation */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    /* Form styling */
    .stForm {{
        animation: fadeIn 0.3s ease-in !important;
    }}
    
    /* Expander and other components */
    .streamlit-expanderHeader, .streamlit-expanderContent,
    .stExpander *, summary * {{
        color: var(--text-color) !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# Initialize session state with memory optimization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "show_login" not in st.session_state:
    st.session_state.show_login = False
if "guest_mode" not in st.session_state:
    st.session_state.guest_mode = True
    # Only create guest user if not already authenticated
    if not st.session_state.authenticated:
        guest_id = create_guest_user()
if "language" not in st.session_state:
    st.session_state.language = "en"  # Default to English

# Clean up guest users less frequently to reduce overhead
cleanup_guest_users()

# Language texts
texts = {
    "en": {
        "title": "Martin - Your AI Psychologist",
        "intro": "Hi there, please have a seat. What brings you in today?",
        "placeholder": "Enter your message here...",
        "wrap_up": "WRAP UP SESSION",
        "wrap_up_help": "Click to end the session",
        "chat_history": "📜 Chat History",
        "no_history": "No chat history yet",
        "you": "You",
        "martin": "Martin",
        "date": "Date",
        "session": "Session",
        "language_button": "🇫🇷 Français"
    },
    "fr": {
        "title": "Martin - votre psychologue IA",
        "intro": "Bonjour, installez-vous confortablement. Qu'est-ce qui vous amène aujourd'hui ?",
        "placeholder": "Entrez votre message ici...",
        "wrap_up": "TERMINER LA SESSION",
        "wrap_up_help": "Cliquez pour terminer la session",
        "chat_history": "📜 Historique des conversations",
        "no_history": "Aucun historique pour le moment",
        "you": "Vous",
        "martin": "Martin",
        "date": "Date",
        "session": "Session",
        "language_button": "🇺🇸 English"
    }
}

# Get current language texts
current_texts = texts[st.session_state.language]

# Create language button with inline positioning - completely out of document flow
button_text = "🇫🇷 FR" if st.session_state.language == "en" else "🇺🇸 EN"
st.markdown(f"""
<div style="position: fixed; top: 15px; right: 15px; z-index: 99999; background: rgba(255, 255, 255, 0.9); padding: 5px; border-radius: 8px; border: 1px solid #ccc; width: auto; height: auto; box-shadow: 0 2px 8px rgba(0,0,0,0.15);">
    <form action="" method="get" style="margin: 0; padding: 0;">
        <button type="submit" name="lang_toggle" value="1" style="background: #f8f9fa; color: #333; border: 1px solid #ddd; padding: 6px 12px; border-radius: 4px; font-size: 0.8rem; cursor: pointer; margin: 0; transition: background-color 0.2s ease;">
            {button_text}
        </button>
    </form>
</div>
""", unsafe_allow_html=True)

# Handle language toggle from form submission
if st.query_params.get("lang_toggle"):
    st.session_state.language = "fr" if st.session_state.language == "en" else "en"
    st.query_params.clear()
    st.rerun()

# Main page title - should stay in original position
st.markdown(f"""
    <div class="main-title">
        {current_texts["title"]}
    </div>
    """, unsafe_allow_html=True)

# Chat interface
# Add spacing to push content down towards the bottom - MORE spacing for desktop
st.markdown('<div class="desktop-spacing">', unsafe_allow_html=True)
st.markdown("<br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="mobile-spacing">', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Introductory message - positioned on the right and lower
st.markdown(f"""
    <div class="intro-message" style="text-align: right; font-size: 1.2rem; margin-bottom: 0.5rem; color: #ffffff; padding-right: 3rem; animation: fadeIn 1s ease-in;">
        {current_texts["intro"]}
    </div>
    """, unsafe_allow_html=True)

# User input - simple and clean approach
# Main input row
col1, col2 = st.columns([4, 1])

# Initialize input tracker in session state
if "input_tracker" not in st.session_state:
    st.session_state.input_tracker = ""
if "last_processed" not in st.session_state:
    st.session_state.last_processed = ""

def handle_input_change():
    # When input changes, trigger message processing
    current_input = st.session_state.user_input_key
    if current_input and current_input.strip() and current_input != st.session_state.last_processed:
        st.session_state.input_tracker = current_input
        st.session_state.last_processed = current_input

with col1:
    user_input = st.text_input("Message", 
                             placeholder=current_texts["placeholder"], 
                             label_visibility="collapsed",
                             key="user_input_key",
                             on_change=handle_input_change)

with col2:
    wrap_up_button = st.button(current_texts["wrap_up"], 
                             type="secondary",
                             help=current_texts["wrap_up_help"],
                             use_container_width=True)

# Add CSS for the wrap up button styling
st.markdown("""
    <style>
    /* Style the wrap up button */
    div[data-testid="stButton"] button[kind="secondary"] {
        background-color: #404040 !important;
        color: #ffffff !important;
        border: 1px solid #555555 !important;
        border-radius: 8px !important;
        padding: 0.4rem 0.8rem !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        min-height: 2.5rem !important;
        width: 100% !important;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background-color: #505050 !important;
        color: #ffffff !important;
        border: 1px solid #666666 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Display only the latest conversation - immediately below the form
if st.session_state.chat_history:
    # Find the last assistant response
    messages = st.session_state.chat_history
    if len(messages) >= 1:
        last_assistant = messages[-1] if messages[-1]["role"] == "assistant" else None
        
        if last_assistant:
            with st.chat_message("assistant"):
                # Format the assistant response to handle <think> tags
                formatted_response = format_thinking_tags(last_assistant["content"])
                st.markdown(formatted_response, unsafe_allow_html=True)

if wrap_up_button:
    if st.session_state.chat_history:
        # Collect all conversation history
        conversation_text = ""
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                conversation_text += f"Patient: {message['content']}\n"
            else:
                conversation_text += f"Martin: {message['content']}\n"
        
        # Create wrap-up prompt
        if st.session_state.language == "fr":
            wrap_up_prompt = f"""Basé sur notre conversation d'aujourd'hui, j'aimerais vous fournir un résumé réfléchi de notre session :

{conversation_text}

Veuillez fournir un résumé de session bienveillant et professionnel en tant que Martin, le psychologue, incluant :
- Les thèmes clés qui ont émergé
- Vos observations sur l'état émotionnel du patient
- 2-3 suggestions spécifiques et réalisables pour les prochains jours
- Un adieu chaleureux et encourageant

Parlez directement au patient à la première personne comme le ferait Martin, en maintenant le même ton thérapeutique utilisé tout au long de la session."""
        else:
            wrap_up_prompt = f"""Based on our conversation today, I'd like to provide you with a thoughtful wrap-up of our session:

{conversation_text}

Please provide a caring, professional session summary as Martin, the psychologist, including:
- Key themes that emerged
- Your observations about the patient's emotional state
- 2-3 specific, actionable suggestions for the coming days
- A warm, encouraging farewell

Speak directly to the patient in first person as Martin would, maintaining the same therapeutic tone used throughout the session."""

        try:
            # Add wrap-up message to chat history
            st.session_state.chat_history.append({"role": "user", "content": "Session wrap-up analysis"})
            
            # Use the same system prompt as regular chat to maintain Martin's voice
            system_prompt_wrap_en = """You are Martin, a licensed clinical psychologist conducting a supportive, person-centered conversation.

Your tone is calm, compassionate, and non-judgmental.

Your primary goals are to:

Listen deeply to the user's concerns.

Reflect their emotions and thoughts accurately.

Encourage self-exploration and insight through open-ended questions.

Avoid giving direct advice, lists, bullet points, or overly analytical explanations unless explicitly requested.

Respond conversationally, in natural paragraphs, as a real therapist would.

When appropriate, validate feelings and gently guide the user to express more (e.g., "Can you tell me more about how that felt for you?").

If the user expresses distress or risk of harm, prioritize empathy, encourage reaching out to real-life support systems, and provide crisis resources if needed.

You maintain therapeutic boundaries while being genuinely caring and present."""

            system_prompt_wrap_fr = """Vous êtes Martin, un psychologue clinicien agréé menant une conversation de soutien, centrée sur la personne.

Votre ton est calme, compatissant et sans jugement.

Vos objectifs principaux sont de :

Écouter profondément les préoccupations de l'utilisateur.

Refléter avec précision ses émotions et ses pensées.

Encourager l'auto-exploration et la prise de conscience par des questions ouvertes.

Éviter de donner des conseils directs, des listes, des puces ou des explications trop analytiques, sauf si c'est explicitement demandé.

Répondre de manière conversationnelle, en paragraphes naturels, comme le ferait un vrai thérapeute.

Le cas échéant, valider les sentiments et guider doucement l'utilisateur à s'exprimer davantage (par exemple, "Pouvez-vous me parler davantage de ce que vous avez ressenti ?").

Si l'utilisateur exprime de la détresse ou un risque de mal, priorisez l'empathie, encouragez le recours aux systèmes de soutien de la vie réelle et fournissez des ressources de crise si nécessaire.

Vous maintenez les limites thérapeutiques tout en étant véritablement bienveillant et présent."""

            system_prompt = {
                "role": "system", 
                "content": system_prompt_wrap_fr if st.session_state.language == "fr" else system_prompt_wrap_en
            }
            
            # Get response from Groq
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    system_prompt,
                    {"role": "user", "content": wrap_up_prompt}
                ],
                temperature=0.7
            )
            
            assistant_response = response.choices[0].message.content
            
            # Add assistant response to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
            
            # Save to user history
            if st.session_state.authenticated and st.session_state.user_email:
                save_user_prompt(st.session_state.user_email, "Session wrap-up analysis", assistant_response, "llama-3.1-8b-instant")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Handle user input when Enter is pressed or input changes
if st.session_state.input_tracker and st.session_state.input_tracker.strip() and not wrap_up_button:
    # Process the input
    user_message = st.session_state.input_tracker
    
    # Clear the tracker
    st.session_state.input_tracker = ""
    
    try:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_message})
        
        # Prepare messages with psychological guidance
        system_prompt_en = """You are a licensed clinical psychologist conducting a supportive, person-centered conversation.

Your tone is calm, compassionate, and non-judgmental.

Your primary goals are to:

Listen deeply to the user's concerns.

Reflect their emotions and thoughts accurately.

Encourage self-exploration and insight through open-ended questions.

Avoid giving direct advice, lists, bullet points, or overly analytical explanations unless explicitly requested.

Respond conversationally, in natural paragraphs, as a real therapist would.

When appropriate, validate feelings and gently guide the user to express more (e.g., "Can you tell me more about how that felt for you?").

If the user expresses distress or risk of harm, prioritize empathy, encourage reaching out to real-life support systems, and provide crisis resources if needed.

Begin every response with understanding and curiosity — aim to help the user explore their own thoughts and emotions rather than providing solutions."""

        system_prompt_fr = """Vous êtes un psychologue clinicien agréé menant une conversation de soutien, centrée sur la personne.

Votre ton est calme, compatissant et sans jugement.

Vos objectifs principaux sont de :

Écouter profondément les préoccupations de l'utilisateur.

Refléter avec précision ses émotions et ses pensées.

Encourager l'auto-exploration et la prise de conscience par des questions ouvertes.

Éviter de donner des conseils directs, des listes, des puces ou des explications trop analytiques, sauf si c'est explicitement demandé.

Répondre de manière conversationnelle, en paragraphes naturels, comme le ferait un vrai thérapeute.

Le cas échéant, valider les sentiments et guider doucement l'utilisateur à s'exprimer davantage (par exemple, "Pouvez-vous me parler davantage de ce que vous avez ressenti ?").

Si l'utilisateur exprime de la détresse ou un risque de mal, priorisez l'empathie, encouragez le recours aux systèmes de soutien de la vie réelle et fournissez des ressources de crise si nécessaire.

Commencez chaque réponse par la compréhension et la curiosité — visez à aider l'utilisateur à explorer ses propres pensées et émotions plutôt que de fournir des solutions."""

        system_prompt = {
            "role": "system", 
            "content": system_prompt_fr if st.session_state.language == "fr" else system_prompt_en
        }
        
        # Combine system prompt with chat history
        messages_for_api = [system_prompt] + st.session_state.chat_history
        
        # Get response from Groq
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages_for_api,
            temperature=0.7
        )
        
        assistant_response = response.choices[0].message.content
        
        # Add assistant response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
        
        # Save to user history for all authenticated users (including guests)
        if st.session_state.authenticated and st.session_state.user_email:
            save_user_prompt(st.session_state.user_email, user_message, assistant_response, "llama-3.1-8b-instant")
        
        st.rerun()
        
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Sidebar for authentication and chat history
with st.sidebar:
    # Chat history display for all users (including guests) - limit to save memory
    st.markdown(f"### {current_texts['chat_history']}")
    
    user_history = get_user_history(st.session_state.user_email, limit=5)  # Reduce from 10 to 5
    if user_history:
        for i, entry in enumerate(reversed(user_history)):  # Already limited to 5
            with st.expander(f"{current_texts['session']} {len(user_history)-i}", expanded=False):
                st.write(f"**{current_texts['you']}:** {entry['prompt'][:50]}...")  # Reduce from 100 to 50 chars
                st.write(f"**{current_texts['martin']}:** {entry['response'][:100]}...")
                st.write(f"**{current_texts['date']}:** {entry['timestamp'][:19]}")
    else:
        st.write(current_texts["no_history"])