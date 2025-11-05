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
    page_title="Martin - your AI psychologist",
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
        color: var(--text-color) !important; font-size: 1.8rem !important; font-weight: 100 !important;
        text-align: left !important; margin: 0 !important; padding: 0.3rem 1rem !important;
        background: linear-gradient(135deg, var(--primary-color) 0%, #e0e0e0 100%) !important;
        -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important;
        position: absolute !important;
        top: 5px !important;
        left: 5px !important;
        z-index: 10 !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
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

# Clean up guest users less frequently to reduce overhead
cleanup_guest_users()

# Main page title - moved higher
st.markdown("""
    <div class="main-title">
        Martin - your AI psychologist
    </div>
    """, unsafe_allow_html=True)

# Chat interface
# Add spacing to push content down towards the bottom
st.markdown("<br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

# Introductory message - positioned on the right and lower
st.markdown("""
    <div style="text-align: right; font-size: 1.2rem; margin-bottom: 1rem; color: #ffffff; padding-right: 3rem; animation: fadeIn 1s ease-in;">
        Hi there, please have a seat. What brings you in today?
    </div>
    """, unsafe_allow_html=True)

# User input with form for Enter key support
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_area(
            "",
            height=80,
            placeholder="Type your message here... (Press Ctrl+Enter to send)",
            key="user_input_form"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
        send_button = st.form_submit_button("Send", type="primary")
    
    # Send and Clear buttons - smaller and on the side
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.write("")  # Empty space
    with col2:
        pass  # Send button is now next to the prompt
    with col3:
        pass

# Wrap-up session button between prompt and answer
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    wrap_up_button = st.button("Let's wrap up today's session", type="secondary")

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

# Clear button outside the form
col1, col2, col3 = st.columns([6, 1, 1])
with col3:
    clear_button = st.button("Clear")

if clear_button:
    st.session_state.chat_history = []
    st.rerun()

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
            system_prompt = {
                "role": "system", 
                "content": """You are Martin, a licensed clinical psychologist conducting a supportive, person-centered conversation.

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

if send_button:
    if user_input.strip():
        try:
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            # Prepare messages with psychological guidance
            system_prompt = {
                "role": "system", 
                "content": """You are a licensed clinical psychologist conducting a supportive, person-centered conversation.

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
                save_user_prompt(st.session_state.user_email, user_input, assistant_response, "llama-3.1-8b-instant")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Sidebar for authentication and chat history
with st.sidebar:
    # Chat history display for all users (including guests) - limit to save memory
    st.markdown("### 📜 Chat History")
    
    user_history = get_user_history(st.session_state.user_email, limit=5)  # Reduce from 10 to 5
    if user_history:
        for i, entry in enumerate(reversed(user_history)):  # Already limited to 5
            with st.expander(f"Session {len(user_history)-i}", expanded=False):
                st.write(f"**You:** {entry['prompt'][:50]}...")  # Reduce from 100 to 50 chars
                st.write(f"**Martin:** {entry['response'][:100]}...")
                st.write(f"**Date:** {entry['timestamp'][:19]}")
    else:
        st.write("No chat history yet")
