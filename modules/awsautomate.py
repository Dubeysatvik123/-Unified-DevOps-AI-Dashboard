#!/usr/bin/env python3
"""
EC2 Hand Gesture Control Application using Streamlit and CVZone
Control AWS EC2 instances with hand gestures using computer vision
"""

import streamlit as st
import cv2
import numpy as np
import boto3
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import threading
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# CVZone imports
try:
    from cvzone.HandTrackingModule import HandDetector
    from cvzone.ClassificationModule import Classifier
except ImportError:
    st.error("Please install CVZone: pip install cvzone")
    st.stop()

# AWS EC2 Configuration
@dataclass
class AWSConfig:
    access_key_id: str
    secret_access_key: str
    region_name: str = "us-east-1"

# Gesture Commands
class GestureCommand(Enum):
    START_INSTANCE = "start"
    STOP_INSTANCE = "stop" 
    RESTART_INSTANCE = "restart"
    LIST_INSTANCES = "list"
    NONE = "none"

@dataclass
class EC2Instance:
    instance_id: str
    name: str
    state: str
    instance_type: str
    public_ip: Optional[str]
    private_ip: Optional[str]
    launch_time: Optional[datetime]

class HandGestureDetector:
    """Hand gesture detection and command mapping"""
    
    def __init__(self):
        self.detector = HandDetector(detectionCon=0.8, maxHands=1)
        self.gesture_history = []
        self.gesture_threshold = 5  # Frames to confirm gesture
        self.last_command_time = 0
        self.command_cooldown = 3  # Seconds between commands
        
        # Gesture mappings
        self.gesture_commands = {
            "thumbs_up": GestureCommand.START_INSTANCE,
            "thumbs_down": GestureCommand.STOP_INSTANCE,
            "fist": GestureCommand.RESTART_INSTANCE,
            "open_palm": GestureCommand.LIST_INSTANCES,
            "peace": GestureCommand.NONE
        }
    
    def detect_gesture(self, img) -> Tuple[str, float]:
        """Detect hand gesture from image"""
        hands, img = self.detector.findHands(img, draw=True)
        
        if not hands:
            return "none", 0.0
        
        hand = hands[0]
        fingers = self.detector.fingersUp(hand)
        
        # Gesture recognition logic
        gesture = self._classify_gesture(fingers)
        confidence = self._calculate_confidence(fingers)
        
        return gesture, confidence
    
    def _classify_gesture(self, fingers: List[int]) -> str:
        """Classify gesture based on finger positions"""
        # fingers = [thumb, index, middle, ring, pinky]
        
        # Thumbs up: thumb up, others down
        if fingers == [1, 0, 0, 0, 0]:
            return "thumbs_up"
        
        # Thumbs down: thumb down, others up (approximation)
        if fingers == [0, 1, 1, 1, 1]:
            return "thumbs_down"
        
        # Fist: all fingers down
        if fingers == [0, 0, 0, 0, 0]:
            return "fist"
        
        # Open palm: all fingers up
        if fingers == [1, 1, 1, 1, 1]:
            return "open_palm"
        
        # Peace sign: index and middle up
        if fingers == [0, 1, 1, 0, 0]:
            return "peace"
        
        return "none"
    
    def _calculate_confidence(self, fingers: List[int]) -> float:
        """Calculate confidence score for gesture"""
        # Simple confidence based on clear finger positions
        return 0.9 if sum(fingers) != 2.5 else 0.5
    
    def get_stable_command(self, gesture: str, confidence: float) -> Optional[GestureCommand]:
        """Get stable command after confirming gesture over multiple frames"""
        current_time = time.time()
        
        # Add gesture to history
        if confidence > 0.7:
            self.gesture_history.append(gesture)
        
        # Keep only recent history
        if len(self.gesture_history) > self.gesture_threshold:
            self.gesture_history.pop(0)
        
        # Check if we have a stable gesture
        if len(self.gesture_history) >= self.gesture_threshold:
            most_common = max(set(self.gesture_history), key=self.gesture_history.count)
            
            # Check cooldown
            if current_time - self.last_command_time > self.command_cooldown:
                if most_common in self.gesture_commands:
                    self.last_command_time = current_time
                    self.gesture_history.clear()
                    return self.gesture_commands[most_common]
        
        return None

