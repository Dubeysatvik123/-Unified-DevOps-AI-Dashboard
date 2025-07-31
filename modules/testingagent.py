#!/usr/bin/env python3
"""
Multi-Agent Code Analysis Streamlit Application using LangChain and Groq
Analyzes single files or entire directories with multiple specialized agents
"""

import os
import re
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import mimetypes
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# LangChain imports
try:
    from langchain_groq import ChatGroq
except ImportError:
    try:
        from langchain_community.chat_models.groq import ChatGroq
    except ImportError:
        # Fallback for older versions
        from langchain_community.llms import Groq as ChatGroq

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

# Configuration
@dataclass
class Config:
    groq_api_key: str
    model_name: str = "llama-3.1-8b-instant"
    
    max_file_size_mb: float = 10.0
    supported_extensions: Tuple[str, ...] = (
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
        '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
        '.html', '.css', '.sql', '.sh', '.bash', '.yaml', '.yml', '.json',
        '.xml', '.md', '.txt', '.cfg', '.ini', '.toml'
    )

class AnalysisType(Enum):
    SINGLE_FILE = "single_file"
    DIRECTORY = "directory"
    ERROR = "error"

@dataclass
class FileInfo:
    path: Path
    size_bytes: int
    extension: str
    is_supported: bool
    content: Optional[str] = None
    error: Optional[str] = None

class FilePathExtractor:
    """Extracts and resolves file/directory paths from natural language"""
    
    def __init__(self):
        # Comprehensive regex patterns for different path formats
        self.path_patterns = [
            # Quoted paths (single/double quotes)
            r'["\']([^"\']+(?:\.[\w]+|/[\w\-\./]*)?)["\']',
            # Unquoted absolute paths
            r'(?:^|\s)(/[^\s]+(?:\.[\w]+|/[\w\-\./]*)?)',
            # Unquoted relative paths with extensions
            r'(?:^|\s)((?:\.{1,2}/)?[\w\-\./]+\.[\w]+)',
            # Unquoted directory paths
            r'(?:^|\s)((?:\.{1,2}/)?[\w\-\./]+/)',
            # Home directory paths
            r'(?:^|\s)(~[^\s]*)',
            # Windows paths
            r'([A-Za-z]:[\\\/][^\s]*)',
        ]
    
    def extract_paths(self, text: str) -> List[str]:
        """Extract all potential file/directory paths from text"""
        paths = []
        
        for pattern in self.path_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            if isinstance(matches[0] if matches else None, tuple):
                paths.extend([match for match in matches if match])
            else:
                paths.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_paths = []
        for path in paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)
        
        return unique_paths
    
    def resolve_path(self, path_str: str) -> Optional[Path]:
        """Resolve path string to absolute Path object"""
        try:
            # Expand user home directory
            if path_str.startswith('~'):
                path_str = os.path.expanduser(path_str)
            
            # Convert to Path and resolve
            path = Path(path_str).resolve()
            
            # Validate path exists
            if path.exists():
                return path
            else:
                st.warning(f"Path does not exist: {path}")
                return None
                
        except Exception as e:
            st.error(f"Error resolving path '{path_str}': {e}")
            return None

