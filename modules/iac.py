import streamlit as st
import os
import zipfile
import tempfile
import shutil
from pathlib import Path
import google.generativeai as genai
from datetime import datetime
import json

def run():
    # Custom CSS for better styling
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            color: white;
            text-align: center;
        }
        
        .provider-card {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            margin: 1rem 0;
        }
        
        .success-box {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .error-box {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏗️ Infrastructure as Code Generator</h1>
        <p>Powered by Google Gemini Flash API</p>
    </div>
    """, unsafe_allow_html=True)

    class TerraformGenerator:
        def __init__(self, api_key):
            self.api_key = api_key
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        def generate_terraform_code(self, provider, app_requirements, credentials):
            """Generate Terraform code using Gemini Flash"""
            prompt = f"""
            Generate complete Terraform infrastructure code for the following requirements:
            
            Cloud Provider: {provider}
            Application Requirements: {app_requirements}
            
            Please generate the following files:
            1. main.tf - Main infrastructure resources
            2. variables.tf - Variable definitions
            3. outputs.tf - Output values
            4. terraform.tfvars.example - Example variables file
            5. providers.tf - Provider configuration
            6. versions.tf - Terraform and provider version constraints
            
            Requirements:
            - Follow Terraform best practices
            - Use appropriate resource naming conventions
            - Include proper tags and labels
            - Add comments for clarity
            - Use variables for configurable values
            - Include security best practices
            - Make it production-ready
            
            For {provider}, consider these common resources based on the application type:
            - Compute instances/containers
            - Networking (VPC, subnets, security groups)
            - Storage solutions
            - Load balancers
            - Databases if needed
            - IAM roles and policies
            - Monitoring and logging
            
            Return the response in JSON format with each file as a separate key:
            {{
                "main.tf": "content here",
                "variables.tf": "content here",
                "outputs.tf": "content here",
                "terraform.tfvars.example": "content here",
                "providers.tf": "content here",
                "versions.tf": "content here",
                "README.md": "deployment instructions and overview"
            }}
            """
            
            try:
                response = self.model.generate_content(prompt)
                # Try to extract JSON from the response
                response_text = response.text
                
                # Find JSON content in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_content = response_text[start_idx:end_idx]
                    return json.loads(json_content)
                else:
                    # If JSON parsing fails, create a structured response
                    return {
                        "main.tf": response_text,
                        "variables.tf": "# Variables will be defined here",
                        "outputs.tf": "# Outputs will be defined here",
                        "terraform.tfvars.example": "# Example variables",
                        "providers.tf": f"# Provider configuration for {provider}",
                        "versions.tf": "# Version constraints",
                        "README.md": f"# {provider} Infrastructure\n\nGenerated Terraform code for your application."
                    }
            except Exception as e:
                st.error(f"Error generating Terraform code: {str(e)}")
                return None

    def create_project_structure(files_content, project_name, provider):
        """Create project directory structure and files"""
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir) / f"{project_name}_{provider.lower()}_terraform"
        project_path.mkdir(exist_ok=True)
        
        # Create files
        for filename, content in files_content.items():
            file_path = project_path / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return str(project_path)

    def create_zip_file(project_path):
        """Create a zip file of the project"""
        zip_path = f"{project_path}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_path)
                    zipf.write(file_path, arcname)
        return zip_path

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Gemini API Key
        api_key = st.text_input(
            "Google Gemini API Key",
            type="password",
            help="Enter your Google Gemini API key to generate Terraform code"
        )
        
        if not api_key:
            st.warning("Please enter your Gemini API key to continue")
            st.markdown("""
            **How to get Gemini API Key:**
            1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
            2. Create a new API key
            3. Copy and paste it here
            """)
            return
        
        st.success("✅ API Key configured!")
        
        # Provider Selection
        st.header("☁️ Cloud Provider")
        provider = st.selectbox(
            "Select Cloud Provider",
            ["AWS", "Azure", "Google Cloud (GCP)", "DigitalOcean", "Linode", "Vultr"]
        )
        
        # Project Configuration
        st.header("📁 Project Settings")
        project_name = st.text_input(
            "Project Name",
            value="my-infrastructure",
            help="Name for your infrastructure project"
        )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🔧 Application Requirements")
        
        # Application type
        app_type = st.selectbox(
            "Application Type",
            [
                "Web Application (Frontend + Backend)",
                "API Service",
                "Microservices Architecture",
                "Static Website",
                "Container-based Application",
                "Database Application",
                "Machine Learning Pipeline",
                "Data Processing Pipeline",
                "Custom Requirements"
            ]
        )
        
        # Detailed requirements
        app_requirements = st.text_area(
            "Detailed Requirements",
            placeholder="""Describe your infrastructure requirements:
- Number of servers needed
- Expected traffic load
- Database requirements
- Storage needs
- Security requirements
- Compliance needs
- Backup requirements
- Monitoring needs
- Any specific services needed""",
            height=200
        )
        
        # Additional configuration based on provider
        st.subheader(f"🔑 {provider} Configuration")
        
        with st.expander("Credential Configuration", expanded=False):
            if provider == "AWS":
                access_key = st.text_input("AWS Access Key ID", type="password")
                secret_key = st.text_input("AWS Secret Access Key", type="password")
                region = st.selectbox("AWS Region", [
                    "us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"
                ])
            elif provider == "Azure":
                subscription_id = st.text_input("Azure Subscription ID", type="password")
                client_id = st.text_input("Azure Client ID", type="password")
                client_secret = st.text_input("Azure Client Secret", type="password")
                tenant_id = st.text_input("Azure Tenant ID", type="password")
            elif provider == "Google Cloud (GCP)":
                project_id = st.text_input("GCP Project ID")
                credentials_file = st.file_uploader("Service Account JSON", type="json")
                region = st.selectbox("GCP Region", [
                    "us-central1", "us-east1", "europe-west1", "asia-southeast1"
                ])
            else:
                api_token = st.text_input(f"{provider} API Token", type="password")
                region = st.text_input(f"{provider} Region", value="nyc1")
        
        # Generate button
        if st.button("🚀 Generate Terraform Code", type="primary"):
            if not app_requirements.strip():
                st.error("Please provide application requirements")
                return
            
            with st.spinner("Generating Terraform code with Gemini Flash..."):
                # Initialize generator
                generator = TerraformGenerator(api_key)
                
                # Prepare credentials dict
                credentials = {
                    "provider": provider,
                    "project_name": project_name,
                    "app_type": app_type
                }
                
                # Generate Terraform code
                files_content = generator.generate_terraform_code(
                    provider, 
                    f"Application Type: {app_type}\n\nRequirements:\n{app_requirements}",
                    credentials
                )
                
                if files_content:
                    st.success("✅ Terraform code generated successfully!")
                    
                    # Store in session state for download
                    st.session_state.generated_files = files_content
                    st.session_state.project_name = project_name
                    st.session_state.provider = provider
                    
                    # Display generated files
                    st.subheader("📄 Generated Files")
                    
                    for filename, content in files_content.items():
                        with st.expander(f"📄 {filename}"):
                            st.code(content, language='hcl' if filename.endswith('.tf') else 'text')
    
    with col2:
        st.header("📥 Download & Deploy")
        
        if 'generated_files' in st.session_state:
            # Create project structure
            project_path = create_project_structure(
                st.session_state.generated_files,
                st.session_state.project_name,
                st.session_state.provider
            )
            
            # Create zip file
            zip_path = create_zip_file(project_path)
            
            # Download button
            with open(zip_path, 'rb') as f:
                st.download_button(
                    label="📦 Download Terraform Project",
                    data=f.read(),
                    file_name=f"{st.session_state.project_name}_{st.session_state.provider.lower()}_terraform.zip",
                    mime="application/zip"
                )
            
            # Deployment instructions
            st.subheader("🚀 Deployment Instructions")
            st.markdown(f"""
            **Steps to deploy your {st.session_state.provider} infrastructure:**
            
            1. **Extract the zip file** to your local machine
            2. **Navigate to the project directory**
            3. **Configure your credentials** in the terraform.tfvars file
            4. **Initialize Terraform:**
               ```bash
               terraform init
               ```
            5. **Plan the deployment:**
               ```bash
               terraform plan
               ```
            6. **Apply the infrastructure:**
               ```bash
               terraform apply
               ```
            7. **Destroy when needed:**
               ```bash
               terraform destroy
               ```
            """)
        else:
            st.info("Generate Terraform code to see download options")
        
        # Provider information
        st.subheader("ℹ️ Provider Information")
        provider_info = {
            "AWS": {
                "icon": "🟧",
                "description": "Amazon Web Services - Comprehensive cloud platform",
                "docs": "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"
            },
            "Azure": {
                "icon": "🔵", 
                "description": "Microsoft Azure - Enterprise cloud solutions",
                "docs": "https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs"
            },
            "Google Cloud (GCP)": {
                "icon": "🔴",
                "description": "Google Cloud Platform - Data and AI focused",
                "docs": "https://registry.terraform.io/providers/hashicorp/google/latest/docs"
            },
            "DigitalOcean": {
                "icon": "🔷",
                "description": "Simple cloud computing for developers",
                "docs": "https://registry.terraform.io/providers/digitalocean/digitalocean/latest/docs"
            },
            "Linode": {
                "icon": "🟢",
                "description": "Developer-friendly cloud hosting",
                "docs": "https://registry.terraform.io/providers/linode/linode/latest/docs"
            },
            "Vultr": {
                "icon": "🟣",
                "description": "High-performance cloud compute",
                "docs": "https://registry.terraform.io/providers/vultr/vultr/latest/docs"
            }
        }
        
        if provider in provider_info:
            info = provider_info[provider]
            st.markdown(f"""
            <div class="provider-card">
                <h4>{info['icon']} {provider}</h4>
                <p>{info['description']}</p>
                <a href="{info['docs']}" target="_blank">📚 View Documentation</a>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    run()