class EC2Manager:
    """AWS EC2 instance management"""
    
    def __init__(self, config: AWSConfig):
        self.config = config
        self.ec2_client = None
        self.ec2_resource = None
        self._initialize_aws_clients()
    
    def _initialize_aws_clients(self):
        """Initialize AWS clients"""
        try:
            self.ec2_client = boto3.client(
                'ec2',
                aws_access_key_id=self.config.access_key_id,
                aws_secret_access_key=self.config.secret_access_key,
                region_name=self.config.region_name
            )
            
            self.ec2_resource = boto3.resource(
                'ec2',
                aws_access_key_id=self.config.access_key_id,
                aws_secret_access_key=self.config.secret_access_key,
                region_name=self.config.region_name
            )
            
        except Exception as e:
            st.error(f"Failed to initialize AWS clients: {str(e)}")
    
    def list_instances(self) -> List[EC2Instance]:
        """List all EC2 instances"""
        try:
            response = self.ec2_client.describe_instances()
            instances = []
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    # Get instance name from tags
                    name = "N/A"
                    if 'Tags' in instance:
                        for tag in instance['Tags']:
                            if tag['Key'] == 'Name':
                                name = tag['Value']
                                break
                    
                    instances.append(EC2Instance(
                        instance_id=instance['InstanceId'],
                        name=name,
                        state=instance['State']['Name'],
                        instance_type=instance['InstanceType'],
                        public_ip=instance.get('PublicIpAddress'),
                        private_ip=instance.get('PrivateIpAddress'),
                        launch_time=instance.get('LaunchTime')
                    ))
            
            return instances
            
        except Exception as e:
            st.error(f"Failed to list instances: {str(e)}")
            return []
    
    def start_instance(self, instance_id: str) -> bool:
        """Start EC2 instance"""
        try:
            response = self.ec2_client.start_instances(InstanceIds=[instance_id])
            return response['ResponseMetadata']['HTTPStatusCode'] == 200
        except Exception as e:
            st.error(f"Failed to start instance {instance_id}: {str(e)}")
            return False
    
    def stop_instance(self, instance_id: str) -> bool:
        """Stop EC2 instance"""
        try:
            response = self.ec2_client.stop_instances(InstanceIds=[instance_id])
            return response['ResponseMetadata']['HTTPStatusCode'] == 200
        except Exception as e:
            st.error(f"Failed to stop instance {instance_id}: {str(e)}")
            return False
    
    def restart_instance(self, instance_id: str) -> bool:
        """Restart EC2 instance"""
        try:
            response = self.ec2_client.reboot_instances(InstanceIds=[instance_id])
            return response['ResponseMetadata']['HTTPStatusCode'] == 200
        except Exception as e:
            st.error(f"Failed to restart instance {instance_id}: {str(e)}")
            return False

