import google.generativeai as genai
import streamlit as st
import time

# Configure Gemini API
genai.configure(api_key="AIzaSyAAdwMJ2cO-Cqp76d8J_beTwYNE2EahyXI")
model = genai.GenerativeModel("gemini-1.5-flash")

def run():
    # Note: Page config is handled by the main app
    # st.set_page_config(
    #     page_title="🚀 Manthan The AI - Startup Evaluator",
    #     page_icon="🚀",
    #     layout="wide",
    #     initial_sidebar_state="expanded"
    # )

    # Custom CSS for enhanced styling
    st.markdown("""
    <style>
        /* Main header styling */
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        
        .main-header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .main-header p {
            font-size: 1.2rem;
            margin: 0;
            opacity: 0.9;
        }
        
        /* Section headers */
        .section-header {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 10px;
            border-left: 5px solid #667eea;
            margin: 1.5rem 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .section-header h3 {
            margin: 0;
            color: #2c3e50;
        }
        
        /* Example buttons styling */
        .example-container {
            background: #e3f2fd;
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            border: 1px solid #bbdefb;
        }
        
        .example-item {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            border-left: 4px solid #2196f3;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        
        .example-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        /* Tips box */
        .tips-box {
            background: #fff3cd;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 5px solid #ffc107;
            margin: 1rem 0;
        }
        
        .tips-box h4 {
            color: #856404;
            margin-bottom: 1rem;
        }
        
        .tips-box ul {
            color: #856404;
        }
        
        /* Progress styling */
        .progress-text {
            text-align: center;
            font-weight: bold;
            color: #667eea;
            margin: 1rem 0;
        }
        
        /* Results container */
        .results-container {
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-top: 1rem;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            margin-top: 3rem;
            padding: 2rem;
            color: #666;
            border-top: 1px solid #eee;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        /* Status indicators */
        .status-success {
            background: #d4edda;
            color: #155724;
            padding: 0.75rem;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }
        
        .status-error {
            background: #f8d7da;
            color: #721c24;
            padding: 0.75rem;
            border-radius: 8px;
            border-left: 4px solid #dc3545;
        }
    </style>
    """, unsafe_allow_html=True)

    # Main header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 Manthan The AI</h1>
        <p>Get expert analysis of your startup idea across 5 key pillars</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'evaluation_result' not in st.session_state:
        st.session_state.evaluation_result = ""
    if 'is_evaluating' not in st.session_state:
        st.session_state.is_evaluating = False

    # Example ideas
    examples = [
        "An AI-powered personal finance app that automatically categorizes expenses and provides investment recommendations based on spending patterns",
        "A platform connecting local farmers directly with restaurants, reducing food waste and supporting sustainable agriculture",
        "A VR-based remote collaboration tool specifically designed for creative teams working on 3D projects",
        "An app that uses machine learning to optimize home energy consumption by learning user behavior patterns"
    ]

    # Layout: Two columns
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown('<div class="section-header"><h3>💡 Your Startup Idea</h3></div>', unsafe_allow_html=True)
        
        # Idea input
        idea_input = st.text_area(
            label="Describe your startup idea",
            placeholder="e.g., An AI-powered app that helps people find the perfect pet based on their lifestyle, living situation, and preferences...",
            height=200,
            key="idea_input",
            help="Be as detailed as possible for better evaluation results"
        )
        
        # Action buttons
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            evaluate_btn = st.button(
                "🔍 Evaluate Idea", 
                type="primary", 
                use_container_width=True,
                disabled=st.session_state.is_evaluating
            )
        
        with col_btn2:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.idea_input = ""
                st.session_state.evaluation_result = ""
                st.rerun()
        
        # Examples section
        st.markdown('<div class="section-header"><h3>💭 Need inspiration? Try these examples:</h3></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="example-container">', unsafe_allow_html=True)
        for i, example in enumerate(examples):
            if st.button(
                f"💡 Example {i+1}",
                key=f"example_{i}",
                help=example,
                use_container_width=True
            ):
                st.session_state.idea_input = example
                st.rerun()
            
            # Show truncated example text
            st.markdown(f'<div class="example-item"><small>{example[:100]}...</small></div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-header"><h3>📊 Evaluation Results</h3></div>', unsafe_allow_html=True)
        
        # Results container
        results_container = st.container()
        
        with results_container:
            if evaluate_btn and idea_input.strip():
                st.session_state.is_evaluating = True
                st.session_state.evaluation_result = evaluate_startup_idea(idea_input.strip())
                st.session_state.is_evaluating = False
                st.rerun()
            
            elif evaluate_btn and not idea_input.strip():
                st.markdown('<div class="status-error">⚠️ Please enter your startup idea to get an evaluation.</div>', unsafe_allow_html=True)
            
            # Display results
            if st.session_state.evaluation_result:
                st.markdown('<div class="results-container">', unsafe_allow_html=True)
                st.markdown(st.session_state.evaluation_result)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Download button for results
                st.download_button(
                    label="📄 Download Analysis",
                    data=st.session_state.evaluation_result,
                    file_name="startup_evaluation.txt",
                    mime="text/plain"
                )
            
            else:
                # Placeholder content
                st.markdown("""
                <div class="results-container">
                    <h4>Your detailed startup evaluation will appear here...</h4>
                    <p>✨ <strong>The analysis will cover:</strong></p>
                    <ul>
                        <li>🔧 <strong>Feasibility</strong> & Technical Requirements</li>
                        <li>📈 <strong>Market Potential</strong> & Competition Analysis</li>
                        <li>🏗️ <strong>Build Strategy</strong> & Development Plan</li>
                        <li>💰 <strong>Cost Estimates</strong> & Team Structure</li>
                        <li>⚠️ <strong>Risks</strong> & Improvement Suggestions</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
        
        # Tips section
        st.markdown("""
        <div class="tips-box">
            <h4>💡 Tips for better results:</h4>
            <ul>
                <li>Be specific about your target audience</li>
                <li>Mention any unique features or technology</li>
                <li>Include your business model if you have one in mind</li>
                <li>Describe the problem you're solving clearly</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Sidebar with additional info
    with st.sidebar:
        st.markdown("### 📊 Evaluation Metrics")
        
        # Show evaluation criteria
        criteria = [
            {"name": "Feasibility", "icon": "🔧", "desc": "Technical doability"},
            {"name": "Market Potential", "icon": "📈", "desc": "Business viability"},
            {"name": "Build Strategy", "icon": "🏗️", "desc": "Development plan"},
            {"name": "Cost & Team", "icon": "💰", "desc": "Resource planning"},
            {"name": "Risks & Improvements", "icon": "⚠️", "desc": "Risk assessment"}
        ]
        
        for criterion in criteria:
            st.markdown(f"""
            **{criterion['icon']} {criterion['name']}**  
            {criterion['desc']}
            """)
        
        st.markdown("---")
        
        # Statistics
        st.markdown("### 📈 Session Stats")
        if 'evaluation_count' not in st.session_state:
            st.session_state.evaluation_count = 0
        
        st.metric("Evaluations", st.session_state.evaluation_count)
        
        # API status
        st.markdown("### 🔌 API Status")
        st.success("🟢 Gemini AI Connected")
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.info("This tool uses Google's Gemini 1.5 Flash model to provide comprehensive startup evaluations based on industry best practices.")

    # Footer
    st.markdown("""
    <div class="footer">
        <p>🤖 <strong>Powered by Google's Gemini AI | Built with Streamlit</strong></p>
        <p style="font-size: 0.9em;">Get comprehensive startup evaluations in seconds</p>
        <p style="font-size: 0.8em; margin-top: 1rem;">
            Built by Satvik Dubey | Team 73
        </p>
    </div>
    """, unsafe_allow_html=True)

def evaluate_startup_idea(prompt):
    """Evaluate startup idea with progress tracking"""
    if not prompt.strip():
        return "Please enter your startup idea to get an evaluation."
    
    # Progress indicator
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    try:
        # Progress updates
        progress_placeholder.progress(0.1)
        status_placeholder.markdown('<div class="progress-text">🔄 Initializing evaluation...</div>', unsafe_allow_html=True)
        time.sleep(0.5)
        
        system_prompt = """You are a seasoned project architect and startup strategist. For the idea I provide, give a brief, structured evaluation across these 5 pillars:

1. **Feasibility** 🔧
   - Is it technically doable today?
   - Do similar products exist? If yes, what's the clear differentiator (USP)?

2. **Market Potential** 📈
   - Does it solve a real, current/growing problem?
   - Quick view: target users, market size, key competitors, monetization model.

3. **Build Strategy** 🏗️
   - MVP → Beta → Scale: short 3-stage plan.
   - Ideal tech stack, architecture (e.g. monolith/microservices), and methodology (Agile, Lean).

4. **Cost & Team** 💰
   - Ballpark cost (dev, infra, tools), ideal team setup.
   - Cost-saving tips: OSS, no-code/low-code, outsourcing, phased rollouts.

5. **Improvements & Risks** ⚠️
   - UX/features to boost value.
   - Key risks (tech, market, legal), and how to reduce them.

Format your response with clear headers, bullet points, and actionable insights. Use emojis to make it visually appealing."""

        progress_placeholder.progress(0.3)
        status_placeholder.markdown('<div class="progress-text">🤖 Connecting to AI model...</div>', unsafe_allow_html=True)
        time.sleep(0.5)
        
        convo = model.start_chat(history=[
            {"role": "user", "parts": [system_prompt]}
        ])
        
        progress_placeholder.progress(0.6)
        status_placeholder.markdown('<div class="progress-text">🧠 Analyzing your startup idea...</div>', unsafe_allow_html=True)
        time.sleep(0.5)
        
        response = convo.send_message(prompt)
        
        progress_placeholder.progress(0.9)
        status_placeholder.markdown('<div class="progress-text">✨ Finalizing evaluation...</div>', unsafe_allow_html=True)
        time.sleep(0.5)
        
        progress_placeholder.progress(1.0)
        status_placeholder.markdown('<div class="status-success">✅ Evaluation complete!</div>', unsafe_allow_html=True)
        
        # Update session state
        if 'evaluation_count' not in st.session_state:
            st.session_state.evaluation_count = 0
        st.session_state.evaluation_count += 1
        
        # Clear progress indicators after a short delay
        time.sleep(1)
        progress_placeholder.empty()
        status_placeholder.empty()
        
        return response.text
        
    except Exception as e:
        progress_placeholder.empty()
        status_placeholder.markdown(f'<div class="status-error">❌ Error occurred: {str(e)}</div>', unsafe_allow_html=True)
        return f"❌ **Error occurred:** {str(e)}\n\nPlease try again or check your API configuration."

# Run the app
if __name__ == "__main__":
    run()