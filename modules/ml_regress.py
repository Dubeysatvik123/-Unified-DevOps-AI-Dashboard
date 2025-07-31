import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import seaborn as sns
import matplotlib.pyplot as plt

# Note: Page config is handled by the main app
# st.set_page_config(
#     page_title="💰 Dowry Analytics Dashboard",
#     page_icon="📊",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .insight-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        margin: 1rem 0;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    .stSelectbox > div > div {
        background-color: #f8f9fa;
    }
    
    .prediction-result {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Load and prepare data
@st.cache_data
def load_data():
    # Sample data based on the provided dataset
    data = {
        'Job Title': ['Doctor', 'Software Engineer', 'Startup Founder', 'Teacher', 'IAS Officer', 
                     'Bank PO', 'Clerk', 'Government Officer'] * 8,
        'Monthly Salary': [124045, 31924, 76795, 87646, 82119, 135464, 52014, 180858,
                          155069, 54604, 170592, 173006, 158956, 179894, 141261, 110407,
                          58684, 130407, 55538, 184121, 136755, 67795, 85646, 99013,
                          170851, 82917, 84872, 53258, 189161, 60928, 197607, 59180,
                          156261, 73829, 37080, 185790, 21659, 21201, 124463, 185323,
                          140972, 130771, 77997, 111074, 53517, 93048, 77885, 61073,
                          158246, 124850, 169570, 44168, 47836, 134022, 123489, 134022] + [np.random.randint(20000, 200000) for _ in range(8)],
        'Education': ['MBBS', 'B.Tech', 'MBA', 'B.A.', 'M.A.', 'M.Sc', 'Ph.D'] * 9 + ['B.Tech'],
        'City Tier': ['Tier-1', 'Tier-2', 'Tier-3'] * 21 + ['Tier-1'],
        'Expected Dowry (INR)': [1433000, 611000, 1271000, 1078000, 2709000, 2175000, 966000, 3214000,
                                3699000, 1631000, 2866000, 1461000, 8161000, 5318000, 2816000, 2471000,
                                768000, 2426000, 1116000, 2438000, 3263000, 621000, 2486000, 3175000,
                                2810000, 1847000, 2524000, 1223000, 3812000, 860000, 3527000, 1484000,
                                1974000, 1287000, 858000, 2846000, 730000, 409000, 2934000, 3399000,
                                1612000, 2722000, 1446000, 2866000, 986000, 1596000, 1575000, 644000,
                                1993000, 2658000, 2699000, 997000, 371000, 2052000, 1609000, 2052000] + [np.random.randint(300000, 5000000) for _ in range(8)]
    }
    return pd.DataFrame(data)

def run():
    # Main function to run the ML regression module
    df = load_data()

    # Header
    st.markdown('<h1 class="main-header">💰 Dowry Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Comprehensive Analysis of Dowry Expectations Across Different Demographics</p>', unsafe_allow_html=True)

    # Sidebar
    st.sidebar.markdown("## 🎛️ Dashboard Controls")
    st.sidebar.markdown("---")

    # Analysis type selection
    analysis_type = st.sidebar.selectbox(
        "📊 Select Analysis Type",
        ["📈 Overview Dashboard", "🔍 Detailed Analysis", "🤖 Prediction Model", "📋 Data Explorer"]
    )

    if analysis_type == "📈 Overview Dashboard":
        # Key Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_dowry = df['Expected Dowry (INR)'].mean()
            st.markdown(f"""
            <div class="metric-card">
                <h3>₹{avg_dowry:,.0f}</h3>
                <p>Average Dowry</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            max_dowry = df['Expected Dowry (INR)'].max()
            st.markdown(f"""
            <div class="metric-card">
                <h3>₹{max_dowry:,.0f}</h3>
                <p>Highest Dowry</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            avg_salary = df['Monthly Salary'].mean()
            st.markdown(f"""
            <div class="metric-card">
                <h3>₹{avg_salary:,.0f}</h3>
                <p>Average Salary</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            total_records = len(df)
            st.markdown(f"""
            <div class="metric-card">
                <h3>{total_records}</h3>
                <p>Total Records</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Main visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💼 Dowry by Job Title")
            job_dowry = df.groupby('Job Title')['Expected Dowry (INR)'].mean().sort_values(ascending=True)
            fig_job = px.bar(
                x=job_dowry.values,
                y=job_dowry.index,
                orientation='h',
                color=job_dowry.values,
                color_continuous_scale='viridis',
                title="Average Dowry Expectations by Profession"
            )
            fig_job.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_job, use_container_width=True)
        
        with col2:
            st.subheader("🎓 Education vs Dowry")
            edu_dowry = df.groupby('Education')['Expected Dowry (INR)'].mean().sort_values(ascending=False)
            fig_edu = px.pie(
                values=edu_dowry.values,
                names=edu_dowry.index,
                color_discrete_sequence=px.colors.qualitative.Set3,
                title="Dowry Distribution by Education Level"
            )
            fig_edu.update_layout(height=400)
            st.plotly_chart(fig_edu, use_container_width=True)
        
        # Second row of visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏙️ City Tier Analysis")
            tier_stats = df.groupby('City Tier').agg({
                'Expected Dowry (INR)': ['mean', 'median', 'max'],
                'Monthly Salary': 'mean'
            }).round(0)
            
            tier_data = df.groupby('City Tier')['Expected Dowry (INR)'].mean().reset_index()
            fig_tier = px.bar(
                data_frame=tier_data,
                x='City Tier',
                y='Expected Dowry (INR)',
                color='Expected Dowry (INR)',
                color_continuous_scale='viridis',
                title="Average Dowry by City Tier"
            )
            fig_tier.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_tier, use_container_width=True)
            
            # Display tier statistics
            st.markdown("### 📊 Tier Statistics")
            st.dataframe(tier_stats, use_container_width=True)
        
        with col2:
            st.subheader("💰 Salary vs Dowry Correlation")
            fig_scatter = px.scatter(
                data_frame=df,
                x='Monthly Salary',
                y='Expected Dowry (INR)',
                color='Job Title',
                size='Expected Dowry (INR)',
                hover_data=['Education', 'City Tier'],
                title="Salary vs Dowry Relationship"
            )
            fig_scatter.update_layout(height=400)
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Correlation coefficient
            correlation = df['Monthly Salary'].corr(df['Expected Dowry (INR)'])
            st.metric("Correlation Coefficient", f"{correlation:.3f}")

    elif analysis_type == "🔍 Detailed Analysis":
        st.subheader("🔍 Detailed Analysis")
        
        # Detailed breakdowns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 💼 Job Title Analysis")
            job_analysis = df.groupby('Job Title').agg({
                'Expected Dowry (INR)': ['mean', 'median', 'std', 'count'],
                'Monthly Salary': 'mean'
            }).round(0)
            job_analysis.columns = ['Avg Dowry', 'Median Dowry', 'Std Dowry', 'Count', 'Avg Salary']
            st.dataframe(job_analysis, use_container_width=True)
        
        with col2:
            st.markdown("### 🎓 Education Analysis")
            edu_analysis = df.groupby('Education').agg({
                'Expected Dowry (INR)': ['mean', 'median', 'std', 'count'],
                'Monthly Salary': 'mean'
            }).round(0)
            edu_analysis.columns = ['Avg Dowry', 'Median Dowry', 'Std Dowry', 'Count', 'Avg Salary']
            st.dataframe(edu_analysis, use_container_width=True)
        
        # Advanced visualizations
        st.markdown("### 📊 Advanced Visualizations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Box plot for dowry distribution by job
            fig_box = px.box(
                data_frame=df,
                x='Job Title',
                y='Expected Dowry (INR)',
                color='Job Title',
                title="Dowry Distribution by Job Title"
            )
            fig_box.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig_box, use_container_width=True)
        
        with col2:
            # Violin plot for salary distribution
            fig_violin = px.violin(
                data_frame=df,
                x='City Tier',
                y='Monthly Salary',
                color='City Tier',
                title="Salary Distribution by City Tier"
            )
            fig_violin.update_layout(height=400)
            st.plotly_chart(fig_violin, use_container_width=True)
        
        # Heatmap of correlations
        st.markdown("### 🔥 Correlation Heatmap")
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        correlation_matrix = df[numeric_cols].corr()
        
        fig_heatmap = px.imshow(
            correlation_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale='RdBu',
            title="Feature Correlation Matrix"
        )
        fig_heatmap.update_layout(height=400)
        st.plotly_chart(fig_heatmap, use_container_width=True)

    elif analysis_type == "🤖 Prediction Model":
        st.subheader("🤖 Machine Learning Prediction Model")
        
        # Prepare data for ML
        df_ml = df.copy()
        
        # Encode categorical variables
        le_job = LabelEncoder()
        le_edu = LabelEncoder()
        le_city = LabelEncoder()
        
        df_ml['Job Title_encoded'] = le_job.fit_transform(df_ml['Job Title'])
        df_ml['Education_encoded'] = le_edu.fit_transform(df_ml['Education'])
        df_ml['City Tier_encoded'] = le_city.fit_transform(df_ml['City Tier'])
        
        # Select features
        features = ['Monthly Salary', 'Job Title_encoded', 'Education_encoded', 'City Tier_encoded']
        X = df_ml[features]
        y = df_ml['Expected Dowry (INR)']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        
        # Model performance
        col1, col2, col3 = st.columns(3)
        
        with col1:
            mae = mean_absolute_error(y_test, y_pred)
            st.metric("Mean Absolute Error", f"₹{mae:,.0f}")
        
        with col2:
            r2 = r2_score(y_test, y_pred)
            st.metric("R² Score", f"{r2:.3f}")
        
        with col3:
            accuracy = (1 - abs(y_test - y_pred) / y_test).mean() * 100
            st.metric("Accuracy", f"{accuracy:.1f}%")
        
        # Prediction interface
        st.markdown("### 🎯 Make Predictions")
        
        pred_col1, pred_col2 = st.columns(2)
        
        with pred_col1:
            pred_salary = st.number_input("Monthly Salary (₹)", 
                                        min_value=10000, 
                                        max_value=500000, 
                                        value=50000, 
                                        step=1000)
            pred_job = st.selectbox("Job Title", df['Job Title'].unique())
            pred_edu = st.selectbox("Education", df['Education'].unique())
        
        with pred_col2:
            pred_city = st.selectbox("City Tier", df['City Tier'].unique())
            
            if st.button("🚀 Predict Dowry"):
                # Encode inputs
                job_encoded = le_job.transform([pred_job])[0]
                edu_encoded = le_edu.transform([pred_edu])[0]
                city_encoded = le_city.transform([pred_city])[0]
                
                # Make prediction
                prediction = model.predict([[pred_salary, job_encoded, edu_encoded, city_encoded]])[0]
                
                st.markdown(f"""
                <div class="prediction-result">
                    <h2>Predicted Dowry: ₹{prediction:,.0f}</h2>
                </div>
                """, unsafe_allow_html=True)
        
        # Feature importance
        feature_names = ['Monthly Salary', 'Job Title', 'Education', 'City Tier']
        importance = model.feature_importances_
        
        fig_importance = px.bar(
            x=importance,
            y=feature_names,
            orientation='h',
            title="Feature Importance in Prediction",
            color=importance,
            color_continuous_scale='viridis'
        )
        fig_importance.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_importance, use_container_width=True)

    elif analysis_type == "📋 Data Explorer":
        st.subheader("📋 Data Explorer")
        
        # Data overview
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Dataset Overview")
            st.write(f"**Total Records:** {len(df)}")
            st.write(f"**Features:** {len(df.columns)}")
            st.write(f"**Date Range:** Sample Dataset")
            
            st.markdown("### 🔍 Data Types")
            st.write(df.dtypes)
        
        with col2:
            st.markdown("### 📈 Basic Statistics")
            st.write(df.describe())
        
        # Raw data with filters
        st.markdown("### 🗂️ Raw Data")
        
        # Search and filter options
        col1, col2 = st.columns(2)
        with col1:
            search_job = st.selectbox("Filter by Job Title", ["All"] + list(df['Job Title'].unique()))
        with col2:
            salary_range = st.slider("Salary Range (₹)", 
                                    min_value=int(df['Monthly Salary'].min()), 
                                    max_value=int(df['Monthly Salary'].max()),
                                    value=(int(df['Monthly Salary'].min()), int(df['Monthly Salary'].max())))
        
        # Apply filters
        display_df = df.copy()
        if search_job != "All":
            display_df = display_df[display_df['Job Title'] == search_job]
        
        display_df = display_df[
            (display_df['Monthly Salary'] >= salary_range[0]) & 
            (display_df['Monthly Salary'] <= salary_range[1])
        ]
        
        st.dataframe(display_df, use_container_width=True)
        
        # Download option
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name="dowry_data_filtered.csv",
            mime="text/csv"
        )

    # Insights section
    st.markdown("---")
    st.markdown("## 💡 Key Insights")

    insight_col1, insight_col2 = st.columns(2)

    with insight_col1:
        st.markdown("""
        <div class="insight-box">
            <h4>🎯 Profession Impact</h4>
            <p>IAS Officers and Doctors tend to have the highest dowry expectations, reflecting societal prestige associated with these professions.</p>
        </div>
        """, unsafe_allow_html=True)

    with insight_col2:
        st.markdown("""
        <div class="insight-box">
            <h4>🎓 Education Correlation</h4>
            <p>Higher education levels (Ph.D., MBBS, MBA) generally correlate with increased dowry expectations across all professions.</p>
        </div>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>📊 Dowry Analytics Dashboard | Built with Streamlit & Plotly</p>
        <p><em>This dashboard is for analytical purposes only and does not endorse dowry practices.</em></p>
    </div>
    """, unsafe_allow_html=True)
