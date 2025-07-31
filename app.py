import streamlit as st
from PIL import Image
import time
import sys
import traceback
import importlib

# ================= Page Configuration =================
st.set_page_config(
    page_title="DevOps + AI Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= Module Loading System =================
def safe_import_module(module_name, module_path):
    """Safely import a module and return the module object"""
    try:
        module = importlib.import_module(module_path)
        return module
    except Exception as e:
        st.sidebar.error(f"⚠️ Failed to load {module_name}: {str(e)}")
        return None

# Define module mappings
MODULE_MAPPINGS = {
    "awsautomate": "modules.awsautomate",
    "dockermenu": "modules.dockermenu", 
    "GENAI": "modules.GENAI",
    "github_automation": "modules.github_automation",
    "iac": "modules.iac",
    "kubernetesmenue": "modules.kubernetesmenue",
    "linux": "modules.linux",
    "ml_dashboard": "modules.ml_dashboard",
    "ml_regress": "modules.ml_regress",
    "promptengineeing": "modules.promptengineeing",
    "pythonmenu": "modules.pythonmenu",
    "testingagent": "modules.testingagent"
}

# Load all modules
loaded_modules = {}
for module_name, module_path in MODULE_MAPPINGS.items():
    module = safe_import_module(module_name, module_path)
    if module:
        loaded_modules[module_name] = module

# ================= Custom CSS =================
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #1f4e79;
        --secondary-color: #2e86de;
        --accent-color: #00d2d3;
        --background-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --card-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    }
    
    /* Main content area */
    .main-content {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
        padding: 2rem;
    }
    
    /* Enhanced sidebar profile card */
    .profile-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        text-align: center;
    }
    
    .profile-image {
        border-radius: 50%;
        border: 3px solid rgba(255, 255, 255, 0.3);
        margin-bottom: 1rem;
    }
    
    /* Menu styling */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Hero section */
    .hero-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: var(--card-shadow);
    }
    
    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .hero-subtitle {
        font-size: 1.3rem;
        margin-bottom: 1.5rem;
        opacity: 0.9;
    }
    
    .hero-description {
        font-size: 1.1rem;
        max-width: 800px;
        margin: 0 auto 2rem;
        line-height: 1.6;
    }
    
    /* Feature cards grid */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .feature-card {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: var(--card-shadow);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }
    
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    
    .feature-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: var(--primary-color);
    }
    
    .feature-description {
        color: #666;
        line-height: 1.5;
    }
    
    /* Statistics cards */
    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: var(--card-shadow);
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Animated elements */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .animate-fade-in {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .status-online {
        background: rgba(46, 204, 113, 0.1);
        color: #27ae60;
        border: 1px solid rgba(46, 204, 113, 0.3);
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: currentColor;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# ================= Enhanced Sidebar =================
with st.sidebar:
    st.markdown("""
    <div class="profile-card">
        <img src="https://github.com/Dubeysatvik123/Images/blob/main/Satvik.jpg?raw=true" 
             class="profile-image" width="150" alt="Profile">
        <h3 style="color: white; margin: 0.5rem 0;">Satvik Dubey</h3>
        <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0;">Team No: 73</p>
        <div class="status-indicator status-online">
            <div class="status-dot"></div>
            System Online
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Enhanced menu with better categorization
    st.markdown("### 🎯 Navigation")
    menu = st.selectbox("Select a Module", [
        "🏠 Home",
        "🤖 AI & Machine Learning",
        "📊 ML Dashboard",
        "📈 ML Regression",
        "🛠️ DevOps & Infrastructure",
        "🐳 Docker Automation",
        "☸️ Kubernetes Automation",
        "🔁 AIOps",
        "🧱 Infrastructure as Code",
        "☁️ AWS Automation",
        "💻 Development Tools",
        "🐧 Linux Tools",
        "🐍 Python MultiTool",
        "🤖 GenAI",
        "🧑‍💻 Agentic AI",
        "✍️ Prompt Engineering",
        "🌐 Blog Automation"
    ])
    
    # Add module status in sidebar
    st.markdown("---")
    st.markdown("### 📈 Module Status")
    loaded_count = sum(1 for module in loaded_modules.values() if module is not None)
    total_count = len(loaded_modules)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Loaded", loaded_count, f"/{total_count}")
    with col2:
        percentage = (loaded_count / total_count) * 100 if total_count > 0 else 0
        st.metric("Success", f"{percentage:.0f}%")

# Enhanced Loading Animation
def show_loading():
    with st.spinner("Loading module..."):
        time.sleep(0.5)  # Brief loading animation

# ================= Enhanced Home Page =================
def show_home():
    st.markdown("""
    <div class="hero-container animate-fade-in">
        <div class="hero-title">🚀 Unified DevOps + AI Dashboard</div>
        <div class="hero-subtitle">Welcome to the Ultimate Productivity Suite</div>
        <div class="hero-description">
            A comprehensive platform that integrates Machine Learning, DevOps automation, 
            and AI tools in one seamless interface. Streamline your workflow from development 
            to deployment with cutting-edge technologies.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Statistics overview
    st.markdown("""
    <div class="stats-container">
        <div class="stat-card">
            <div class="stat-number">15+</div>
            <div class="stat-label">Integrated Modules</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">100%</div>
            <div class="stat-label">Python Powered</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">24/7</div>
            <div class="stat-label">Availability</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">∞</div>
            <div class="stat-label">Possibilities</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature highlights
    st.markdown("## ✨ Key Features")
    
    features = [
        {
            "icon": "🧠",
            "title": "Machine Learning Suite",
            "description": "Advanced ML models including ANN, Linear Regression, and Classification algorithms with interactive dashboards."
        },
        {
            "icon": "🐳",
            "title": "Container Orchestration",
            "description": "Automated Docker and Kubernetes management with deployment pipelines and monitoring capabilities."
        },
        {
            "icon": "☁️",
            "title": "Cloud Integration",
            "description": "Seamless AWS automation with Infrastructure as Code (IaC) for scalable cloud deployments."
        },
        {
            "icon": "🤖",
            "title": "AI-Powered Tools",
            "description": "GenAI capabilities, Agentic AI systems, and advanced prompt engineering for intelligent automation."
        },
        {
            "icon": "💻",
            "title": "Development Toolkit",
            "description": "Comprehensive Python tools, Linux utilities, and automated testing frameworks for developers."
        },
        {
            "icon": "📊",
            "title": "Real-time Analytics",
            "description": "Live dashboards and monitoring systems with AIOps integration for proactive issue resolution."
        }
    ]
    
    # Create feature cards grid
    cols = st.columns(2)
    for i, feature in enumerate(features):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="feature-card">
                <div class="feature-icon">{feature['icon']}</div>
                <div class="feature-title">{feature['title']}</div>
                <div class="feature-description">{feature['description']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Getting started section
    st.markdown("---")
    st.markdown("## 🚀 Getting Started")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("**Step 1:** Choose a module from the sidebar navigation menu")
    
    with col2:
        st.info("**Step 2:** Explore the interactive tools and features available")
    
    with col3:
        st.info("**Step 3:** Leverage the integrated capabilities for your projects")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #666;">
        <p>🌟 Built with ❤️ by <strong>Satvik Dubey</strong> (Team 73)</p>
        <p><em>"Empowering innovation through integrated technology solutions"</em></p>
    </div>
    """, unsafe_allow_html=True)

# ================= Enhanced Routing with Loading =================
def show_loading():
    with st.spinner("Loading module..."):
        time.sleep(0.5)  # Brief loading animation

def run_module_safely(module_name):
    """Safely run a module with error handling"""
    if module_name in loaded_modules:
        try:
            module = loaded_modules[module_name]
            if hasattr(module, 'run'):
                module.run()
            else:
                st.error(f"Module {module_name} does not have a 'run' function")
        except Exception as e:
            st.error(f"Error running {module_name}: {str(e)}")
            st.code(traceback.format_exc())
    else:
        st.error(f"Module {module_name} not found or failed to load")

# Route handling with categories
if menu == "🏠 Home":
    show_home()
elif menu == "🤖 AI & Machine Learning":
    st.title("🤖 AI & Machine Learning Hub")
    st.info("Select a specific ML module from the sidebar to continue.")
    ml_modules = [
        {"name": "📊 ML Dashboard", "desc": "Interactive machine learning dashboard with visualizations"},
        {"name": "📈 ML Regression", "desc": "Advanced regression analysis with data visualization"}
    ]
    for module in ml_modules:
        st.markdown(f"**{module['name']}**: {module['desc']}")
elif menu == "📊 ML Dashboard":
    show_loading()
    run_module_safely("ml_dashboard")
elif menu == "📈 ML Regression":
    show_loading()
    run_module_safely("ml_regress")
elif menu == "🛠️ DevOps & Infrastructure":
    st.title("🛠️ DevOps & Infrastructure Hub")
    st.info("Select a specific DevOps tool from the sidebar to continue.")
elif menu == "🐳 Docker Automation":
    show_loading()
    run_module_safely("dockermenu")
elif menu == "☸️ Kubernetes Automation":
    show_loading()
    run_module_safely("kubernetesmenue")
elif menu == "🔁 AIOps":
    show_loading()
    run_module_safely("testingagent")
elif menu == "🧱 Infrastructure as Code":
    show_loading()
    run_module_safely("iac")
elif menu == "☁️ AWS Automation":
    show_loading()
    run_module_safely("awsautomate")
elif menu == "💻 Development Tools":
    st.title("💻 Development Tools Hub")
    st.info("Select a specific development tool from the sidebar to continue.")
elif menu == "🐧 Linux Tools":
    show_loading()
    run_module_safely("linux")
elif menu == "🐍 Python MultiTool":
    show_loading()
    run_module_safely("pythonmenu")
elif menu == "🤖 GenAI":
    show_loading()
    run_module_safely("GENAI")
elif menu == "🧑‍💻 Agentic AI":
    show_loading()
    run_module_safely("testingagent")
elif menu == "✍️ Prompt Engineering":
    show_loading()
    run_module_safely("promptengineeing")
elif menu == "🌐 Blog Automation":
    show_loading()
    run_module_safely("github_automation")
