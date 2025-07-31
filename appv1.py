import streamlit as st
import os
from pathlib import Path
import importlib.util
import sys

# Import modules dynamically from the /modules directory
module_dir = Path(__file__).parent / "modules"
sys.path.append(str(module_dir))

# Import specific modules
try:
    from DOX_Dockerautumation import docker_page
    from k8s_automation import kubernetes_page
    from awsautomate import aws_ec2_gesture_page, aws_provisioner_page
    from GENAI import genai_evaluator_page
    from promptengineeing import prompt_comparator_page
    from github_automation import github_pusher_page
    from pythonmenue import python_multitask_page
    from ml_dashboard import ml_dashboard_page
    from linux import linux_automation_page
except ImportError as e:
    st.error(f"Error importing module: {e}")
    st.stop()

# Configuration
st.set_page_config(
    page_title="Achyut Dubey's Multipurpose AI + DevOps Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar configuration
def setup_sidebar():
    st.sidebar.image("assets/profile.jpg", caption="Achyut Dubey", width=150)
    st.sidebar.markdown(f"**Name**: Achyut Dubey")
    st.sidebar.markdown(f"**Team**: Team 07")
    st.sidebar.markdown("---")
    
    # Page selection
    pages = [
        "Home",
        "Docker Automation",
        "Kubernetes Automation",
        "AWS EC2 Launcher (Gesture-Based)",
        "AWS Automation Provisioner",
        "GenAI-Based Project Evaluator (Manthan)",
        "Prompt Engineering Comparator",
        "GitHub Agentic Code Pusher",
        "Python Multi-Task Menu",
        "Machine Learning Dashboard",
        "AI Quiz Generator",
        "Microservice Architecture Visualizer",
        "Linux Automation",
        "Projects Showcase"
    ]
    selected_page = st.sidebar.selectbox("Select Tool", pages, key="page_selector")
    return selected_page

# Initialize session state
if 'selected_page' not in st.session_state:
    st.session_state.selected_page = "Home"

# Main app logic
def main():
    selected_page = setup_sidebar()
    st.session_state.selected_page = selected_page

    st.title("Achyut Dubey's Multipurpose AI + DevOps Dashboard")
    st.markdown("A powerful suite of automation and AI tools for DevOps, ML, and more.")

    # Page routing
    if selected_page == "Home":
        st.header("Welcome to the Dashboard")
        st.markdown("""
        This dashboard provides a suite of 14 tools for automation, AI, and DevOps tasks.
        Use the sidebar to navigate to each tool. Built by **Achyut Dubey** (Team 07).
        """)
        st.subheader("Available Tools")
        cols = st.columns(3)
        for i, page in enumerate([
            "Docker Automation", "Kubernetes Automation", "AWS EC2 Launcher (Gesture-Based)",
            "AWS Automation Provisioner", "GenAI-Based Project Evaluator (Manthan)",
            "Prompt Engineering Comparator", "GitHub Agentic Code Pusher", "Python Multi-Task Menu",
            "Machine Learning Dashboard", "AI Quiz Generator", "Microservice Architecture Visualizer",
            "Linux Automation", "Projects Showcase"
        ]):
            with cols[i % 3]:
                st.markdown(f"- **{page}**")

    elif selected_page == "Docker Automation":
        st.header("Docker Automation")
        docker_page()

    elif selected_page == "Kubernetes Automation":
        st.header("Kubernetes Automation")
        kubernetes_page()

    elif selected_page == "AWS EC2 Launcher (Gesture-Based)":
        st.header("AWS EC2 Launcher (Gesture-Based)")
        aws_ec2_gesture_page()

    elif selected_page == "AWS Automation Provisioner":
        st.header("AWS Automation Provisioner")
        aws_provisioner_page()

    elif selected_page == "GenAI-Based Project Evaluator (Manthan)":
        st.header("GenAI-Based Project Evaluator (Manthan)")
        genai_evaluator_page()

    elif selected_page == "Prompt Engineering Comparator":
        st.header("Prompt Engineering Comparator")
        prompt_comparator_page()

    elif selected_page == "GitHub Agentic Code Pusher":
        st.header("GitHub Agentic Code Pusher")
        github_pusher_page()

    elif selected_page == "Python Multi-Task Menu":
        st.header("Python Multi-Task Menu")
        python_multitask_page()

    elif selected_page == "Machine Learning Dashboard":
        st.header("Machine Learning Dashboard")
        ml_dashboard_page()

    elif selected_page == "AI Quiz Generator":
        st.header("AI Quiz Generator")
        st.write("Generate MCQs dynamically for a given topic.")
        # Placeholder for AI Quiz Generator
        topic = st.text_input("Enter Topic (e.g., DevOps, ML, Python)")
        num_questions = st.slider("Number of Questions", 5, 10, 5)
        if st.button("Generate Quiz"):
            with st.spinner("Generating quiz..."):
                try:
                    # Mock implementation (replace with actual LLM call)
                    st.write(f"Generated {num_questions} MCQs for {topic}")
                    for i in range(num_questions):
                        st.markdown(f"**Q{i+1}**: Sample question {i+1} for {topic}?")
                        st.radio(f"Options for Q{i+1}", ["A", "B", "C", "D"], key=f"q{i+1}")
                    if st.button("Submit Quiz"):
                        st.success("Quiz submitted! Score: TBD")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    elif selected_page == "Microservice Architecture Visualizer":
        st.header("Microservice Architecture Visualizer")
        st.write("Visualize a 3-tier architecture with Docker Compose, Kubernetes, and AWS.")
        # Placeholder for visualization
        st.write("Network diagram coming soon...")

    elif selected_page == "Linux Automation":
        st.header("Linux Automation")
        linux_automation_page()

    elif selected_page == "Projects Showcase":
        st.header("Projects Showcase")
        st.write("Showcasing 3-tier architectures and deployments.")
        # Placeholder for showcase
        st.markdown("""
        ### Projects
        - **3-Tier Docker Compose Stack**: Multi-container setup with web, app, and database layers.
        - **3-Tier Kubernetes Deployment**: Master-worker node visualization.
        - **AWS Infrastructure**: EC2, Prometheus, and Grafana monitoring.
        """)

# Run the app
if __name__ == "__main__":
    main()