class GestureControlApp:
    """Main application class"""
    
    def __init__(self):
        self.gesture_detector = HandGestureDetector()
        self.ec2_manager = None
        self.camera = None
        self.is_running = False
        self.command_history = []
        self.selected_instance = None
    
    def initialize_ec2_manager(self, config: AWSConfig):
        """Initialize EC2 manager with configuration"""
        self.ec2_manager = EC2Manager(config)
    
    def start_camera(self):
        """Start camera capture"""
        try:
            self.camera = cv2.VideoCapture(0)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            return True
        except Exception as e:
            st.error(f"Failed to start camera: {str(e)}")
            return False
    
    def stop_camera(self):
        """Stop camera capture"""
        if self.camera:
            self.camera.release()
            self.camera = None
    
    def process_frame(self) -> Tuple[np.ndarray, str, Optional[GestureCommand]]:
        """Process single camera frame"""
        if not self.camera:
            return None, "No camera", None
        
        ret, frame = self.camera.read()
        if not ret:
            return None, "Failed to read frame", None
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Detect gesture
        gesture, confidence = self.gesture_detector.detect_gesture(frame)
        
        # Get stable command
        command = self.gesture_detector.get_stable_command(gesture, confidence)
        
        # Add text overlay
        cv2.putText(frame, f"Gesture: {gesture} ({confidence:.2f})", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if command:
            cv2.putText(frame, f"Command: {command.value}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return frame, gesture, command
    
    def execute_command(self, command: GestureCommand) -> str:
        """Execute gesture command"""
        if not self.ec2_manager or not self.selected_instance:
            return "No EC2 manager or instance selected"
        
        result = ""
        instance_id = self.selected_instance
        
        if command == GestureCommand.START_INSTANCE:
            success = self.ec2_manager.start_instance(instance_id)
            result = f"Started instance {instance_id}" if success else "Failed to start instance"
        
        elif command == GestureCommand.STOP_INSTANCE:
            success = self.ec2_manager.stop_instance(instance_id)
            result = f"Stopped instance {instance_id}" if success else "Failed to stop instance"
        
        elif command == GestureCommand.RESTART_INSTANCE:
            success = self.ec2_manager.restart_instance(instance_id)
            result = f"Restarted instance {instance_id}" if success else "Failed to restart instance"
        
        elif command == GestureCommand.LIST_INSTANCES:
            result = "Refreshing instance list..."
        
        # Add to command history
        self.command_history.append({
            "timestamp": datetime.now(),
            "command": command.value,
            "instance_id": instance_id,
            "result": result
        })
        
        return result

def create_instance_chart(instances: List[EC2Instance]):
    """Create instance state distribution chart"""
    if not instances:
        return None
    
    state_counts = {}
    for instance in instances:
        state_counts[instance.state] = state_counts.get(instance.state, 0) + 1
    
    fig = px.pie(
        values=list(state_counts.values()),
        names=list(state_counts.keys()),
        title="EC2 Instance States",
        color_discrete_map={
            'running': '#28a745',
            'stopped': '#dc3545',
            'pending': '#ffc107',
            'stopping': '#fd7e14',
            'terminated': '#6c757d'
        }
    )
    return fig

def create_command_history_chart(command_history: List[Dict]):
    """Create command history timeline"""
    if not command_history:
        return None
    
    df = pd.DataFrame(command_history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    fig = px.timeline(
        df,
        x_start="timestamp",
        x_end="timestamp",
        y="command",
        color="command",
        title="Command History Timeline"
    )
    return fig

def run():
    """Main Streamlit application"""
    # Note: Page config is handled by the main app
    # st.set_page_config(
    #     page_title="EC2 Gesture Control",
    #     page_icon="👋",
    #     layout="wide"
    # )
    
    st.title("👋 EC2 Hand Gesture Control")
    st.markdown("Control your AWS EC2 instances using hand gestures!")
    
    # Initialize app
    if 'app' not in st.session_state:
        st.session_state.app = GestureControlApp()
    
    app = st.session_state.app
    
    # Sidebar configuration
    st.sidebar.header("⚙️ AWS Configuration")
    
    aws_access_key = st.sidebar.text_input("AWS Access Key ID", type="password")
    aws_secret_key = st.sidebar.text_input("AWS Secret Access Key", type="password")
    aws_region = st.sidebar.selectbox(
        "AWS Region",
        ["us-east-1", "us-west-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-southeast-1"]
    )
    
    # Gesture commands help
    st.sidebar.header("🤚 Gesture Commands")
    st.sidebar.markdown("""
    - **👍 Thumbs Up**: Start Instance
    - **👎 Thumbs Down**: Stop Instance  
    - **✊ Fist**: Restart Instance
    - **✋ Open Palm**: List Instances
    - **✌️ Peace**: No Action
    """)
    
    # Initialize EC2 manager
    if aws_access_key and aws_secret_key:
        if 'ec2_initialized' not in st.session_state:
            config = AWSConfig(
                access_key_id=aws_access_key,
                secret_access_key=aws_secret_key,
                region_name=aws_region
            )
            app.initialize_ec2_manager(config)
            st.session_state.ec2_initialized = True
            st.sidebar.success("✅ AWS configured!")
    else:
        st.sidebar.warning("⚠️ Please enter AWS credentials")
        st.warning("Please configure AWS credentials in the sidebar to continue.")
        return
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📹 Camera Feed")
        
        # Camera controls
        camera_col1, camera_col2 = st.columns(2)
        
        with camera_col1:
            if st.button("📷 Start Camera", type="primary"):
                if app.start_camera():
                    st.session_state.camera_active = True
                    st.success("Camera started!")
                else:
                    st.error("Failed to start camera")
        
        with camera_col2:
            if st.button("⏹️ Stop Camera"):
                app.stop_camera()
                st.session_state.camera_active = False
                st.info("Camera stopped")
        
        # Camera feed placeholder
        camera_placeholder = st.empty()
        
        # Gesture status
        gesture_status = st.empty()
        command_status = st.empty()
    
    with col2:
        st.header("🖥️ EC2 Instances")
        
        # Refresh instances
        if st.button("🔄 Refresh Instances"):
            if app.ec2_manager:
                with st.spinner("Loading instances..."):
                    st.session_state.instances = app.ec2_manager.list_instances()
        
        # Instance selection
        if 'instances' in st.session_state and st.session_state.instances:
            instances = st.session_state.instances
            
            instance_options = {
                f"{inst.name} ({inst.instance_id})": inst.instance_id 
                for inst in instances
            }
            
            selected = st.selectbox(
                "Select Instance to Control:",
                options=list(instance_options.keys())
            )
            
            if selected:
                app.selected_instance = instance_options[selected]
                
                # Show selected instance details
                selected_inst = next(
                    inst for inst in instances 
                    if inst.instance_id == app.selected_instance
                )
                
                st.info(f"""
                **Instance Details:**
                - ID: {selected_inst.instance_id}
                - State: {selected_inst.state}
                - Type: {selected_inst.instance_type}
                - Public IP: {selected_inst.public_ip or 'N/A'}
                """)
        
        # Manual controls
        st.header("🎮 Manual Controls")
        
        manual_col1, manual_col2 = st.columns(2)
        
        with manual_col1:
            if st.button("▶️ Start"):
                if app.selected_instance:
                    result = app.execute_command(GestureCommand.START_INSTANCE)
                    st.success(result)
        
        with manual_col2:
            if st.button("⏹️ Stop"):
                if app.selected_instance:
                    result = app.execute_command(GestureCommand.STOP_INSTANCE)
                    st.success(result)
        
        if st.button("🔄 Restart", use_container_width=True):
            if app.selected_instance:
                result = app.execute_command(GestureCommand.RESTART_INSTANCE)
                st.success(result)
    
    # Camera processing loop
    if st.session_state.get('camera_active', False):
        frame, gesture, command = app.process_frame()
        
        if frame is not None:
            # Convert BGR to RGB for Streamlit
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            camera_placeholder.image(frame_rgb, channels="RGB", use_column_width=True)
            
            # Update status
            gesture_status.info(f"Current Gesture: {gesture}")
            
            if command:
                result = app.execute_command(command)
                command_status.success(f"Command Executed: {command.value} - {result}")
                
                # Auto-refresh instances after command
                if app.ec2_manager:
                    st.session_state.instances = app.ec2_manager.list_instances()
    
    # Analytics section
    st.header("📊 Analytics")
    
    analytics_col1, analytics_col2 = st.columns(2)
    
    with analytics_col1:
        if 'instances' in st.session_state and st.session_state.instances:
            chart = create_instance_chart(st.session_state.instances)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
    
    with analytics_col2:
        if app.command_history:
            history_chart = create_command_history_chart(app.command_history)
            if history_chart:
                st.plotly_chart(history_chart, use_container_width=True)
    
    # Instance table
    if 'instances' in st.session_state and st.session_state.instances:
        st.header("📋 Instance Details")
        
        instance_data = []
        for inst in st.session_state.instances:
            instance_data.append({
                "Name": inst.name,
                "Instance ID": inst.instance_id,
                "State": inst.state,
                "Type": inst.instance_type,
                "Public IP": inst.public_ip or "N/A",
                "Private IP": inst.private_ip or "N/A",
                "Launch Time": inst.launch_time.strftime("%Y-%m-%d %H:%M:%S") if inst.launch_time else "N/A"
            })
        
        df = pd.DataFrame(instance_data)
        st.dataframe(df, use_container_width=True)
    
    # Command history
    if app.command_history:
        st.header("📜 Command History")
        
        history_data = []
        for cmd in app.command_history[-10:]:  # Last 10 commands
            history_data.append({
                "Timestamp": cmd["timestamp"].strftime("%H:%M:%S"),
                "Command": cmd["command"],
                "Instance ID": cmd["instance_id"],
                "Result": cmd["result"]
            })
        
        history_df = pd.DataFrame(history_data)
        st.dataframe(history_df, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("Made with ❤️ using Streamlit, CVZone, and AWS SDK")

if __name__ == "__main__":
    run()