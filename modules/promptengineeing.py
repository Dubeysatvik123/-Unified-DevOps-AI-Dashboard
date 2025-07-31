import streamlit as st
import google.generativeai as genai
import time
import os
from typing import Dict, Any

def run():
    # Note: Page config is handled by the main app
    # st.set_page_config(
    #     page_title="IaC Prompting Assistant",
    #     page_icon="🏗️",
    #     layout="wide",
    #     initial_sidebar_state="expanded"
    # )

    # ============================================================================
    # 🔑 HARDCODED API KEY SECTION - PASTE YOUR GEMINI API KEY HERE
    # ============================================================================
    GEMINI_API_KEY = "AIzaSyCzyswaoYrJeMDbiwtcMcmthX79Dttyjqs"
    # 
    # Get your free API key from: https://makersuite.google.com/app/apikey
    # Replace "PASTE_YOUR_GEMINI_API_KEY_HERE" with your actual API key
    # ============================================================================

    # Gemini Configuration
    @st.cache_resource
    def configure_gemini():
        """Configure Gemini API with hardcoded API key"""
        try:
            # Use hardcoded API key
            api_key = GEMINI_API_KEY
            
            if not api_key or api_key == "PASTE_YOUR_GEMINI_API_KEY_HERE":
                st.error("⚠️ Please paste your Gemini API key in the GEMINI_API_KEY variable at the top of this script.")
                st.info("🔗 Get your free API key from: https://makersuite.google.com/app/apikey")
                st.stop()
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            st.success("✅ Gemini AI configured successfully!")
            return model
        except Exception as e:
            st.error(f"❌ Error configuring Gemini: {str(e)}")
            st.stop()

    # Initialize Gemini model
    gemini_model = configure_gemini()

    def generate_prompt_response(technique: str, user_prompt: str) -> str:
        """Generate responses using different prompting techniques with Gemini"""
        
        # Define prompting templates for each technique
        prompts = {
            "zero_shot": f"""
You are an expert Infrastructure as Code engineer. Generate a complete solution for the following request:

{user_prompt}

Provide:
1. A brief explanation of the solution
2. Complete, production-ready code
3. Deployment/usage instructions

Format your response with clear code blocks and explanations.
        """,
            
            "few_shot": f"""
You are an expert Infrastructure as Code engineer. Here are some examples of infrastructure solutions:

Example 1:
Request: "Create an S3 bucket with versioning in Terraform"
Solution:
```hcl
resource "aws_s3_bucket" "example" {{
  bucket = "my-example-bucket"
}}

resource "aws_s3_bucket_versioning" "example" {{
  bucket = aws_s3_bucket.example.id
  versioning_configuration {{
    status = "Enabled"
  }}
}}
```

Example 2:
Request: "Deploy nginx using Docker"
Solution:
```yaml
version: '3.8'
services:
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

Example 3:
Request: "Create RDS MySQL instance with Terraform"
Solution:
```hcl
resource "aws_db_instance" "mysql" {{
  identifier     = "my-mysql-db"
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = "db.t3.micro"
  allocated_storage = 20
  
  db_name  = "myapp"
  username = "admin"
  password = "changeme123"
  
  skip_final_snapshot = true
}}
```

Now solve this request following the same pattern:
{user_prompt}

Provide complete, production-ready infrastructure code with explanations.
        """,
            
            "chain_of_thought": f"""
You are an expert Infrastructure as Code engineer. Solve this step-by-step using chain-of-thought reasoning:

Request: {user_prompt}

Please think through this systematically:

Step 1: Analyze the requirements
- What infrastructure components are needed?
- Which cloud provider or tool is most suitable?
- What are the dependencies and relationships?

Step 2: Design the architecture
- How should the components be structured?
- What security considerations apply?
- What are the networking requirements?

Step 3: Choose the implementation approach
- Which IaC tool is best for this use case?
- What modules or resources are needed?
- How should configuration be managed?

Step 4: Implementation
- Provide the complete code solution
- Include all necessary configurations
- Add deployment instructions

Think through each step explicitly before providing your final solution.
        """,
            
            "react": f"""
You are an expert Infrastructure as Code engineer using ReAct methodology. Solve this infrastructure request by thinking through each step:

Request: {user_prompt}

Use this format:
Thought: [Your reasoning about what needs to be done]
Action: [What you'll implement or research]  
Observation: [What you learned or accomplished]

Continue this cycle until you have a complete solution. Then provide:
- Final infrastructure code
- Deployment instructions
- Best practices followed

Start with your first Thought about analyzing this request.
        """,
            
            "toolformer": f"""
You are an expert Infrastructure as Code engineer with access to multiple tools. Analyze this request and select the best approach:

Request: {user_prompt}

First, evaluate available tools:
- Terraform (multi-cloud, declarative)
- Ansible (configuration management, imperative)  
- CloudFormation (AWS native)
- Kubernetes YAML (container orchestration)
- Docker Compose (local development)
- Pulumi (programming language based)
- Bash scripts (simple automation)

Tool Selection Process:
1. Analyze requirements and identify best tool(s)
2. Explain why this tool is optimal for the use case
3. Consider integration with existing infrastructure
4. Account for team skills and preferences

Selected Tool: [Your choice]
Justification: [Why this tool is best]

Implementation:
[Provide complete solution using the selected tool]

Alternative approaches:
[Mention 1-2 alternative tools and brief reasoning]
        """
        }
        
        try:
            response = gemini_model.generate_content(prompts[technique])
            return response.text
        except Exception as e:
            return f"❌ Error generating response: {str(e)}\n\nPlease check your API key and internet connection."

    def display_response_with_formatting(response: str):
        """Display the Gemini response with proper formatting"""
        if "❌ Error" in response:
            st.error(response)
            return
        
        # Split response into sections for better formatting
        lines = response.split('\n')
        current_code_block = ""
        in_code_block = False
        code_language = "text"
        
        for line in lines:
            if line.strip().startswith('```'):
                if not in_code_block:
                    # Starting a code block
                    in_code_block = True
                    code_language = line.strip()[3:] or "text"
                    current_code_block = ""
                else:
                    # Ending a code block
                    in_code_block = False
                    if current_code_block.strip():
                        st.code(current_code_block.strip(), language=code_language)
                    current_code_block = ""
            elif in_code_block:
                current_code_block += line + "\n"
            else:
                if line.strip():
                    st.markdown(line)
                elif not in_code_block:
                    st.markdown("")  # Preserve spacing outside code blocks

    # Custom CSS for better styling
    st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    text-align: center;
    color: #1f77b4;
    margin-bottom: 2rem;
}
.technique-header {
    font-size: 1.5rem;
    font-weight: bold;
    color: #2e8b57;
    border-bottom: 2px solid #2e8b57;
    padding-bottom: 0.5rem;
    margin-top: 1rem;
}
.prompt-box {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
}
.response-container {
    border-left: 4px solid #1f77b4;
    padding-left: 1rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

    # Main header
    st.markdown('<h1 class="main-header">🏗️ IaC Prompting Assistant</h1>', unsafe_allow_html=True)

    # Sidebar with information
    with st.sidebar:
        st.header("📚 Prompting Techniques")
        st.markdown("""
        **1️⃣ Zero-Shot**
        - Direct response without examples
        - Quick and straightforward
        
        **2️⃣ Few-Shot**
        - Shows example prompts & outputs
        - Learns from patterns
        
        **3️⃣ Chain-of-Thought**
        - Step-by-step reasoning
        - Breaks down complex problems
        
        **4️⃣ ReAct**
        - Thought → Action → Observation
        - Iterative problem solving
        
        **5️⃣ Toolformer-Inspired**
        - Tool selection & justification
        - Best practice recommendations
        """)
        
        st.divider()
        
        st.header("🔑 API Configuration")
        if GEMINI_API_KEY == "PASTE_YOUR_GEMINI_API_KEY_HERE":
            st.error("⚠️ API Key Required")
            st.markdown("""
            **Steps to setup:**
            1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
            2. Replace `PASTE_YOUR_GEMINI_API_KEY_HERE` in the script
            3. Restart the application
            """)
        else:
            st.success("✅ API Key Configured")
            st.markdown(f"**Key Preview:** `{GEMINI_API_KEY[:8]}...{GEMINI_API_KEY[-4:]}`")
        
        st.header("🛠️ Supported Tools")
        st.markdown("""
        - **Terraform** (AWS, Azure, GCP)
        - **Ansible** Playbooks
        - **Docker** & Kubernetes
        - **CloudFormation** Templates
        - **Pulumi** Scripts
        - **Bash** Scripts
        """)

    # Main content area
    st.markdown("### 📝 Enter Your Infrastructure Prompt")

    # User input section
    user_prompt = st.text_area(
        label="Infrastructure Requirements",
        placeholder="Example: Provision an EC2 instance in AWS with Terraform and install Nginx",
        height=100,
        help="Describe the infrastructure you want to provision or configure"
    )

    # Display user prompt if entered
    if user_prompt:
        st.markdown('<div class="prompt-box">', unsafe_allow_html=True)
        st.markdown(f"**Your Prompt:** {user_prompt}")
        st.markdown('</div>', unsafe_allow_html=True)

    # Generate responses button
    if st.button("🚀 Generate IaC Solutions", type="primary", use_container_width=True):
        if not user_prompt.strip():
            st.error("Please enter an infrastructure prompt first!")
        else:
            # Create tabs for different techniques
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "1️⃣ Zero-Shot", 
                "2️⃣ Few-Shot", 
                "3️⃣ Chain-of-Thought", 
                "4️⃣ ReAct", 
                "5️⃣ Toolformer-Inspired"
            ])
            
            # Zero-Shot Tab
            with tab1:
                st.markdown('<h3 class="technique-header">Zero-Shot Prompting</h3>', unsafe_allow_html=True)
                st.markdown("**Approach:** Direct response without examples or detailed reasoning")
                
                with st.spinner("🤖 Generating Zero-Shot response with Gemini..."):
                    response = generate_prompt_response("zero_shot", user_prompt)
                
                st.markdown('<div class="response-container">', unsafe_allow_html=True)
                st.markdown("**Generated Solution:**")
                display_response_with_formatting(response)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Few-Shot Tab
            with tab2:
                st.markdown('<h3 class="technique-header">Few-Shot Prompting</h3>', unsafe_allow_html=True)
                st.markdown("**Approach:** Provide examples before solving the user's prompt")
                
                with st.spinner("🤖 Generating Few-Shot response with Gemini..."):
                    response = generate_prompt_response("few_shot", user_prompt)
                    
                st.markdown('<div class="response-container">', unsafe_allow_html=True)
                st.markdown("**Generated Solution Based on Examples:**")
                display_response_with_formatting(response)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Chain-of-Thought Tab  
            with tab3:
                st.markdown('<h3 class="technique-header">Chain-of-Thought Prompting</h3>', unsafe_allow_html=True)
                st.markdown("**Approach:** Step-by-step reasoning before generating the solution")
                
                with st.spinner("🤖 Generating Chain-of-Thought response with Gemini..."):
                    response = generate_prompt_response("chain_of_thought", user_prompt)
                    
                st.markdown('<div class="response-container">', unsafe_allow_html=True)
                st.markdown("**Step-by-Step Solution:**")
                display_response_with_formatting(response)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # ReAct Tab
            with tab4:
                st.markdown('<h3 class="technique-header">ReAct Prompting</h3>', unsafe_allow_html=True)
                st.markdown("**Approach:** Reasoning and Acting in iterative cycles (Thought → Action → Observation)")
                
                with st.spinner("🤖 Generating ReAct response with Gemini..."):
                    response = generate_prompt_response("react", user_prompt)
                    
                st.markdown('<div class="response-container">', unsafe_allow_html=True)
                st.markdown("**Iterative Problem-Solving Process:**")
                display_response_with_formatting(response)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Toolformer-Inspired Tab
            with tab5:
                st.markdown('<h3 class="technique-header">Toolformer-Inspired Prompting</h3>', unsafe_allow_html=True)
                st.markdown("**Approach:** Select the best IaC tool and justify the choice before implementation")
                
                with st.spinner("🤖 Generating Toolformer-Inspired response with Gemini..."):
                    response = generate_prompt_response("toolformer", user_prompt)
                    
                st.markdown('<div class="response-container">', unsafe_allow_html=True)
                st.markdown("**Tool Selection & Implementation:**")
                display_response_with_formatting(response)
                st.markdown('</div>', unsafe_allow_html=True)

    # Footer with usage instructions
    st.markdown("---")
    st.markdown("### 📋 Usage Instructions")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **🚀 Getting Started:**
        1. **Paste your Gemini API key** in the script (line 10)
        2. Enter your infrastructure prompt below
        3. Click "Generate IaC Solutions"
        4. Compare responses across different techniques
        """)

    with col2:
        st.markdown("""
        **💡 Tips for Better Results:**
        - Be specific about cloud provider (AWS, Azure, GCP)
        - Mention preferred tools (Terraform, Ansible, etc.)
        - Include requirements (security, scalability, etc.)
        - Specify environment (dev, staging, prod)
        """)

    st.markdown("---")
    st.markdown("**🔧 Built with Streamlit & Google Gemini AI** | *Compare prompting techniques for Infrastructure as Code generation*")
    st.markdown("**🔑 API Key:** Hardcoded in script for easy setup")

if __name__ == "__main__":
    run()
