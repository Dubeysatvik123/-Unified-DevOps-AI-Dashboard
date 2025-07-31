import os
import subprocess
import json
import requests
import streamlit as st
from pathlib import Path
import shutil
from datetime import datetime
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_google_genai import ChatGoogleGenerativeAI

def run():
    # Configure Streamlit page
    # Note: Page config is handled by the main app
    # st.set_page_config(
    #     page_title="🤖 Agentic GitHub Automation",
    #     page_icon="🤖",
    #     layout="wide",
    #     initial_sidebar_state="expanded"
    # )

    # Initialize session state
    if 'github_username' not in st.session_state:
        st.session_state.github_username = ""
    if 'github_token' not in st.session_state:
        st.session_state.github_token = ""
    if 'gemini_api_key' not in st.session_state:
        st.session_state.gemini_api_key = ""
    if 'agent_executor' not in st.session_state:
        st.session_state.agent_executor = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'agent_thinking' not in st.session_state:
        st.session_state.agent_thinking = []

    def create_agent(github_username, github_token, gemini_api_key):
        """Create the LangChain agent with tools"""
        
        # Initialize LLM
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=gemini_api_key)
        
        # Set up headers for GitHub API
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        def analyze_folder(folder_path: str) -> str:
            try:
                files = []
                for root, _, filenames in os.walk(folder_path):
                    for filename in filenames:
                        if not filename.startswith("."):
                            files.append(os.path.relpath(os.path.join(root, filename), folder_path))
                
                if not files:
                    return f"The folder '{os.path.basename(folder_path)}' is empty."
                
                return f"The folder '{os.path.basename(folder_path)}' contains {len(files)} files: {files[:10]}{'...' if len(files) > 10 else ''}"
            except Exception as e:
                return f"Error analyzing folder: {str(e)}"

        def create_repo(repo_name: str) -> str:
            try:
                data = {
                    "name": repo_name,
                    "description": f"Auto-generated repository for {repo_name}",
                    "private": False,
                    "auto_init": False
                }
                response = requests.post("https://api.github.com/user/repos", headers=headers, json=data)
                if response.status_code == 201:
                    return f"SUCCESS: Repo '{repo_name}' created successfully"
                elif response.status_code == 422:
                    return f"INFO: Repo '{repo_name}' already exists"
                else:
                    return f"ERROR: Failed to create repo '{repo_name}': {response.text}"
            except Exception as e:
                return f"ERROR: Exception creating repo: {str(e)}"

        def push_to_github(local_path: str, repo_name: str) -> str:
            try:
                has_files = False
                for root, _, filenames in os.walk(local_path):
                    for filename in filenames:
                        if not filename.startswith("."):
                            has_files = True
                            break
                    if has_files:
                        break
                
                if not has_files:
                    return f"WARNING: No files to push in '{repo_name}'"
                
                repo_url = f"https://{github_token}@github.com/{github_username}/{repo_name}.git"
                
                # Clean up any existing git repo
                git_dir = os.path.join(local_path, '.git')
                if os.path.exists(git_dir):
                    shutil.rmtree(git_dir)
                
                # Initialize git repo
                subprocess.run(["git", "init"], cwd=local_path, check=True, capture_output=True)
                subprocess.run(["git", "add", "-A"], cwd=local_path, check=True, capture_output=True)
                
                # Check if there's anything to commit
                result = subprocess.run(["git", "status", "--porcelain"], cwd=local_path, capture_output=True, text=True)
                if not result.stdout.strip():
                    return f"WARNING: No changes to commit in '{repo_name}'"
                
                subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=local_path, check=True, capture_output=True)
                subprocess.run(["git", "branch", "-M", "main"], cwd=local_path, check=True, capture_output=True)
                subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=local_path, check=True, capture_output=True)
                subprocess.run(["git", "push", "-u", "origin", "main"], cwd=local_path, check=True, capture_output=True)
                
                return f"SUCCESS: Successfully pushed '{repo_name}' to GitHub"
            except subprocess.CalledProcessError as e:
                return f"ERROR: Git push failed for '{repo_name}': {str(e)}"
            except Exception as e:
                return f"ERROR: Exception pushing to GitHub: {str(e)}"

        def process_multiple_folders(parent_path: str) -> str:
            try:
                if not os.path.isdir(parent_path):
                    return f"ERROR: Invalid folder path '{parent_path}'"

                folders = [os.path.join(parent_path, f) for f in os.listdir(parent_path)
                           if os.path.isdir(os.path.join(parent_path, f)) and not f.startswith(".")]

                if not folders:
                    return f"WARNING: No subfolders found in '{parent_path}'"

                results = []
                results.append(f"Found {len(folders)} subfolders in '{parent_path}'")
                
                for folder in folders:
                    folder_name = os.path.basename(folder)
                    
                    analyze_result = analyze_folder(folder)
                    results.append(f"ANALYZE {folder_name}: {analyze_result}")
                    
                    if "is empty" in analyze_result:
                        results.append(f"SKIP {folder_name}: Empty folder")
                        continue
                    
                    create_result = create_repo(folder_name)
                    results.append(f"CREATE {folder_name}: {create_result}")
                    
                    push_result = push_to_github(folder, folder_name)
                    results.append(f"PUSH {folder_name}: {push_result}")
                
                return "\n".join(results)
            except Exception as e:
                return f"ERROR: Exception processing folders: {str(e)}"

        # Define tools
        tools = [
            Tool(
                name="analyze_folder",
                func=analyze_folder,
                description="Analyzes a folder's contents and returns file information. Input: folder_path (string)"
            ),
            Tool(
                name="create_repo",
                func=create_repo,
                description="Creates a GitHub repository. Input: repo_name (string)"
            ),
            Tool(
                name="push_to_github",
                func=push_to_github,
                description="Pushes a local folder to GitHub repository. Input: local_path (string), repo_name (string)"
            ),
            Tool(
                name="process_multiple_folders",
                func=process_multiple_folders,
                description="Processes all subfolders in a parent directory. Input: parent_path (string)"
            )
        ]

        # Create prompt template
        prompt_template = PromptTemplate.from_template("""
You are an intelligent GitHub automation agent. You can understand natural language commands and execute them using the available tools.

Available commands you can handle:
- "process folder <path>" - Process a single folder (analyze, create repo, push)
- "process all folders in <path>" - Process all subfolders in a directory
- "analyze <path>" - Just analyze a folder's contents
- "create repo <name>" - Create a GitHub repository
- "push <folder_path> to <repo_name>" - Push a folder to a repository

Always be helpful and execute the user's request using the appropriate tools.

You have access to these tools:
{tools}

Use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
{agent_scratchpad}
""")

        # Create agent
        agent = create_react_agent(llm, tools, prompt_template)
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True, 
            handle_parsing_errors=True, 
            max_iterations=10
        )
        
        return agent_executor

    def display_agent_thinking(agent_thinking):
        """Display the agent's thinking process"""
        if agent_thinking:
            with st.expander("🧠 Agent Thinking Process", expanded=False):
                for step in agent_thinking:
                    if "Thought:" in step:
                        st.info(f"💭 {step}")
                    elif "Action:" in step:
                        st.warning(f"⚡ {step}")
                    elif "Observation:" in step:
                        st.success(f"👀 {step}")
                    else:
                        st.text(step)

    # Header
    st.title("🤖 Agentic GitHub Automation")
    st.markdown("**Intelligent AI Agent for GitHub Repository Management**")
    st.markdown("Talk to the agent in natural language - it will understand and execute your GitHub automation tasks!")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Agent Configuration")
        
        github_username = st.text_input(
            "GitHub Username",
            value=st.session_state.github_username,
            help="Your GitHub username"
        )
        
        github_token = st.text_input(
            "GitHub Token",
            value=st.session_state.github_token,
            type="password",
            help="Your GitHub personal access token"
        )
        
        gemini_api_key = st.text_input(
            "Gemini API Key",
            value=st.session_state.gemini_api_key,
            type="password",
            help="Your Google Gemini API key"
        )
        
        # Update session state
        st.session_state.github_username = github_username
        st.session_state.github_token = github_token
        st.session_state.gemini_api_key = gemini_api_key
        
        # Initialize agent when credentials are provided
        if st.button("🚀 Initialize Agent"):
            if github_username and github_token and gemini_api_key:
                try:
                    with st.spinner("Initializing AI Agent..."):
                        st.session_state.agent_executor = create_agent(
                            github_username, github_token, gemini_api_key
                        )
                    st.success("✅ Agent initialized successfully!")
                except Exception as e:
                    st.error(f"❌ Failed to initialize agent: {str(e)}")
            else:
                st.error("❌ Please provide all required credentials")
        
        # Agent status
        if st.session_state.agent_executor:
            st.success("🤖 Agent is ready!")
        else:
            st.warning("⚠️ Agent not initialized")
        
        st.markdown("---")
        
        # Clear chat history
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.session_state.agent_thinking = []
            st.rerun()
        
        # Example commands
        st.markdown("### 💡 Example Commands")
        st.markdown("""
        - `process folder /path/to/my/project`
        - `analyze /home/user/code`
        - `create repo my-new-project`
        - `process all folders in /projects`
        - `push /local/folder to existing-repo`
        """)
    
    # Main chat interface
    st.markdown("### 💬 Chat with Your GitHub Agent")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for i, (user_msg, agent_msg, thinking) in enumerate(st.session_state.chat_history):
            # User message
            with st.chat_message("user"):
                st.write(user_msg)
            
            # Agent response
            with st.chat_message("assistant"):
                st.write(agent_msg)
                
                # Show thinking process if available
                if thinking:
                    with st.expander("🧠 Agent Thinking", expanded=False):
                        for step in thinking:
                            if "Thought:" in step:
                                st.info(f"💭 {step}")
                            elif "Action:" in step:
                                st.warning(f"⚡ {step}")
                            elif "Observation:" in step:
                                st.success(f"👀 {step}")
                            else:
                                st.text(step)
    
    # Chat input
    user_input = st.chat_input("Enter your command (e.g., 'process folder /path/to/my/project')")
    
    if user_input:
        if not st.session_state.agent_executor:
            st.error("❌ Please initialize the agent first using the sidebar")
        else:
            # Add user message to chat
            with st.chat_message("user"):
                st.write(user_input)
            
            # Process with agent
            with st.chat_message("assistant"):
                with st.spinner("🤖 Agent is thinking..."):
                    try:
                        # Capture agent's thinking process
                        thinking_steps = []
                        
                        # Execute agent
                        result = st.session_state.agent_executor.invoke({"input": user_input})
                        
                        # Display result
                        st.write(result['output'])
                        
                        # For now, we'll create a simplified thinking display
                        # In a full implementation, you'd capture the actual agent steps
                        thinking_steps = [
                            f"Thought: I need to process the command: {user_input}",
                            f"Action: Executing appropriate GitHub automation tools",
                            f"Observation: {result['output']}"
                        ]
                        
                        # Show thinking process
                        with st.expander("🧠 Agent Thinking", expanded=False):
                            for step in thinking_steps:
                                if "Thought:" in step:
                                    st.info(f"💭 {step}")
                                elif "Action:" in step:
                                    st.warning(f"⚡ {step}")
                                elif "Observation:" in step:
                                    st.success(f"👀 {step}")
                        
                        # Add to chat history
                        st.session_state.chat_history.append((
                            user_input, 
                            result['output'], 
                            thinking_steps
                        ))
                        
                    except Exception as e:
                        error_msg = f"❌ Error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.chat_history.append((
                            user_input, 
                            error_msg, 
                            []
                        ))
            
            st.rerun()
    
    # Instructions panel
    with st.expander("📖 How to Use the Agent", expanded=False):
        st.markdown("""
        ### 🚀 Getting Started
        1. **Configure Credentials**: Enter your GitHub username, token, and Gemini API key in the sidebar
        2. **Initialize Agent**: Click "Initialize Agent" to create your AI assistant
        3. **Chat Naturally**: Type commands in natural language
        
        ### 🎯 What the Agent Can Do
        - **Analyze Folders**: "analyze /path/to/folder"
        - **Create Repositories**: "create repo my-project"
        - **Process Single Folders**: "process folder /path/to/my/code"
        - **Batch Process**: "process all folders in /projects"
        - **Push to Existing Repos**: "push /local/folder to existing-repo"
        
        ### 🧠 Agent Intelligence
        The agent uses LangChain and Google's Gemini to understand your requests and:
        - Plan the sequence of actions needed
        - Execute GitHub API calls and Git operations
        - Provide detailed feedback on each step
        - Handle errors and edge cases intelligently
        
        ### 🔒 Security
        - All credentials are stored securely in session state
        - No data is permanently stored
        - Agent operations are logged for transparency
        """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            🤖 Agentic GitHub Automation | Powered by LangChain + Gemini AI
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    run()