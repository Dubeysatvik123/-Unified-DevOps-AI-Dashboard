import streamlit as st
import psutil
import smtplib
from email.message import EmailMessage
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw
import numpy as np
import os
import time
import re

# Handle optional imports with error handling
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

try:
    from googlesearch import search
    GOOGLE_SEARCH_AVAILABLE = True
except ImportError:
    GOOGLE_SEARCH_AVAILABLE = False

try:
    import cv2
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

# Try to import pywhatkit with display handling
try:
    # Set environment variable to prevent display issues
    os.environ.setdefault('DISPLAY', ':99')
    import pywhatkit
    PYWHATKIT_AVAILABLE = True
except Exception:
    PYWHATKIT_AVAILABLE = False

# Try to import social media libraries
try:
    from instabot import Bot
    INSTABOT_AVAILABLE = True
except ImportError:
    INSTABOT_AVAILABLE = False

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False

try:
    import facebook_sdk as fb
    FACEBOOK_AVAILABLE = True
except ImportError:
    FACEBOOK_AVAILABLE = False

# Set page configuration
# Note: Page config is handled by the main app
# st.set_page_config(
#     page_title="Python Multi-Task Dashboard",
#     page_icon="🐍",
#     layout="wide"
# )

# Main application
st.title("🐍 Python Multi-Task Dashboard")
st.write("A comprehensive collection of Python-based automation and utility tools.")

# Sidebar for tool selection
st.sidebar.title("🛠️ Tool Selection")
tool = st.sidebar.selectbox(
    "Choose a Tool",
    [
        "📊 Read RAM Usage",
        "📱 Send WhatsApp Message",
        "📧 Send Email",
        "💬 Send WhatsApp Without Contact",
        "📲 Send SMS",
        "📞 Make Phone Call",
        "🔍 Google Search",
        "📱 Post on Social Media",
        "🌐 Download Website Data",
        "🔒 Anonymous Email",
        "📋 Tuple vs List Comparison",
        "🎨 Create Digital Image",
        "👥 Swap Faces in Images"
    ]
)

# Tool 1: Read RAM Usage
if tool == "📊 Read RAM Usage":
    st.header("📊 System RAM Usage Monitor")
    st.write("Real-time system memory usage statistics using psutil.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Check RAM Usage", type="primary"):
            try:
                ram = psutil.virtual_memory()
                
                # Display metrics
                st.metric("Total RAM", f"{ram.total / (1024 ** 3):.2f} GB")
                st.metric("Used RAM", f"{ram.used / (1024 ** 3):.2f} GB")
                st.metric("Free RAM", f"{ram.free / (1024 ** 3):.2f} GB")
                st.metric("RAM Usage", f"{ram.percent}%")
                
                # Progress bar
                st.progress(ram.percent / 100)
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    with col2:
        if st.button("📈 Detailed System Info"):
            try:
                # CPU info
                st.subheader("🖥️ CPU Information")
                st.write(f"CPU Count: {psutil.cpu_count()}")
                st.write(f"CPU Usage: {psutil.cpu_percent()}%")
                
                # Disk info
                disk = psutil.disk_usage('/')
                st.subheader("💾 Disk Information")
                st.write(f"Total Disk: {disk.total / (1024 ** 3):.2f} GB")
                st.write(f"Used Disk: {disk.used / (1024 ** 3):.2f} GB")
                st.write(f"Free Disk: {disk.free / (1024 ** 3):.2f} GB")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Tool 2: Send WhatsApp Message