class FileScanner:
    """Scans files and directories, collecting supported code files"""
    
    def __init__(self, config: Config):
        self.config = config
        self.max_file_size = config.max_file_size_mb * 1024 * 1024  # Convert to bytes
    
    def is_supported_file(self, path: Path) -> bool:
        """Check if file extension is supported"""
        return path.suffix.lower() in self.config.supported_extensions
    
    def is_binary_file(self, path: Path) -> bool:
        """Check if file is binary using mime type"""
        try:
            mime_type, _ = mimetypes.guess_type(str(path))
            if mime_type and mime_type.startswith('text'):
                return False
            
            # Try reading first few bytes to detect binary
            with open(path, 'rb') as f:
                chunk = f.read(8192)
                return b'\x00' in chunk
        except:
            return True
    
    def read_file_content(self, path: Path) -> Tuple[Optional[str], Optional[str]]:
        """Read file content with error handling"""
        try:
            if path.stat().st_size > self.max_file_size:
                return None, f"File too large: {path.stat().st_size / 1024 / 1024:.2f}MB"
            
            if self.is_binary_file(path):
                return None, "Binary file detected"
            
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(), None
                
        except Exception as e:
            return None, f"Error reading file: {str(e)}"
    
    def scan_file(self, path: Path) -> FileInfo:
        """Scan a single file"""
        try:
            stat = path.stat()
            content, error = self.read_file_content(path) if self.is_supported_file(path) else (None, "Unsupported file type")
            
            return FileInfo(
                path=path,
                size_bytes=stat.st_size,
                extension=path.suffix,
                is_supported=self.is_supported_file(path),
                content=content,
                error=error
            )
        except Exception as e:
            return FileInfo(
                path=path,
                size_bytes=0,
                extension=path.suffix,
                is_supported=False,
                error=f"Failed to scan file: {str(e)}"
            )
    
    def scan_directory(self, dir_path: Path, max_files: int = 1000) -> List[FileInfo]:
        """Recursively scan directory for supported files"""
        files = []
        processed = 0
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            all_items = list(dir_path.rglob('*'))
            total_items = len([item for item in all_items if item.is_file()])
            
            for i, item in enumerate(all_items):
                if processed >= max_files:
                    st.warning(f"Reached maximum file limit ({max_files})")
                    break
                
                if item.is_file():
                    # Skip hidden files and common ignore patterns
                    if any(part.startswith('.') for part in item.parts):
                        continue
                    
                    if any(ignore in str(item) for ignore in ['__pycache__', 'node_modules', '.git']):
                        continue
                    
                    file_info = self.scan_file(item)
                    files.append(file_info)
                    processed += 1
                    
                    # Update progress
                    progress = min(processed / min(max_files, total_items), 1.0)
                    progress_bar.progress(progress)
                    status_text.text(f"Scanning: {item.name} ({processed}/{min(max_files, total_items)})")
                    
        except Exception as e:
            st.error(f"Error scanning directory {dir_path}: {e}")
        
        progress_bar.empty()
        status_text.empty()
        return files

class AnalysisAgent:
    """Base class for specialized analysis agents"""
    
    def __init__(self, name: str, role: str, llm: ChatGroq):
        self.name = name
        self.role = role
        self.llm = llm
    
    async def analyze(self, files: List[FileInfo], context: Dict[str, Any]) -> Dict[str, Any]:
        """Override in subclasses"""
        raise NotImplementedError

