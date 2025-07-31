
import streamlit as st

def run():
    st.title("🤖 ML Mini Dashboard")
    st.markdown("Welcome to the Machine Learning Dashboard!")
    
    # Display available ML modules
    st.subheader("📊 Available ML Modules")
    
    ml_modules = [
        {
            "name": "📈 ML Regression",
            "description": "Advanced regression analysis with data visualization and machine learning models",
            "status": "✅ Available"
        }
    ]
    
    for module in ml_modules:
        with st.expander(f"{module['name']} - {module['status']}"):
            st.write(module['description'])
            st.info("Select this module from the sidebar to access it directly.")
    
    st.markdown("---")
    st.markdown("### 🎯 How to Use")
    st.markdown("""
    1. **Choose a Module**: Select any ML module from the sidebar navigation
    2. **Explore Features**: Each module provides interactive tools and visualizations
    3. **Run Analysis**: Use the built-in datasets or upload your own data
    4. **View Results**: Get detailed insights and predictions
    """)