elif tool == "📱 Send WhatsApp Message":
    st.header("📱 WhatsApp Message Sender")
    
    if not PYWHATKIT_AVAILABLE:
        st.error("⚠️ PyWhatKit is not available or has display connection issues.")
        st.info("💡 **Solutions:**\n- Install virtual display (Xvfb)\n- Set up proper X11 forwarding\n- Use alternative WhatsApp APIs like Twilio")
        
        # Provide alternative solution
        st.subheader("🔗 Alternative: WhatsApp Web Link Generator")
        phone = st.text_input("📞 Phone Number (with country code, e.g., +1234567890)")
        message = st.text_area("💬 Message Content")
        
        if st.button("🔗 Generate WhatsApp Link"):
            if phone and message:
                clean_phone = re.sub(r'[^\d+]', '', phone)
                encoded_message = requests.utils.quote(message)
                whatsapp_url = f"https://wa.me/{clean_phone.lstrip('+')}?text={encoded_message}"
                
                st.success("✅ WhatsApp link generated!")
                st.markdown(f"🔗 [**Click here to send message**]({whatsapp_url})")
                st.code(whatsapp_url)
            else:
                st.warning("⚠️ Please enter phone number and message.")
    else:
        st.write("Send a WhatsApp message using pywhatkit. Ensure WhatsApp Web is open in your browser.")
        
        phone = st.text_input("📞 Phone Number (with country code, e.g., +1234567890)")
        message = st.text_input("💬 Message")
        
        col1, col2 = st.columns(2)
        with col1:
            hour = st.number_input("🕐 Hour (24-hour format)", min_value=0, max_value=23, step=1)
        with col2:
            minute = st.number_input("⏱️ Minute", min_value=0, max_value=59, step=1)
        
        if st.button("📤 Send WhatsApp Message"):
            if phone and message:
                try:
                    with st.spinner("Scheduling message..."):
                        pywhatkit.sendwhatmsg(phone, message, hour, minute)
                    st.success("✅ Message scheduled successfully!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("⚠️ Please enter a phone number and message.")

# Tool 3: Send Email
elif tool == "📧 Send Email":
    st.header("📧 Email Sender")
    st.write("Send emails using SMTP. Works with Gmail, Outlook, and other providers.")
    
    with st.expander("📋 Email Configuration"):
        sender_email = st.text_input("📧 Your Email Address")
        password = st.text_input("🔐 Email Password (App Password recommended)", type="password")
        
        st.info("💡 **For Gmail users:** Use App Passwords instead of your regular password for better security.")
    
    receiver_email = st.text_input("📨 Recipient Email")
    subject = st.text_input("📝 Subject")
    body = st.text_area("📄 Email Body", height=200)
    
    if st.button("📤 Send Email", type="primary"):
        if sender_email and password and receiver_email and subject and body:
            try:
                with st.spinner("Sending email..."):
                    msg = EmailMessage()
                    msg.set_content(body)
                    msg['Subject'] = subject
                    msg['From'] = sender_email
                    msg['To'] = receiver_email
                    
                    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                        server.login(sender_email, password)
                        server.send_message(msg)
                st.success("✅ Email sent successfully!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ Please fill in all fields.")

# Tool 4: Send WhatsApp Without Contact
elif tool == "💬 Send WhatsApp Without Contact":
    st.header("💬 WhatsApp via Twilio API")
    
    if not TWILIO_AVAILABLE:
        st.error("⚠️ Twilio library is not installed.")
        st.code("pip install twilio")
    else:
        st.write("Send WhatsApp messages using Twilio API (no contact saving required).")
        
        with st.expander("🔧 Twilio Configuration"):
            account_sid = st.text_input("🆔 Twilio Account SID", type="password")
            auth_token = st.text_input("🔑 Twilio Auth Token", type="password")
            twilio_number = st.text_input("📱 Twilio Phone Number")
        
        recipient_number = st.text_input("📞 Recipient Phone Number (with country code)")
        message = st.text_area("💬 Message")
        
        if st.button("📤 Send WhatsApp"):
            if all([account_sid, auth_token, twilio_number, recipient_number, message]):
                try:
                    with st.spinner("Sending WhatsApp message..."):
                        client = Client(account_sid, auth_token)
                        message_obj = client.messages.create(
                            from_=f"whatsapp:{twilio_number}",
                            body=message,
                            to=f"whatsapp:{recipient_number}"
                        )
                    st.success(f"✅ Message sent! SID: {message_obj.sid}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("⚠️ Please fill in all fields.")

# Tool 5: Send SMS
elif tool == "📲 Send SMS":
    st.header("📲 SMS Sender")
    
    if not TWILIO_AVAILABLE:
        st.error("⚠️ Twilio library is not installed.")
        st.code("pip install twilio")
    else:
        st.write("Send SMS messages using Twilio API.")
        
        with st.expander("🔧 Twilio Configuration"):
            account_sid = st.text_input("🆔 Twilio Account SID", type="password")
            auth_token = st.text_input("🔑 Twilio Auth Token", type="password")
            twilio_number = st.text_input("📱 Twilio Phone Number")
        
        recipient_number = st.text_input("📞 Recipient Phone Number (with country code)")
        message = st.text_area("💬 SMS Message")
        
        if st.button("📤 Send SMS"):
            if all([account_sid, auth_token, twilio_number, recipient_number, message]):
                try:
                    with st.spinner("Sending SMS..."):
                        client = Client(account_sid, auth_token)
                        message_obj = client.messages.create(
                            from_=twilio_number,
                            body=message,
                            to=recipient_number
                        )
                    st.success(f"✅ SMS sent! SID: {message_obj.sid}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("⚠️ Please fill in all fields.")

# Tool 6: Make Phone Call
elif tool == "📞 Make Phone Call":
    st.header("📞 Phone Call Initiator")
    
    if not TWILIO_AVAILABLE:
        st.error("⚠️ Twilio library is not installed.")
        st.code("pip install twilio")
    else:
        st.write("Initiate phone calls using Twilio API.")
        
        with st.expander("🔧 Twilio Configuration"):
            account_sid = st.text_input("🆔 Twilio Account SID", type="password")
            auth_token = st.text_input("🔑 Twilio Auth Token", type="password")
            twilio_number = st.text_input("📱 Twilio Phone Number")
        
        recipient_number = st.text_input("📞 Recipient Phone Number (with country code)")
        
        if st.button("📞 Make Call"):
            if all([account_sid, auth_token, twilio_number, recipient_number]):
                try:
                    with st.spinner("Initiating call..."):
                        client = Client(account_sid, auth_token)
                        call = client.calls.create(
                            twiml='<Response><Say>Hello from Python Dashboard</Say></Response>',
                            from_=twilio_number,
                            to=recipient_number
                        )
                    st.success(f"✅ Call initiated! SID: {call.sid}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("⚠️ Please fill in all fields.")

# Tool 7: Google Search
elif tool == "🔍 Google Search":
    st.header("🔍 Google Search Tool")
    
    if not GOOGLE_SEARCH_AVAILABLE:
        st.error("⚠️ Google Search library is not installed.")
        st.code("pip install googlesearch-python")
    else:
        st.write("Perform Google searches and display results.")
        
        query = st.text_input("🔍 Search Query")
        num_results = st.slider("📊 Number of Results", min_value=1, max_value=20, value=5)
        
        if st.button("🔍 Search"):
            if query:
                try:
                    with st.spinner("Searching..."):
                        results = list(search(query, num_results=num_results))
                    
                    st.success(f"✅ Found {len(results)} results:")
                    for i, result in enumerate(results, 1):
                        st.write(f"**{i}.** {result}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("⚠️ Please enter a search query.")

# Tool 8: Post on Social Media
elif tool == "📱 Post on Social Media":
    st.header("📱 Social Media Poster")
    st.write("Post content to Instagram, X (Twitter), or Facebook.")
    
    platform = st.selectbox("🎯 Select Platform", ["Instagram", "X (Twitter)", "Facebook"])
    message = st.text_area("📝 Post Content", height=150)
    
    if platform == "Instagram":
        if not INSTABOT_AVAILABLE:
            st.error("⚠️ Instagram bot library is not installed.")
            st.code("pip install instabot")
        else:
            username = st.text_input("👤 Instagram Username")
            password = st.text_input("🔐 Instagram Password", type="password")
            if st.button("📤 Post to Instagram"):
                st.warning("📷 Instagram posting requires image files. This is a text-only demo.")
                if username and password and message:
                    st.info("✅ Instagram bot would be initialized here.")
    
    elif platform == "X (Twitter)":
        if not TWEEPY_AVAILABLE:
            st.error("⚠️ Tweepy library is not installed.")
            st.code("pip install tweepy")
        else:
            with st.expander("🔧 X API Configuration"):
                consumer_key = st.text_input("🔑 Consumer Key", type="password")
                consumer_secret = st.text_input("🔐 Consumer Secret", type="password")
                access_token = st.text_input("🎫 Access Token", type="password")
                access_token_secret = st.text_input("🔒 Access Token Secret", type="password")
            
            if st.button("📤 Post to X"):
                if all([consumer_key, consumer_secret, access_token, access_token_secret, message]):
                    try:
                        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
                        auth.set_access_token(access_token, access_token_secret)
                        api = tweepy.API(auth)
                        api.update_status(message)
                        st.success("✅ Posted to X!")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    elif platform == "Facebook":
        if not FACEBOOK_AVAILABLE:
            st.error("⚠️ Facebook SDK library is not installed.")
            st.code("pip install facebook-sdk")
        else:
            access_token = st.text_input("🎫 Facebook Access Token", type="password")
            if st.button("📤 Post to Facebook"):
                if access_token and message:
                    try:
                        graph = fb.GraphAPI(access_token)
                        graph.put_object("me", "feed", message=message)
                        st.success("✅ Posted to Facebook!")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

# Tool 9: Download Website Data
elif tool == "🌐 Download Website Data":
    st.header("🌐 Website Content Downloader")
    st.write("Download and analyze website content using web scraping.")
    
    url = st.text_input("🔗 Website URL")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Download Content"):
            if url:
                try:
                    with st.spinner("Downloading website content..."):
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        response = requests.get(url, headers=headers, timeout=10)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.text, 'html.parser')
                        content = soup.get_text()
                    
                    st.success("✅ Content downloaded successfully!")
                    st.text_area("📄 Website Content", 
                               content[:2000] + "..." if len(content) > 2000 else content, 
                               height=400)
                    
                    # Show statistics
                    st.info(f"📊 **Stats:** {len(content)} characters, {len(content.split())} words")
                    
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Request Error: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("⚠️ Please enter a URL.")
    
    with col2:
        if st.button("🔍 Analyze Structure"):
            if url:
                try:
                    with st.spinner("Analyzing website structure..."):
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        response = requests.get(url, headers=headers, timeout=10)
                        soup = BeautifulSoup(response.text, 'html.parser')
                    
                    st.success("✅ Analysis complete!")
                    
                    # Show structure info
                    st.write(f"**Title:** {soup.title.string if soup.title else 'No title'}")
                    st.write(f"**Links:** {len(soup.find_all('a'))}")
                    st.write(f"**Images:** {len(soup.find_all('img'))}")
                    st.write(f"**Headings:** {len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))}")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Tool 10: Anonymous Email
elif tool == "🔒 Anonymous Email":
    st.header("🔒 Anonymous Email Sender")
    st.write("Send emails through relay services (Educational demonstration).")
    
    st.warning("⚠️ **Educational Purpose Only:** Configure a legitimate relay service.")
    
    with st.expander("🔧 SMTP Configuration"):
        smtp_server = st.text_input("🌐 SMTP Server")
        smtp_port = st.number_input("🔌 SMTP Port", min_value=1, max_value=65535, value=587)
        sender_email = st.text_input("📧 Sender Email (Relay)")
        api_key = st.text_input("🔑 API Key", type="password")
    
    receiver_email = st.text_input("📨 Recipient Email")
    subject = st.text_input("📝 Subject")
    body = st.text_area("📄 Email Body")
    
    if st.button("📤 Send Anonymous Email"):
        if all([smtp_server, sender_email, api_key, receiver_email, subject, body]):
            try:
                with st.spinner("Sending anonymous email..."):
                    msg = EmailMessage()
                    msg.set_content(body)
                    msg['Subject'] = subject
                    msg['From'] = sender_email
                    msg['To'] = receiver_email
                    
                    with smtplib.SMTP(smtp_server, smtp_port) as server:
                        server.starttls()
                        server.login(sender_email, api_key)
                        server.send_message(msg)
                st.success("✅ Anonymous email sent successfully!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ Please fill in all fields.")

# Tool 11: Tuple vs List Comparison
elif tool == "📋 Tuple vs List Comparison":
    st.header("📋 Python: Tuple vs List Comparison")
    st.write("Learn the technical differences between Tuples and Lists in Python.")
    
    # Comparison table
    st.subheader("📊 Feature Comparison")
    comparison_data = {
        "Feature": ["Mutability", "Syntax", "Performance", "Memory Usage", "Use Case", "Available Methods"],
        "Tuple": ["Immutable ❌", "( )", "Faster ⚡", "Less memory 💾", "Fixed data 📌", "Limited (2 methods)"],
        "List": ["Mutable ✅", "[ ]", "Slower 🐌", "More memory 💾💾", "Dynamic data 🔄", "Many methods (11+)"]
    }
    
    st.table(comparison_data)
    
    # Interactive examples
    st.subheader("🧪 Interactive Examples")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🔹 Tuple Example:**")
        st.code("""
# Creating a tuple
coordinates = (10, 20, 30)
print(coordinates)

# Accessing elements
print(coordinates[0])  # 10

# Trying to modify (will fail)
# coordinates[0] = 15  # Error!
        """)
        
        if st.button("🔍 Test Tuple Operations"):
            coordinates = (10, 20, 30)
            st.write(f"Tuple: {coordinates}")
            st.write(f"First element: {coordinates[0]}")
            st.write(f"Count of 20: {coordinates.count(20)}")
            st.write(f"Index of 30: {coordinates.index(30)}")
    
    with col2:
        st.write("**🔹 List Example:**")
        st.code("""
# Creating a list
numbers = [10, 20, 30]
print(numbers)

# Accessing elements
print(numbers[0])  # 10

# Modifying elements
numbers[0] = 15
numbers.append(40)
        """)
        
        if st.button("🔍 Test List Operations"):
            numbers = [10, 20, 30]
            st.write(f"Original list: {numbers}")
            numbers[0] = 15
            st.write(f"After modification: {numbers}")
            numbers.append(40)
            st.write(f"After append: {numbers}")
            st.write(f"Length: {len(numbers)}")

# Tool 12: Create Digital Image
elif tool == "🎨 Create Digital Image":
    st.header("🎨 Digital Image Generator")
    st.write("Create custom digital images using PIL and NumPy.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🖼️ Image Settings")
        width = st.slider("📏 Width", min_value=100, max_value=800, value=400)
        height = st.slider("📐 Height", min_value=100, max_value=800, value=400)
        
        pattern = st.selectbox("🎨 Pattern Type", [
            "Gradient", "Checkerboard", "Circles", "Random Noise"
        ])
    
    with col2:
        if st.button("🎨 Generate Image", type="primary"):
            try:
                with st.spinner("Creating image..."):
                    if pattern == "Gradient":
                        # Create gradient
                        array = np.zeros((height, width, 3), dtype=np.uint8)
                        for y in range(height):
                            for x in range(width):
                                array[y, x] = [x * 255 // width, y * 255 // height, (x + y) * 255 // (width + height)]
                    
                    elif pattern == "Checkerboard":
                        # Create checkerboard
                        array = np.zeros((height, width, 3), dtype=np.uint8)
                        square_size = 50
                        for y in range(height):
                            for x in range(width):
                                if ((x // square_size) + (y // square_size)) % 2:
                                    array[y, x] = [255, 255, 255]
                                else:
                                    array[y, x] = [0, 0, 0]
                    
                    elif pattern == "Circles":
                        # Create circles pattern
                        array = np.zeros((height, width, 3), dtype=np.uint8)
                        center_x, center_y = width // 2, height // 2
                        for y in range(height):
                            for x in range(width):
                                distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                                color_val = int((np.sin(distance * 0.1) + 1) * 127)
                                array[y, x] = [color_val, color_val, 255 - color_val]
                    
                    else:  # Random Noise
                        # Create random noise
                        array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
                    
                    img = Image.fromarray(array)
                
                st.success("✅ Image generated successfully!")
                st.image(img, caption=f"Generated {pattern} Image ({width}x{height})")
                
                # Optionally save to disk
                try:
                    filename = f"generated_{pattern.lower()}_{width}x{height}.png"
                    img.save(filename)
                    st.info(f"💾 Image saved as {filename}")
                except Exception as save_error:
                    st.warning(f"⚠️ Could not save to disk: {save_error}")
                    
            except Exception as e:
                st.error(f"❌ Error generating image: {str(e)}")

# Tool 13: Swap Faces in Images
elif tool == "👥 Swap Faces in Images":
    st.header("👥 Face Swap Tool")
    
    if not FACE_RECOGNITION_AVAILABLE:
        st.error("⚠️ Face recognition libraries are not installed.")
        st.code("pip install opencv-python face-recognition")
    else:
        st.write("Upload two images to swap faces using AI face detection.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📷 First Image")
            image1 = st.file_uploader("Upload First Image", type=["png", "jpg", "jpeg"], key="img1")
            if image1:
                st.image(image1, caption="Image 1", use_column_width=True)
        
        with col2:
            st.subheader("📷 Second Image")
            image2 = st.file_uploader("Upload Second Image", type=["png", "jpg", "jpeg"], key="img2")
            if image2:
                st.image(image2, caption="Image 2", use_column_width=True)
        
        if st.button("🔄 Swap Faces", type="primary"):
            if image1 and image2:
                try:
                    with st.spinner("🔍 Detecting faces and swapping..."):
                        # Create temporary file paths
                        import tempfile
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp1:
                            tmp1.write(image1.read())
                            temp_path1 = tmp1.name
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp2:
                            tmp2.write(image2.read())
                            temp_path2 = tmp2.name
                        
                        # Load images
                        img1 = face_recognition.load_image_file(temp_path1)
                        img2 = face_recognition.load_image_file(temp_path2)
                        
                        # Detect faces
                        face_locations1 = face_recognition.face_locations(img1)
                        face_locations2 = face_recognition.face_locations(img2)
                        
                        if len(face_locations1) == 0:
                            st.error("❌ No faces detected in the first image.")
                        elif len(face_locations2) == 0:
                            st.error("❌ No faces detected in the second image.")
                        else:
                            # Get face coordinates
                            top1, right1, bottom1, left1 = face_locations1[0]
                            top2, right2, bottom2, left2 = face_locations2[0]
                            
                            # Extract face regions
                            face1 = img1[top1:bottom1, left1:right1]
                            face2 = img2[top2:bottom2, left2:right2]
                            
                            # Resize faces to match
                            face1_resized = cv2.resize(face1, (right2 - left2, bottom2 - top2))
                            face2_resized = cv2.resize(face2, (right1 - left1, bottom1 - top1))
                            
                            # Create copies for swapping
                            result1 = img1.copy()
                            result2 = img2.copy()
                            
                            # Swap faces
                            result1[top1:bottom1, left1:right1] = face2_resized
                            result2[top2:bottom2, left2:right2] = face1_resized
                            
                            # Convert to PIL Images and display
                            result_img1 = Image.fromarray(result1)
                            result_img2 = Image.fromarray(result2)
                            
                            st.success("✅ Face swap completed!")
                            
                            # Display results
                            col1, col2 = st.columns(2)
                            with col1:
                                st.image(result_img1, caption="Swapped Image 1", use_column_width=True)
                            with col2:
                                st.image(result_img2, caption="Swapped Image 2", use_column_width=True)
                            
                            # Save results
                            try:
                                result_img1.save("face_swap_result1.jpg")
                                result_img2.save("face_swap_result2.jpg")
                                st.info("💾 Results saved as face_swap_result1.jpg and face_swap_result2.jpg")
                            except Exception as save_error:
                                st.warning(f"⚠️ Could not save results: {save_error}")
                        
                        # Clean up temporary files
                        try:
                            os.unlink(temp_path1)
                            os.unlink(temp_path2)
                        except:
                            pass
                            
                except Exception as e:
                    st.error(f"❌ Error processing images: {str(e)}")
            else:
                st.warning("⚠️ Please upload both images.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>🐍 <strong>Python Multi-Task Dashboard</strong> | 
        Built with Streamlit | 
        <a href='https://github.com' target='_blank'>GitHub</a></p>
    </div>
    """, 
    unsafe_allow_html=True
)

# Sidebar information
with st.sidebar:
    st.markdown("---")
    st.subheader("📊 System Info")
    try:
        ram = psutil.virtual_memory()
        st.metric("RAM Usage", f"{ram.percent}%")
        st.metric("Available RAM", f"{ram.available / (1024**3):.1f} GB")
    except:
        st.write("System info unavailable")
    
    st.markdown("---")
    st.subheader("📚 Library Status")
    
    libraries = {
        "PyWhatKit": PYWHATKIT_AVAILABLE,
        "Twilio": TWILIO_AVAILABLE,
        "Google Search": GOOGLE_SEARCH_AVAILABLE,
        "Face Recognition": FACE_RECOGNITION_AVAILABLE,
        "Instagram Bot": INSTABOT_AVAILABLE,
        "Tweepy": TWEEPY_AVAILABLE,
        "Facebook SDK": FACEBOOK_AVAILABLE
    }
    
    for lib, available in libraries.items():
        status = "✅" if available else "❌"
        st.write(f"{status} {lib}")
    
    st.markdown("---")
    st.info("💡 **Tip:** Install missing libraries to unlock more features!")

# Auto-refresh option
if st.sidebar.button("🔄 Refresh Page"):
    st.rerun()