class CodeQualityAgent(AnalysisAgent):
    """Agent focused on code quality, style, and best practices"""
    
    def __init__(self, llm: ChatGroq):
        super().__init__("CodeQualityAgent", "Code Quality Analyst", llm)
    
    async def analyze(self, files: List[FileInfo], context: Dict[str, Any]) -> Dict[str, Any]:
        supported_files = [f for f in files if f.is_supported and f.content]
        
        if not supported_files:
            return {"error": "No supported files to analyze"}
        
        prompt = f"""
        As a Code Quality Analyst, analyze the following code files for:
        - Code style and formatting issues
        - Best practices adherence
        - Potential bugs or issues
        - Code complexity assessment
        - Maintainability concerns
        
        Files to analyze ({len(supported_files)} files):
        """
        
        for file_info in supported_files[:10]:  # Limit to first 10 files
            prompt += f"\n\nFile: {file_info.path}\n"
            prompt += f"Extension: {file_info.extension}\n"
            prompt += f"Size: {file_info.size_bytes} bytes\n"
            prompt += f"Content:\n```{file_info.extension[1:]}\n{file_info.content[:2000]}\n```\n"
        
        prompt += "\n\nProvide a structured analysis with specific recommendations."
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return {
                "agent": self.name,
                "analysis": response.content,
                "files_analyzed": len(supported_files),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            # Try synchronous call if async fails
            try:
                response = self.llm.invoke([HumanMessage(content=prompt)])
                return {
                    "agent": self.name,
                    "analysis": response.content,
                    "files_analyzed": len(supported_files),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e2:
                return {"error": f"Analysis failed: {str(e)} / {str(e2)}"}

class SecurityAgent(AnalysisAgent):
    """Agent focused on security vulnerabilities and concerns"""
    
    def __init__(self, llm: ChatGroq):
        super().__init__("SecurityAgent", "Security Analyst", llm)
    
    async def analyze(self, files: List[FileInfo], context: Dict[str, Any]) -> Dict[str, Any]:
        supported_files = [f for f in files if f.is_supported and f.content]
        
        if not supported_files:
            return {"error": "No supported files to analyze"}
        
        prompt = f"""
        As a Security Analyst, analyze the following code files for:
        - Security vulnerabilities (SQL injection, XSS, etc.)
        - Insecure coding practices
        - Hardcoded secrets or credentials
        - Input validation issues
        - Authentication/authorization flaws
        - Data exposure risks
        
        Files to analyze ({len(supported_files)} files):
        """
        
        for file_info in supported_files[:10]:
            prompt += f"\n\nFile: {file_info.path}\n"
            prompt += f"Content:\n```{file_info.extension[1:]}\n{file_info.content[:2000]}\n```\n"
        
        prompt += "\n\nProvide a security assessment with risk levels and remediation suggestions."
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return {
                "agent": self.name,
                "analysis": response.content,
                "files_analyzed": len(supported_files),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            # Try synchronous call if async fails
            try:
                response = self.llm.invoke([HumanMessage(content=prompt)])
                return {
                    "agent": self.name,
                    "analysis": response.content,
                    "files_analyzed": len(supported_files),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e2:
                return {"error": f"Security analysis failed: {str(e)} / {str(e2)}"}

class ArchitectureAgent(AnalysisAgent):
    """Agent focused on code architecture and design patterns"""
    
    def __init__(self, llm: ChatGroq):
        super().__init__("ArchitectureAgent", "Architecture Analyst", llm)
    
    async def analyze(self, files: List[FileInfo], context: Dict[str, Any]) -> Dict[str, Any]:
        supported_files = [f for f in files if f.is_supported and f.content]
        
        if not supported_files:
            return {"error": "No supported files to analyze"}
        
        # Create project structure overview
        structure = {}
        for file_info in supported_files:
            parts = file_info.path.parts
            current = structure
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = f"{file_info.extension} ({file_info.size_bytes}B)"
        
        prompt = f"""
        As an Architecture Analyst, analyze the following project structure and code files for:
        - Overall architecture patterns
        - Design patterns usage
        - Code organization and modularity
        - Dependencies and coupling
        - Scalability considerations
        - Architectural anti-patterns
        
        Project Structure:
        {json.dumps(structure, indent=2)}
        
        Sample files ({min(5, len(supported_files))} of {len(supported_files)}):
        """
        
        for file_info in supported_files[:5]:
            prompt += f"\n\nFile: {file_info.path}\n"
            prompt += f"Content preview:\n```{file_info.extension[1:]}\n{file_info.content[:1500]}\n```\n"
        
        prompt += "\n\nProvide an architectural assessment with recommendations for improvement."
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return {
                "agent": self.name,
                "analysis": response.content,
                "project_structure": structure,
                "files_analyzed": len(supported_files),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            # Try synchronous call if async fails
            try:
                response = self.llm.invoke([HumanMessage(content=prompt)])
                return {
                    "agent": self.name,
                    "analysis": response.content,
                    "project_structure": structure,
                    "files_analyzed": len(supported_files),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e2:
                return {"error": f"Architecture analysis failed: {str(e)} / {str(e2)}"}

class MultiAgentCodeAnalyzer:
    """Main orchestrator for multi-agent code analysis"""
    
    def __init__(self, config: Config):
        self.config = config
        self.path_extractor = FilePathExtractor()
        self.file_scanner = FileScanner(config)
        
        # Initialize Groq LLM
        self.llm = ChatGroq(
            groq_api_key=config.groq_api_key,
            model_name=config.model_name,
            temperature=0.1
        )
        
        # Initialize agents
        self.agents = [
            CodeQualityAgent(self.llm),
            SecurityAgent(self.llm),
            ArchitectureAgent(self.llm)
        ]
    
    def determine_analysis_type(self, prompt: str) -> Tuple[AnalysisType, List[Path]]:
        """Determine if prompt contains file or directory paths"""
        extracted_paths = self.path_extractor.extract_paths(prompt)
        
        if not extracted_paths:
            return AnalysisType.ERROR, []
        
        resolved_paths = []
        for path_str in extracted_paths:
            resolved_path = self.path_extractor.resolve_path(path_str)
            if resolved_path:
                resolved_paths.append(resolved_path)
        
        if not resolved_paths:
            return AnalysisType.ERROR, []
        
        # Determine analysis type based on first valid path
        first_path = resolved_paths[0]
        if first_path.is_file():
            return AnalysisType.SINGLE_FILE, [first_path]
        elif first_path.is_dir():
            return AnalysisType.DIRECTORY, [first_path]
        else:
            return AnalysisType.ERROR, []
    
    async def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """Main analysis method"""
        # Determine analysis type and extract paths
        analysis_type, paths = self.determine_analysis_type(prompt)
        
        if analysis_type == AnalysisType.ERROR:
            return {
                "error": "No valid file or directory paths found in prompt",
                "extracted_paths": self.path_extractor.extract_paths(prompt)
            }
        
        # Scan files
        all_files = []
        for path in paths:
            if analysis_type == AnalysisType.SINGLE_FILE:
                st.info(f"📄 Analyzing single file: {path}")
                file_info = self.file_scanner.scan_file(path)
                all_files.append(file_info)
            else:  # DIRECTORY
                st.info(f"📁 Scanning directory: {path}")
                dir_files = self.file_scanner.scan_directory(path)
                all_files.extend(dir_files)
        
        # Filter supported files
        supported_files = [f for f in all_files if f.is_supported and f.content]
        st.success(f"✅ Found {len(supported_files)} supported files out of {len(all_files)} total")
        
        # Run multi-agent analysis
        st.info("🤖 Running multi-agent analysis...")
        analysis_results = []
        
        context = {
            "analysis_type": analysis_type.value,
            "total_files": len(all_files),
            "supported_files": len(supported_files),
            "paths": [str(p) for p in paths]
        }
        
        # Create progress bar for agents
        agent_progress = st.progress(0)
        agent_status = st.empty()
        
        # Run agents sequentially with progress updates
        for i, agent in enumerate(self.agents):
            agent_status.text(f"Running {agent.name}...")
            try:
                result = await agent.analyze(all_files, context)
                analysis_results.append(result)
            except Exception as e:
                analysis_results.append({"error": str(e)})
            
            agent_progress.progress((i + 1) / len(self.agents))
        
        agent_progress.empty()
        agent_status.empty()
        
        # Compile final report
        return {
            "analysis_type": analysis_type.value,
            "paths_analyzed": [str(p) for p in paths],
            "file_summary": {
                "total_files": len(all_files),
                "supported_files": len(supported_files),
                "file_types": list(set(f.extension for f in all_files if f.extension)),
                "total_size_mb": sum(f.size_bytes for f in all_files) / 1024 / 1024
            },
            "agent_analyses": analysis_results,
            "timestamp": datetime.now().isoformat(),
            "all_files": all_files  # Store for detailed view
        }

def create_file_summary_chart(file_summary):
    """Create file type distribution chart"""
    if not file_summary.get("file_types"):
        return None
    
    # Count files by extension
    ext_counts = {}
    for ext in file_summary["file_types"]:
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
    
    fig = px.pie(
        values=list(ext_counts.values()),
        names=list(ext_counts.keys()),
        title="File Type Distribution"
    )
    return fig

def create_file_size_chart(all_files):
    """Create file size distribution chart"""
    if not all_files:
        return None
    
    df = pd.DataFrame([
        {
            "file": f.path.name,
            "size_kb": f.size_bytes / 1024,
            "extension": f.extension,
            "supported": f.is_supported
        }
        for f in all_files[:20]  # Top 20 files
    ])
    
    fig = px.bar(
        df,
        x="file",
        y="size_kb",
        color="extension",
        title="File Sizes (Top 20 Files)",
        labels={"size_kb": "Size (KB)", "file": "File Name"}
    )
    fig.update_xaxis(tickangle=45)
    return fig

def run():
    """Main function to run the testing agent module"""
    main()

def main():
    """Main Streamlit application"""
    # Note: Page config is handled by the main app
    # st.set_page_config(
    #     page_title="Multi-Agent Code Analyzer",
    #     page_icon="🔍",
    #     layout="wide"
    # )
    
    st.title("🔍 Multi-Agent Code Analysis Tool")
    st.markdown("Analyze your code with specialized AI agents for quality, security, and architecture insights.")
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    # API Key input
    api_key = st.sidebar.text_input(
        "Groq API Key",
        type="password",
        help="Enter your Groq API key"
    )
    
    # Model selection
    model_name = st.sidebar.selectbox(
        "Model",
        ["llama-3.1-8b-instant", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"],
        help="Select the Groq model to use"
    )
    
    # File size limit
    max_file_size = st.sidebar.slider(
        "Max File Size (MB)",
        min_value=1.0,
        max_value=50.0,
        value=10.0,
        step=1.0
    )
    
    if not api_key:
        st.warning("⚠️ Please enter your Groq API key in the sidebar to continue.")
        st.info("You can get a free API key from [Groq Console](https://console.groq.com/)")
        return
    
    # Initialize configuration
    config = Config(
        groq_api_key=api_key,
        model_name=model_name,
        max_file_size_mb=max_file_size
    )
    
    # Initialize analyzer
    if 'analyzer' not in st.session_state:
        try:
            st.session_state.analyzer = MultiAgentCodeAnalyzer(config)
            st.sidebar.success("✅ Analyzer initialized!")
        except Exception as e:
            st.sidebar.error(f"❌ Failed to initialize analyzer: {e}")
            return
    
    # Main interface
    st.header("📝 Analysis Input")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        prompt = st.text_area(
            "Enter a prompt with file or directory paths:",
            placeholder="Examples:\n- Analyze /path/to/project\n- Review the code in ./src/main.py\n- Check ~/Documents/my-project for issues",
            height=100
        )
    
    with col2:
        st.markdown("**Examples:**")
        st.code('Analyze "/home/user/project"')
        st.code('Review "./src/main.py"')
        st.code('Check "~/my-app" for issues')
    
    # Analysis button
    if st.button("🚀 Start Analysis", type="primary", disabled=not prompt.strip()):
        if prompt.strip():
            try:
                # Run analysis
                with st.spinner("Running analysis..."):
                    results = asyncio.run(st.session_state.analyzer.analyze_prompt(prompt))
                
                # Store results in session state
                st.session_state.results = results
                
            except Exception as e:
                st.error(f"❌ Analysis failed: {e}")
                return
    
    # Display results
    if 'results' in st.session_state:
        results = st.session_state.results
        
        if "error" in results:
            st.error(f"❌ Analysis Error: {results['error']}")
            if "extracted_paths" in results:
                st.info(f"Extracted paths: {results['extracted_paths']}")
            return
        
        # Analysis summary
        st.header("📊 Analysis Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        summary = results["file_summary"]
        
        with col1:
            st.metric("Total Files", summary["total_files"])
        with col2:
            st.metric("Supported Files", summary["supported_files"])
        with col3:
            st.metric("File Types", len(summary["file_types"]))
        with col4:
            st.metric("Total Size", f"{summary['total_size_mb']:.2f} MB")
        
        # Charts
        st.header("📈 File Analysis Charts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            chart1 = create_file_summary_chart(summary)
            if chart1:
                st.plotly_chart(chart1, use_container_width=True)
        
        with col2:
            chart2 = create_file_size_chart(results.get("all_files", []))
            if chart2:
                st.plotly_chart(chart2, use_container_width=True)
        
        # Agent analyses
        st.header("🤖 Agent Analysis Results")
        
        for i, analysis in enumerate(results["agent_analyses"]):
            if "error" in analysis:
                st.error(f"❌ Agent {i+1} Error: {analysis['error']}")
                continue
            
            agent_name = analysis.get("agent", f"Agent {i+1}")
            
            with st.expander(f"🤖 {agent_name} - {analysis.get('files_analyzed', 'N/A')} files analyzed", expanded=True):
                st.markdown(analysis.get("analysis", "No analysis available"))
                
                if "project_structure" in analysis:
                    st.subheader("Project Structure")
                    st.json(analysis["project_structure"])
        
        # File details
        if st.checkbox("📁 Show File Details"):
            st.header("📁 File Details")
            
            all_files = results.get("all_files", [])
            if all_files:
                file_data = []
                for f in all_files:
                    file_data.append({
                        "File": str(f.path),
                        "Size (KB)": f.size_bytes / 1024,
                        "Extension": f.extension,
                        "Supported": "✅" if f.is_supported else "❌",
                        "Status": f.error if f.error else "OK"
                    })
                
                df = pd.DataFrame(file_data)
                st.dataframe(df, use_container_width=True)
        
        # Export results
        st.header("💾 Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Copy Results to Clipboard"):
                results_text = json.dumps(results, indent=2, default=str)
                st.code(results_text)
        
        with col2:
            results_json = json.dumps(results, indent=2, default=str)
            st.download_button(
                label="📥 Download Results (JSON)",
                data=results_json,
                file_name=f"code_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main()