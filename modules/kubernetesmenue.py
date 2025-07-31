import streamlit as st
import subprocess
import yaml
import requests
import os
import tempfile
import json
import re
from datetime import datetime

def run():
    """Main function to run the Kubernetes menu module"""
    # Streamlit Dashboard Setup
    st.title("Kubernetes Management Dashboard")
    st.markdown("Manage Kubernetes resources, generate YAMLs, execute YAMLs, and switch contexts/namespaces.")

    # Initialize session state for context and namespace
    if 'current_context' not in st.session_state:
        st.session_state.current_context = None
    if 'current_namespace' not in st.session_state:
        st.session_state.current_namespace = 'default'

    # Helper function to run kubectl commands
    def run_kubectl_command(command, return_output=True):
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            if return_output:
                return result.stdout
            return "Command executed successfully."
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}"

    # Helper function to sanitize YAML
    def sanitize_yaml(yaml_content):
        # Basic sanitization: remove potentially harmful commands
        yaml_content = re.sub(r'!\w+', '', yaml_content)  # Remove YAML tags
        return yaml_content

    # Sidebar for tab selection
    tab = st.sidebar.radio(
        "Select Functionality",
        ["Kubernetes Resources", "YAML Generator", "YAML Executor", "Context & Namespace"]
    )

    # Tab 1: Kubernetes Resource Management
    if tab == "Kubernetes Resources":
        st.header("Kubernetes Resource Management")
        st.write("View, describe, manage, and interact with Kubernetes resources.")

        resources = [
            "pods", "deployments", "services", "replicasets", "statefulsets",
            "daemonsets", "jobs", "cronjobs", "persistentvolumeclaims",
            "configmaps", "secrets", "ingresses", "nodes", "namespaces"
        ]
        selected_resource = st.selectbox("Select Resource Type", resources)
        namespace = st.text_input("Namespace", value=st.session_state.current_namespace)

        # Get resource names
        resource_names = []
        if selected_resource and namespace:
            cmd = f"kubectl get {selected_resource} -n {namespace} --no-headers -o custom-columns=NAME:.metadata.name"
            output = run_kubectl_command(cmd)
            if not output.startswith("Error"):
                resource_names = [name.strip() for name in output.splitlines() if name.strip()]
        
        selected_name = st.selectbox("Select Resource Name", resource_names) if resource_names else None

        # Command buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(f"View All {selected_resource}"):
                cmd = f"kubectl get {selected_resource} -n {namespace}"
                st.code(run_kubectl_command(cmd), language="bash")
        
        with col2:
            if selected_name and st.button("Describe"):
                cmd = f"kubectl describe {selected_resource} {selected_name} -n {namespace}"
                st.code(run_kubectl_command(cmd), language="bash")
        
        with col3:
            if selected_name and st.button("Delete"):
                cmd = f"kubectl delete {selected_resource} {selected_name} -n {namespace}"
                st.code(run_kubectl_command(cmd), language="bash")

        # Pod-specific actions
        if selected_resource == "pods" and selected_name:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("View Logs"):
                    cmd = f"kubectl logs {selected_name} -n {namespace}"
                    st.code(run_kubectl_command(cmd), language="bash")
            with col2:
                if st.button("Exec into Pod"):
                    cmd = f"kubectl exec -it {selected_name} -n {namespace} -- /bin/bash"
                    output = run_kubectl_command(cmd)
                    st.code(output, language="bash")

        # YAML Apply/Delete
        yaml_content = st.text_area("Paste YAML to Apply/Delete", height=200)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Apply YAML"):
                if yaml_content:
                    sanitized_yaml = sanitize_yaml(yaml_content)
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
                        tmp.write(sanitized_yaml)
                        tmp_file = tmp.name
                    cmd = f"kubectl apply -f {tmp_file}"
                    st.code(run_kubectl_command(cmd), language="bash")
                    os.unlink(tmp_file)
                else:
                    st.warning("Please provide YAML content.")
        with col2:
            if st.button("Delete YAML"):
                if yaml_content:
                    sanitized_yaml = sanitize_yaml(yaml_content)
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
                        tmp.write(sanitized_yaml)
                        tmp_file = tmp.name
                    cmd = f"kubectl delete -f {tmp_file}"
                    st.code(run_kubectl_command(cmd), language="bash")
                    os.unlink(tmp_file)
                else:
                    st.warning("Please provide YAML content.")

    # Tab 2: YAML Generator
    elif tab == "YAML Generator":
        st.header("YAML Generator")
        st.write("Generate Kubernetes YAML files using AI-powered prompts.")
        
        prompt = st.text_area("Describe what you want to create:", 
                             placeholder="Example: Create a deployment for a Node.js app with 3 replicas, port 3000, and a service",
                             height=100)
        
        def generate_yaml_mock(prompt):
            # Mock implementation of Gemini 1.5 Flash
            prompt_lower = prompt.lower()
            
            if "deployment" in prompt_lower and "nodejs" in prompt_lower:
                port = 3000
                if "port" in prompt_lower:
                    port_match = re.search(r'port (\d+)', prompt_lower)
                    if port_match:
                        port = int(port_match.group(1))
                
                yaml_content = {
                    'apiVersion': 'apps/v1',
                    'kind': 'Deployment',
                    'metadata': {'name': 'nodejs-app'},
                    'spec': {
                        'replicas': 3,
                        'selector': {'matchLabels': {'app': 'nodejs'}},
                        'template': {
                            'metadata': {'labels': {'app': 'nodejs'}},
                            'spec': {
                                'containers': [{
                                    'name': 'nodejs',
                                    'image': 'node:18',
                                    'ports': [{'containerPort': port}]
                                }]
                            }
                        }
                    }
                }
                
                service_yaml = {
                    'apiVersion': 'v1',
                    'kind': 'Service',
                    'metadata': {'name': 'nodejs-service'},
                    'spec': {
                        'selector': {'app': 'nodejs'},
                        'ports': [{'protocol': 'TCP', 'port': port, 'targetPort': port}],
                        'type': 'ClusterIP'
                    }
                }
                return yaml.dump_all([yaml_content, service_yaml], default_flow_style=False)
            return "# Generated YAML\n# No valid template for the given prompt"

        if st.button("Generate YAML"):
            if prompt:
                try:
                    yaml_output = generate_yaml_mock(prompt)
                    st.session_state.yaml_output = yaml_output
                    st.code(yaml_output, language="yaml")
                except Exception as e:
                    st.error(f"Error generating YAML: {str(e)}")
            else:
                st.warning("Please enter a prompt.")
        
        # Display and allow editing of generated YAML
        if 'yaml_output' in st.session_state:
            edited_yaml = st.text_area("Edit Generated YAML", value=st.session_state.yaml_output, height=300)
            if st.download_button("Download YAML", edited_yaml, file_name="generated.yaml"):
                st.success("YAML downloaded!")

    # Tab 3: YAML Executor
    elif tab == "YAML Executor":
        st.header("YAML Executor")
        st.write("Apply or delete YAML files or pasted content.")
        
        yaml_input = st.text_area("Paste YAML Content", height=200)
        uploaded_file = st.file_uploader("Upload YAML File", type=["yaml", "yml"])
        
        if uploaded_file:
            yaml_input = uploaded_file.read().decode("utf-8")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Apply YAML"):
                if yaml_input:
                    sanitized_yaml = sanitize_yaml(yaml_input)
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
                        tmp.write(sanitized_yaml)
                        tmp_file = tmp.name
                    cmd = f"kubectl apply -f {tmp_file}"
                    st.code(run_kubectl_command(cmd), language="bash")
                    os.unlink(tmp_file)
                else:
                    st.warning("Please provide YAML content or upload a file.")
        with col2:
            if st.button("Delete YAML"):
                if yaml_input:
                    sanitized_yaml = sanitize_yaml(yaml_input)
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
                        tmp.write(sanitized_yaml)
                        tmp_file = tmp.name
                    cmd = f"kubectl delete -f {tmp_file}"
                    st.code(run_kubectl_command(cmd), language="bash")
                    os.unlink(tmp_file)
                else:
                    st.warning("Please provide YAML content or upload a file.")

    # Tab 4: Context & Namespace Switcher
    elif tab == "Context & Namespace":
        st.header("Context & Namespace Switcher")
        st.write("Switch Kubernetes contexts and namespaces.")
        
        # Get contexts
        cmd = "kubectl config get-contexts --no-headers -o name"
        contexts = run_kubectl_command(cmd)
        context_list = contexts.splitlines() if not contexts.startswith("Error") else []
        
        selected_context = st.selectbox("Select Context", context_list, index=context_list.index(st.session_state.current_context) if st.session_state.current_context in context_list else 0)
        
        if st.button("Switch Context"):
            if selected_context:
                cmd = f"kubectl config use-context {selected_context}"
                output = run_kubectl_command(cmd)
                st.code(output, language="bash")
                st.session_state.current_context = selected_context
        
        # Get namespaces
        cmd = "kubectl get namespaces --no-headers -o custom-columns=NAME:.metadata.name"
        namespaces = run_kubectl_command(cmd)
        namespace_list = namespaces.splitlines() if not namespaces.startswith("Error") else ['default']
        
        selected_namespace = st.selectbox("Select Namespace", namespace_list, index=namespace_list.index(st.session_state.current_namespace) if st.session_state.current_namespace in namespace_list else 0)
        
        if st.button("Switch Namespace"):
            st.session_state.current_namespace = selected_namespace
            st.success(f"Switched to namespace: {selected_namespace}")

    # Security Notes
    st.sidebar.markdown("""
    ### Security Notes
    - Ensure `kubectl` is configured with proper authentication.
    - Avoid exposing sensitive kubeconfig details.
    - YAML inputs are sanitized to prevent command injection.
    - Use secure API keys for external services (e.g., Gemini).
    """)