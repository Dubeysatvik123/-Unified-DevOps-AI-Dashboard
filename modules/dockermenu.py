import streamlit as st
import subprocess
import pandas as pd
import json
import time
import requests
import os
from typing import List, Dict, Any, Optional
import google.generativeai as genai

# Page configuration
# Note: Page config is handled by the main app
# st.set_page_config(
#     page_title="DOX - The Docker Automation Tool",
#     page_icon="🐳",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79, #2980b9);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    .mode-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .mode-card h3 {
        color: white;
        margin-bottom: 1rem;
    }
    .mode-card p {
        color: #f0f0f0;
        margin-bottom: 0;
    }
    .success-msg {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-msg {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .warning-msg {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .docker-stats {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .ai-response {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .gemini-badge {
        background: linear-gradient(135deg, #4285f4 0%, #34a853 100%);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        color: white;
        font-size: 0.8rem;
        display: inline-block;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# AI Integration Class with Gemini
class AIDockerAssistant:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.model = None
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.ai_enabled = True
            except Exception as e:
                st.error(f"Failed to initialize Gemini AI: {str(e)}")
                self.ai_enabled = False
        else:
            self.ai_enabled = False
        
        self.docker_command_prompt = """You are a Docker expert assistant. When given a natural language request about Docker, 
        respond with ONLY the appropriate Docker command(s). Do not include explanations, markdown formatting, or additional text.
        
        Examples:
        - "show running containers" -> docker ps
        - "list all containers" -> docker ps -a
        - "stop container nginx" -> docker stop nginx
        - "remove all stopped containers" -> docker container prune -f
        - "show container logs for myapp" -> docker logs myapp
        - "create container from nginx" -> docker run -d --name nginx-container nginx
        - "show docker images" -> docker images
        - "system cleanup" -> docker system prune -af
        - "container stats" -> docker stats --no-stream
        
        Return only the Docker command, nothing else."""
        
        self.dockerfile_prompt = """You are a Docker expert. Generate a production-ready Dockerfile based on the application description provided.
        
        Requirements:
        - Use appropriate base images
        - Include multi-stage builds when beneficial
        - Add security best practices (non-root user, minimal attack surface)
        - Include health checks when applicable
        - Optimize for caching and build speed
        - Add appropriate labels and metadata
        - Handle dependencies efficiently
        
        Return only the Dockerfile content without any explanations or markdown formatting."""
    
    def translate_to_docker_command(self, user_request: str) -> str:
        """Translate natural language to Docker command using Gemini AI."""
        if not self.ai_enabled:
            return self._fallback_command_translation(user_request)
        
        try:
            full_prompt = f"{self.docker_command_prompt}\n\nUser request: {user_request}\n\nDocker command:"
            
            response = self.model.generate_content(full_prompt)
            command = response.text.strip()
            
            # Clean up the response - remove any extra formatting
            command = command.replace('```', '').replace('bash', '').replace('shell', '').strip()
            
            # Validate it's a docker command
            if command.startswith('docker'):
                return command
            else:
                # If AI doesn't return a docker command, try fallback
                return self._fallback_command_translation(user_request)
                
        except Exception as e:
            st.error(f"AI translation failed: {str(e)}")
            return self._fallback_command_translation(user_request)
    
    def _fallback_command_translation(self, user_request: str) -> str:
        """Fallback pattern matching for common Docker operations."""
        request_lower = user_request.lower()
        
        # Pattern matching for common Docker operations
        patterns = {
            'show running containers': 'docker ps',
            'list running containers': 'docker ps',
            'show all containers': 'docker ps -a',
            'list all containers': 'docker ps -a',
            'show images': 'docker images',
            'list images': 'docker images',
            'show networks': 'docker network ls',
            'list networks': 'docker network ls',
            'show volumes': 'docker volume ls',
            'list volumes': 'docker volume ls',
            'system cleanup': 'docker system prune -af',
            'clean up': 'docker system prune -af',
            'container stats': 'docker stats --no-stream',
            'system info': 'docker system df',
            'docker version': 'docker --version',
            'remove unused images': 'docker image prune -f',
            'remove stopped containers': 'docker container prune -f',
            'remove unused volumes': 'docker volume prune -f',
            'remove unused networks': 'docker network prune -f',
        }
        
        # Find matching pattern
        for pattern, command in patterns.items():
            if pattern in request_lower:
                return command
        
        # Handle specific container operations
        if 'stop' in request_lower and 'container' in request_lower:
            words = request_lower.split()
            if len(words) > 2:
                container_name = words[-1]
                return f"docker stop {container_name}"
            return "docker ps"
        
        if 'start' in request_lower and 'container' in request_lower:
            words = request_lower.split()
            if len(words) > 2:
                container_name = words[-1]
                return f"docker start {container_name}"
            return "docker ps -a"
        
        if 'logs' in request_lower:
            words = request_lower.split()
            if len(words) > 1:
                container_name = words[-1]
                return f"docker logs --tail 50 {container_name}"
            return "docker ps"
        
        if 'create' in request_lower and 'container' in request_lower:
            if 'nginx' in request_lower:
                return "docker run -d --name nginx-container nginx"
            elif 'ubuntu' in request_lower:
                return "docker run -dit --name ubuntu-container ubuntu"
            return "docker run -dit --name new-container ubuntu"
        
        return None
    
    def generate_dockerfile(self, app_description: str) -> str:
        """Generate Dockerfile based on application description using Gemini AI."""
        if not self.ai_enabled:
            return self._fallback_dockerfile_generation(app_description)
        
        try:
            full_prompt = f"{self.dockerfile_prompt}\n\nApplication description: {app_description}\n\nGenerate a Dockerfile:"
            
            response = self.model.generate_content(full_prompt)
            dockerfile_content = response.text.strip()
            
            # Clean up the response - remove markdown formatting if present
            dockerfile_content = dockerfile_content.replace('```dockerfile', '').replace('```', '').strip()
            
            # Ensure it starts with a FROM instruction
            if not dockerfile_content.startswith('FROM') and not dockerfile_content.startswith('#'):
                return self._fallback_dockerfile_generation(app_description)
            
            return dockerfile_content
            
        except Exception as e:
            st.error(f"AI Dockerfile generation failed: {str(e)}")
            return self._fallback_dockerfile_generation(app_description)
    
    def _fallback_dockerfile_generation(self, app_description: str) -> str:
        """Fallback Dockerfile generation based on keywords."""
        description_lower = app_description.lower()
        
        if any(keyword in description_lower for keyword in ['python', 'flask', 'django', 'fastapi']):
            return self._generate_python_dockerfile(description_lower)
        elif any(keyword in description_lower for keyword in ['node', 'javascript', 'npm', 'express']):
            return self._generate_nodejs_dockerfile(description_lower)
        elif any(keyword in description_lower for keyword in ['java', 'spring', 'maven', 'gradle']):
            return self._generate_java_dockerfile(description_lower)
        elif any(keyword in description_lower for keyword in ['go', 'golang']):
            return self._generate_go_dockerfile(description_lower)
        elif any(keyword in description_lower for keyword in ['rust', 'cargo']):
            return self._generate_rust_dockerfile(description_lower)
        else:
            return self._generate_generic_dockerfile()
    
    def _generate_python_dockerfile(self, description: str) -> str:
        if 'flask' in description:
            return """# Python Flask Application
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "app.py"]"""
        
        elif 'django' in description:
            return """# Django Application
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Collect static files
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "project.wsgi:application"]"""
        
        else:
            return """# Python Application
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["python", "main.py"]"""
    
    def _generate_nodejs_dockerfile(self, description: str) -> str:
        return """# Node.js Application
FROM node:18-alpine

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Copy application code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001
RUN chown -R nextjs:nodejs /app
USER nextjs

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:3000/health || exit 1

CMD ["node", "server.js"]"""
    
    def _generate_java_dockerfile(self, description: str) -> str:
        if 'maven' in description:
            return """# Java Maven Application
FROM maven:3.9.4-openjdk-17 AS build

WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline

COPY src ./src
RUN mvn clean package -DskipTests

FROM openjdk:17-jre-slim

WORKDIR /app
COPY --from=build /app/target/*.jar app.jar

# Create non-root user
RUN useradd -m -u 1000 appuser
USER appuser

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/actuator/health || exit 1

CMD ["java", "-jar", "app.jar"]"""
        else:
            return """# Java Application
FROM openjdk:17-jre-slim

WORKDIR /app
COPY target/*.jar app.jar

# Create non-root user
RUN useradd -m -u 1000 appuser
USER appuser

EXPOSE 8080

CMD ["java", "-jar", "app.jar"]"""
    
    def _generate_go_dockerfile(self, description: str) -> str:
        return """# Go Application
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/

COPY --from=builder /app/main .

# Create non-root user
RUN adduser -D -s /bin/sh appuser
USER appuser

EXPOSE 8080

CMD ["./main"]"""
    
    def _generate_rust_dockerfile(self, description: str) -> str:
        return """# Rust Application
FROM rust:1.75 as builder

WORKDIR /app
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release
RUN rm src/main.rs

COPY src ./src
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/target/release/app .

# Create non-root user
RUN useradd -m -u 1000 appuser
USER appuser

EXPOSE 8080

CMD ["./app"]"""
    
    def _generate_generic_dockerfile(self) -> str:
        return """# Generic Application
FROM ubuntu:22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install common dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    wget \\
    git \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

# Add your application-specific commands here
# RUN make install

CMD ["./start.sh"]"""

# Utility functions
def run_docker_command(command: str) -> tuple[bool, str]:
    """Execute a docker command and return success status and output."""
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout if result.returncode == 0 else result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)

def get_containers() -> List[Dict[str, Any]]:
    """Get list of all containers."""
    success, output = run_docker_command("docker ps -a --format json")
    if not success:
        return []
    
    containers = []
    for line in output.strip().split('\n'):
        if line.strip():
            try:
                containers.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return containers

def get_images() -> List[Dict[str, Any]]:
    """Get list of all images."""
    success, output = run_docker_command("docker images --format json")
    if not success:
        return []
    
    images = []
    for line in output.strip().split('\n'):
        if line.strip():
            try:
                images.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return images

def get_networks() -> List[str]:
    """Get list of networks."""
    success, output = run_docker_command("docker network ls --format {{.Name}}")
    if not success:
        return []
    return [line.strip() for line in output.strip().split('\n') if line.strip()]

def get_volumes() -> List[str]:
    """Get list of volumes."""
    success, output = run_docker_command("docker volume ls --format {{.Name}}")
    if not success:
        return []
    return [line.strip() for line in output.strip().split('\n') if line.strip()]

def run():
    """Main function to run the Docker menu module"""
    # Initialize session state
    if 'mode' not in st.session_state:
        st.session_state.mode = 'home'
    if 'command_history' not in st.session_state:
        st.session_state.command_history = []
    if 'gemini_api_key' not in st.session_state:
        st.session_state.gemini_api_key = ""

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🐳 DOX - The Docker Automation Tool</h1>
        <p style="color: #ecf0f1; font-size: 1.2rem; margin: 0;">AI-powered Docker management interface</p>
        <div class="gemini-badge">⚡ Powered by Gemini AI Flash 1.5</div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar navigation
    with st.sidebar:
        st.markdown("## 🚀 Navigation")
        mode = st.radio(
            "Select Mode:",
            ["🏠 Home", "🔰 Beginner Mode", "⚡ Pro Mode"],
            index=0
        )
        
        if mode == "🏠 Home":
            st.session_state.mode = 'home'
        elif mode == "🔰 Beginner Mode":
            st.session_state.mode = 'beginner'
        elif mode == "⚡ Pro Mode":
            st.session_state.mode = 'pro'
        
        # Gemini API Key configuration
        st.markdown("---")
        st.markdown("## 🤖 AI Configuration")
        api_key_input = st.text_input(
            "Gemini API Key:",
            type="password",
            value=st.session_state.gemini_api_key,
            help="Enter your Google Gemini API key for AI features"
        )
        
        if api_key_input != st.session_state.gemini_api_key:
            st.session_state.gemini_api_key = api_key_input
        
        if st.session_state.gemini_api_key:
            st.success("🔑 API key configured")
        else:
            st.warning("⚠️ No API key - using fallback mode")
        
        if st.button("🔗 Get Gemini API Key"):
            st.markdown("[Get your free Gemini API key here](https://makersuite.google.com/app/apikey)")
        
        # Quick stats in sidebar
        st.markdown("---")
        st.markdown("## 📊 Quick Stats")
        try:
            containers = get_containers()
            running_containers = len([c for c in containers if c.get('State') == 'running'])
            st.metric("Running", running_containers)
            st.metric("Total Containers", len(containers))
            st.metric("Images", len(get_images()))
        except:
            st.info("Docker not available")

    # Initialize AI assistant with API key
    ai_assistant = AIDockerAssistant(st.session_state.gemini_api_key)

    # Home page
    if st.session_state.mode == 'home':
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="mode-card">
                <h3>🔰 Beginner Mode</h3>
                <p>Perfect for Docker beginners! Easy-to-use interface with guided options for:</p>
                <ul style="color: #f0f0f0;">
                    <li>Container management</li>
                    <li>Image operations</li>
                    <li>Network & volume management</li>
                    <li>System cleanup</li>
                    <li>Troubleshooting tools</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="mode-card">
                <h3>⚡ Pro Mode</h3>
                <p>Advanced features for Docker experts:</p>
                <ul style="color: #f0f0f0;">
                    <li>{'🤖 AI-powered command execution' if ai_assistant.ai_enabled else '🔄 Pattern-based command matching'}</li>
                    <li>{'🧠 Intelligent Dockerfile generation' if ai_assistant.ai_enabled else '📝 Template-based Dockerfiles'}</li>
                    <li>Natural language Docker commands</li>
                    <li>Advanced troubleshooting</li>
                    <li>Custom workflows</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Quick actions
        st.markdown("---")
        st.markdown("## ⚡ Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 View Containers", key="quick_containers"):
                st.session_state.mode = 'beginner'
                st.rerun()
        
        with col2:
            if st.button("🤖 AI Commands", key="quick_ai"):
                st.session_state.mode = 'pro'
                st.rerun()
        
        with col3:
            if st.button("🧹 System Cleanup", key="quick_cleanup"):
                st.session_state.mode = 'beginner'
                st.rerun()
        
        # System status
        st.markdown("---")
        st.markdown("## 📊 System Status")
        
        try:
            containers = get_containers()
            images = get_images()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                running_containers = len([c for c in containers if c.get('State') == 'running'])
                st.metric("🟢 Running Containers", running_containers)
            
            with col2:
                stopped_containers = len([c for c in containers if c.get('State') == 'exited'])
                st.metric("🔴 Stopped Containers", stopped_containers)
            
            with col3:
                st.metric("📦 Docker Images", len(images))
            
            with col4:
                networks = get_networks()
                st.metric("🌐 Networks", len(networks))
            
            # Recent activity
            if st.session_state.command_history:
                st.markdown("### 📈 Recent Activity")
                recent_commands = st.session_state.command_history[-5:]
                for cmd in recent_commands:
                    success_icon = "✅" if cmd['success'] else "❌"
                    st.write(f"{success_icon} {cmd['timestamp']} - {cmd['request'][:50]}...")
            
        except Exception as e:
            st.error(f"❌ Error connecting to Docker: {str(e)}")
            st.info("💡 Make sure Docker is running and accessible")

    # Beginner Mode
    elif st.session_state.mode == 'beginner':
        st.markdown("## 🔰 Beginner Mode - Easy Docker Management")
        
        tab1, tab2, tab3 = st.tabs(["📦 Containers", "🖼️ Images", "🧹 System"])
        
        with tab1:
            st.subheader("📦 Container Management")
            
            # Container operations
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🚀 Start Container")
                containers = get_containers()
                stopped_containers = [c for c in containers if c.get('State') == 'exited']
                
                if stopped_containers:
                    selected_container = st.selectbox(
                        "Select stopped container:",
                        [c['Names'] for c in stopped_containers]
                    )
                    
                    if st.button("▶️ Start Container"):
                        success, output = run_docker_command(f"docker start {selected_container}")
                        if success:
                            st.success(f"✅ Container {selected_container} started!")
                        else:
                            st.error(f"❌ Failed to start container: {output}")
                        st.rerun()
                else:
                    st.info("No stopped containers found")
            
            with col2:
                st.markdown("### ⏹️ Stop Container")
                running_containers = [c for c in containers if c.get('State') == 'running']
                
                if running_containers:
                    selected_container = st.selectbox(
                        "Select running container:",
                        [c['Names'] for c in running_containers]
                    )
                    
                    if st.button("⏹️ Stop Container"):
                        success, output = run_docker_command(f"docker stop {selected_container}")
                        if success:
                            st.success(f"✅ Container {selected_container} stopped!")
                        else:
                            st.error(f"❌ Failed to stop container: {output}")
                        st.rerun()
                else:
                    st.info("No running containers found")
            
            # Container list
            st.markdown("### 📋 All Containers")
            containers = get_containers()
            
            if containers:
                df = pd.DataFrame(containers)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No containers found")
        
        with tab2:
            st.subheader("🖼️ Image Management")
            
            # Image operations
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🗑️ Remove Image")
                images = get_images()
                
                if images:
                    selected_image = st.selectbox(
                        "Select image to remove:",
                        [f"{img['Repository']}:{img['Tag']}" for img in images]
                    )
                    
                    if st.button("🗑️ Remove Image"):
                        success, output = run_docker_command(f"docker rmi {selected_image}")
                        if success:
                            st.success(f"✅ Image {selected_image} removed!")
                        else:
                            st.error(f"❌ Failed to remove image: {output}")
                        st.rerun()
                else:
                    st.info("No images found")
            
            with col2:
                st.markdown("### 📥 Pull Image")
                image_name = st.text_input("Image name (e.g., nginx:latest):")
                
                if st.button("📥 Pull Image"):
                    if image_name:
                        success, output = run_docker_command(f"docker pull {image_name}")
                        if success:
                            st.success(f"✅ Image {image_name} pulled successfully!")
                        else:
                            st.error(f"❌ Failed to pull image: {output}")
                        st.rerun()
                    else:
                        st.warning("Please enter an image name")
            
            # Image list
            st.markdown("### 📋 All Images")
            images = get_images()
            
            if images:
                df = pd.DataFrame(images)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No images found")
        
        with tab3:
            st.subheader("🧹 System Cleanup")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🗑️ Remove Unused Containers")
                if st.button("🧹 Remove Stopped Containers"):
                    success, output = run_docker_command("docker container prune -f")
                    if success:
                        st.success("✅ Stopped containers removed!")
                    else:
                        st.error(f"❌ Failed to remove containers: {output}")
                    st.rerun()
                
                st.markdown("### 🗑️ Remove Unused Images")
                if st.button("🧹 Remove Dangling Images"):
                    success, output = run_docker_command("docker image prune -f")
                    if success:
                        st.success("✅ Dangling images removed!")
                    else:
                        st.error(f"❌ Failed to remove images: {output}")
                    st.rerun()
            
            with col2:
                st.markdown("### 🗑️ Remove Unused Networks")
                if st.button("🧹 Remove Unused Networks"):
                    success, output = run_docker_command("docker network prune -f")
                    if success:
                        st.success("✅ Unused networks removed!")
                    else:
                        st.error(f"❌ Failed to remove networks: {output}")
                    st.rerun()
                
                st.markdown("### 🗑️ Remove Unused Volumes")
                if st.button("🧹 Remove Unused Volumes"):
                    success, output = run_docker_command("docker volume prune -f")
                    if success:
                        st.success("✅ Unused volumes removed!")
                    else:
                        st.error(f"❌ Failed to remove volumes: {output}")
                    st.rerun()
            
            # System info
            st.markdown("### 📊 System Information")
            try:
                success, output = run_docker_command("docker system df")
                if success:
                    st.code(output, language="bash")
                else:
                    st.error(f"❌ Failed to get system info: {output}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    # Pro Mode
    elif st.session_state.mode == 'pro':
        st.markdown("## ⚡ Pro Mode - AI-Powered Docker Management")
        
        tab1, tab2, tab3 = st.tabs(["🤖 AI Commands", "📝 Dockerfile Generator", "📊 Command History"])
        
        with tab1:
            st.subheader("🤖 AI-Powered Command Execution")
            
            if not ai_assistant.ai_enabled:
                st.warning("⚠️ Gemini API key not configured. Using fallback pattern matching.")
                st.info("💡 Add your Gemini API key in the sidebar for full AI capabilities!")
            
            # Command input
            user_request = st.text_area(
                "Describe what you want to do:",
                placeholder="Examples:\n- Start all stopped containers\n- Remove all unused images\n- Show running containers with their ports\n- Create a new network called 'myapp'",
                height=100
            )
            
            if st.button("🚀 Execute Command", type="primary"):
                if user_request:
                    with st.spinner("Processing your request..."):
                        # Get command from AI or fallback
                        if ai_assistant.ai_enabled:
                            command = ai_assistant.translate_to_docker_command(user_request)
                            ai_powered = True
                        else:
                            command = ai_assistant._fallback_command_translation(user_request)
                            ai_powered = False
                        
                        # Execute command
                        success, output = run_docker_command(command)
                        
                        # Store in history
                        st.session_state.command_history.append({
                            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                            'request': user_request,
                            'command': command,
                            'output': output,
                            'success': success,
                            'ai_powered': ai_powered
                        })
                        
                        # Display results
                        st.markdown("### 📋 Results")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Request:** {user_request}")
                            st.markdown(f"**Command:** `{command}`")
                            st.markdown(f"**Method:** {'🤖 Gemini AI' if ai_powered else '🔄 Pattern Matching'}")
                        
                        with col2:
                            if success:
                                st.success("✅ Command executed successfully!")
                            else:
                                st.error("❌ Command failed!")
                        
                        if output:
                            st.text_area("Output:", output, height=200)
                        
                        st.rerun()
                else:
                    st.warning("Please enter a request")
        
        with tab2:
            st.subheader("📝 AI Dockerfile Generator")
            
            if not ai_assistant.ai_enabled:
                st.warning("⚠️ Gemini API key not configured. Using template-based generation.")
                st.info("💡 Add your Gemini API key in the sidebar for intelligent Dockerfile generation!")
            
            app_name = st.text_input("Application name:")
            app_description = st.text_area(
                "Describe your application:",
                placeholder="Examples:\n- A Python Flask web application with Redis cache\n- A Node.js API server with PostgreSQL database\n- A Java Spring Boot application with Maven build\n- A Go microservice with health checks",
                height=150
            )
            
            if st.button("🤖 Generate Dockerfile"):
                if app_description:
                    with st.spinner("Generating Dockerfile..."):
                        if ai_assistant.ai_enabled:
                            dockerfile_content = ai_assistant.generate_dockerfile(app_description)
                        else:
                            dockerfile_content = ai_assistant._fallback_dockerfile_generation(app_description)
                        
                        st.markdown("### 📄 Generated Dockerfile")
                        st.code(dockerfile_content, language="dockerfile")
                        
                        # Security analysis
                        st.markdown("### 🔒 Security Analysis")
                        security_features = []
                        
                        if "USER" in dockerfile_content:
                            security_features.append("✅ Non-root user configured")
                        else:
                            security_features.append("⚠️ Running as root (security risk)")
                        
                        if "COPY" in dockerfile_content and "ADD" not in dockerfile_content:
                            security_features.append("✅ Using COPY instead of ADD")
                        elif "ADD" in dockerfile_content:
                            security_features.append("⚠️ Using ADD (consider COPY for better security)")
                        
                        if "RUN" in dockerfile_content and "apt-get clean" in dockerfile_content:
                            security_features.append("✅ Package cache cleaned")
                        elif "RUN" in dockerfile_content and "apt-get" in dockerfile_content:
                            security_features.append("⚠️ Package cache not cleaned")
                        
                        if "EXPOSE" in dockerfile_content:
                            security_features.append("✅ Ports explicitly exposed")
                        else:
                            security_features.append("⚠️ No ports explicitly exposed")
                        
                        for feature in security_features:
                            st.write(feature)
                        
                        # Best practices
                        st.markdown("### 💡 Best Practices")
                        if ai_assistant.ai_enabled:
                            st.write("• Multi-stage builds for smaller images")
                            st.write("• Layer caching optimization")
                            st.write("• Minimal attack surface with slim base images")
                        
                        # Download button
                        st.download_button(
                            label="💾 Download Dockerfile",
                            data=dockerfile_content,
                            file_name="Dockerfile",
                            mime="text/plain",
                            key="download_dockerfile"
                        )
                        
                        # Build options
                        st.subheader("🔨 Build Options")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            image_name = st.text_input("🏷️ Image name:", value=app_name if app_name else "generated-app", key="build_image_name")
                            image_tag = st.text_input("🏷️ Tag:", value="latest", key="build_tag")
                        
                        with col2:
                            st.markdown("**Build Command Preview:**")
                            build_command = f"docker build -t {image_name}:{image_tag} ."
                            st.code(build_command, language="bash")
                        
                        if st.button("🔨 Build Docker Image", key="build_image"):
                            if image_name:
                                st.info(f"To build this image, save the Dockerfile and run:\n`{build_command}`")
                                st.warning("Note: Building requires the Dockerfile to be saved in your project directory with your application code.")
                            else:
                                st.warning("Please enter an image name.")
                else:
                    st.warning("Please describe your application.")
        
        with tab3:
            st.subheader("📊 Command History")
            
            if st.session_state.command_history:
                # Statistics
                ai_commands = len([cmd for cmd in st.session_state.command_history if cmd.get('ai_powered', False)])
                fallback_commands = len(st.session_state.command_history) - ai_commands
                successful_commands = len([cmd for cmd in st.session_state.command_history if cmd['success']])
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📈 Total Commands", len(st.session_state.command_history))
                with col2:
                    st.metric("🤖 AI-Powered", ai_commands)
                with col3:
                    st.metric("🔄 Pattern-Based", fallback_commands)
                with col4:
                    st.metric("✅ Successful", successful_commands)
                
                # Display command history
                for i, cmd in enumerate(reversed(st.session_state.command_history)):
                    ai_indicator = "🤖" if cmd.get('ai_powered', False) else "🔄"
                    success_indicator = "✅" if cmd['success'] else "❌"
                    
                    with st.expander(f"{success_indicator} {ai_indicator} {cmd['timestamp']} - {cmd['request'][:50]}..."):
                        st.markdown(f"**Request:** {cmd['request']}")
                        st.markdown(f"**Command:** `{cmd['command']}`")
                        st.markdown(f"**Method:** {'🤖 Gemini AI' if cmd.get('ai_powered', False) else '🔄 Pattern Matching'}")
                        st.markdown(f"**Status:** {'✅ Success' if cmd['success'] else '❌ Failed'}")
                        if cmd['output']:
                            st.text_area("Output:", cmd['output'], height=100, key=f"history_output_{i}")
                
                # Clear history button
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("🗑️ Clear History", key="clear_history"):
                        st.session_state.command_history = []
                        st.success("Command history cleared!")
                        st.rerun()
                
                # Export history button
                with col2:
                    if st.button("💾 Export History", key="export_history"):
                        history_json = json.dumps(st.session_state.command_history, indent=2)
                        st.download_button(
                            label="📥 Download History JSON",
                            data=history_json,
                            file_name=f"dox_command_history_{int(time.time())}.json",
                            mime="application/json"
                        )
            else:
                st.info("No commands executed yet. Use the AI Command Executor to get started!")
                if not ai_assistant.ai_enabled:
                    st.info("💡 Add your Gemini API key in the sidebar to unlock advanced AI features!")

    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>🐳 <strong>DOX - The Docker Automation Tool</strong> - Enhanced with Gemini AI Flash 1.5</p>
        <p>{'🤖 AI Mode: Active' if ai_assistant.ai_enabled else '🔄 Fallback Mode: Active'} | Switch between modes using the sidebar to access different features!</p>
        <p style="font-size: 0.8rem; margin-top: 1rem;">
            💡 <strong>Tip:</strong> Use Pro Mode for {'AI-powered natural language commands' if ai_assistant.ai_enabled else 'pattern-based commands'} and {'intelligent' if ai_assistant.ai_enabled else 'template-based'} Dockerfile generation
        </p>
    </div>
    """, unsafe_allow_html=True)
