import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("Public_Transport_Usage_Trends2.csv")
    return df

df = load_data()

st.set_page_config(page_title="Advanced Transport Analytics", layout="wide")
st.title("🚍 Advanced Public Transport Analytics Dashboard")
st.markdown("*Discover hidden patterns and actionable insights in transport usage data*")

# Sidebar filters
st.sidebar.header("🔍 Advanced Filters")

countries = st.sidebar.multiselect(
    "Select Countries", 
    options=df['Country'].unique(), 
    default=df['Country'].unique()[:5] if len(df['Country'].unique()) > 5 else df['Country'].unique()
)

years = st.sidebar.slider(
    "Year Range", 
    min_value=int(df['Year'].min()), 
    max_value=int(df['Year'].max()), 
    value=(int(df['Year'].min()), int(df['Year'].max()))
)

transport_types = st.sidebar.multiselect(
    "Transport Types", 
    options=df['Transport_Type'].unique(), 
    default=df['Transport_Type'].unique()
)

# Advanced filters
min_satisfaction = st.sidebar.slider("Minimum Satisfaction Score", 
                                   min_value=float(df['Customer_Satisfaction_Score'].min()),
                                   max_value=float(df['Customer_Satisfaction_Score'].max()),
                                   value=float(df['Customer_Satisfaction_Score'].min()))

# Filter data
filtered_df = df[
    (df['Country'].isin(countries)) &
    (df['Year'].between(years[0], years[1])) &
    (df['Transport_Type'].isin(transport_types)) &
    (df['Customer_Satisfaction_Score'] >= min_satisfaction)
]

if filtered_df.empty:
    st.error("No data matches your filters. Please adjust your selection.")
    st.stop()

# Calculate insights
total_usage = filtered_df['Annual_Usage'].sum()
growth_rate = ((filtered_df[filtered_df['Year'] == years[1]]['Annual_Usage'].sum() - 
                filtered_df[filtered_df['Year'] == years[0]]['Annual_Usage'].sum()) /
               filtered_df[filtered_df['Year'] == years[0]]['Annual_Usage'].sum() * 100) if years[1] != years[0] else 0

# Enhanced KPIs
st.subheader("🎯 Strategic Insights")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Usage", f"{total_usage/1_000_000:.1f}M", 
              delta=f"{growth_rate:.1f}% growth" if growth_rate != 0 else None)

with col2:
    avg_satisfaction = filtered_df['Customer_Satisfaction_Score'].mean()
    best_satisfaction = df['Customer_Satisfaction_Score'].max()
    st.metric("Avg Satisfaction", f"{avg_satisfaction:.2f}/5", 
              delta=f"{avg_satisfaction - best_satisfaction:.2f}" if avg_satisfaction < best_satisfaction else "Excellent")

with col3:
    avg_emissions = filtered_df['CO2_Emissions_kg_per_passenger'].mean()
    st.metric("CO2 per Passenger", f"{avg_emissions:.2f} kg")

with col4:
    efficiency_score = (avg_satisfaction * total_usage / 1_000_000) / avg_emissions
    st.metric("Efficiency Score", f"{efficiency_score:.1f}")

with col5:
    countries_count = len(filtered_df['Country'].unique())
    st.metric("Markets Analyzed", f"{countries_count}")

# 1. CORRELATION HEATMAP - Most Insightful
st.subheader("🔥 Performance Correlation Matrix")
st.markdown("*Discover which factors drive transport success*")

# Create correlation data
corr_data = filtered_df[['Annual_Usage', 'Customer_Satisfaction_Score', 'CO2_Emissions_kg_per_passenger', 'Urbanization_Rate_%']].corr()
corr_df = corr_data.reset_index().melt('index', var_name='variable', value_name='correlation')

heatmap = alt.Chart(corr_df).mark_rect().encode(
    x=alt.X('variable:N', title='Metrics'),
    y=alt.Y('index:N', title='Metrics'),
    color=alt.Color('correlation:Q', 
                   scale=alt.Scale(scheme='redblue', domain=[-1, 1]),
                   title='Correlation'),
    tooltip=['index', 'variable', 'correlation']
).properties(height=300)

text = alt.Chart(corr_df).mark_text(baseline='middle', fontSize=12, fontWeight='bold').encode(
    x=alt.X('variable:N'),
    y=alt.Y('index:N'),
    text=alt.Text('correlation:Q', format='.2f'),
    color=alt.condition(alt.datum.correlation > 0.5, alt.value('white'), alt.value('black'))
)

st.altair_chart(heatmap + text, use_container_width=True)

# 2. MULTI-DIMENSIONAL BUBBLE CHART
st.subheader("🌟 Transport Performance Matrix")
st.markdown("*Size = Usage Volume | Color = Transport Type | Position = Satisfaction vs Emissions*")

bubble_chart = alt.Chart(filtered_df).mark_circle(opacity=0.7).encode(
    x=alt.X('Customer_Satisfaction_Score:Q', title='Customer Satisfaction Score', scale=alt.Scale(zero=False)),
    y=alt.Y('CO2_Emissions_kg_per_passenger:Q', title='CO2 Emissions (kg per passenger)', scale=alt.Scale(zero=False)),
    size=alt.Size('Annual_Usage:Q', 
                 title='Annual Usage',
                 scale=alt.Scale(range=[100, 1000])),
    color=alt.Color('Transport_Type:N', title='Transport Type'),
    stroke=alt.value('white'),
    strokeWidth=alt.value(1),
    tooltip=['Country', 'Year', 'Transport_Type', 'Annual_Usage', 'Customer_Satisfaction_Score', 'CO2_Emissions_kg_per_passenger']
).properties(
    height=450
).interactive()

st.altair_chart(bubble_chart, use_container_width=True)

# 3. TREND DECOMPOSITION
st.subheader("📈 Growth Trends & Patterns")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Usage Evolution by Transport Type**")
    
    # Calculate year-over-year growth
    yearly_data = filtered_df.groupby(['Year', 'Transport_Type'])['Annual_Usage'].sum().reset_index()
    
    trend_chart = alt.Chart(yearly_data).mark_line(point=True, strokeWidth=3).encode(
        x=alt.X('Year:O', title='Year'),
        y=alt.Y('Annual_Usage:Q', title='Annual Usage'),
        color=alt.Color('Transport_Type:N', title='Transport Type'),
        tooltip=['Year', 'Transport_Type', 'Annual_Usage']
    ).properties(height=350).interactive()
    
    st.altair_chart(trend_chart, use_container_width=True)

with col2:
    st.markdown("**Satisfaction Score Distribution**")
    
    # Satisfaction histogram with overlay
    hist_base = alt.Chart(filtered_df).add_selection(
        alt.selection_interval(bind='scales')
    )
    
    histogram = hist_base.mark_bar(opacity=0.7).encode(
        alt.X('Customer_Satisfaction_Score:Q', bin=alt.Bin(step=0.2), title='Satisfaction Score'),
        alt.Y('count()', title='Number of Records'),
        color=alt.Color('Transport_Type:N', title='Transport Type')
    ).properties(height=350)
    
    st.altair_chart(histogram, use_container_width=True)

# 4. PERFORMANCE BENCHMARKING
st.subheader("🏆 Performance Benchmarking")

# Create performance score
filtered_df_copy = filtered_df.copy()
filtered_df_copy['Performance_Score'] = (
    filtered_df_copy['Customer_Satisfaction_Score'] * 20 +  # 20% weight
    (100 - filtered_df_copy['CO2_Emissions_kg_per_passenger']) * 0.5  # Environmental score
)

top_performers = filtered_df_copy.groupby(['Country', 'Transport_Type']).agg({
    'Performance_Score': 'mean',
    'Annual_Usage': 'sum',
    'Customer_Satisfaction_Score': 'mean',
    'CO2_Emissions_kg_per_passenger': 'mean'
}).reset_index().sort_values('Performance_Score', ascending=False)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Top Performing Transport Systems**")
    
    top_chart = alt.Chart(top_performers.head(10)).mark_bar().encode(
        x=alt.X('Performance_Score:Q', title='Performance Score'),
        y=alt.Y('Country:N', sort='-x', title='Country'),
        color=alt.Color('Transport_Type:N', title='Transport Type'),
        tooltip=['Country', 'Transport_Type', 'Performance_Score', 'Customer_Satisfaction_Score']
    ).properties(height=350)
    
    st.altair_chart(top_chart, use_container_width=True)

with col2:
    st.markdown("**Efficiency Frontier Analysis**")
    
    efficiency_chart = alt.Chart(filtered_df).mark_circle(size=100).encode(
        x=alt.X('CO2_Emissions_kg_per_passenger:Q', title='CO2 Emissions (Lower is Better)'),
        y=alt.Y('Customer_Satisfaction_Score:Q', title='Customer Satisfaction (Higher is Better)'),
        color=alt.Color('Transport_Type:N', title='Transport Type'),
        size=alt.Size('Annual_Usage:Q', title='Usage Volume'),
        tooltip=['Country', 'Transport_Type', 'Customer_Satisfaction_Score', 'CO2_Emissions_kg_per_passenger']
    ).properties(height=350).interactive()
    
    st.altair_chart(efficiency_chart, use_container_width=True)

# 5. ADVANCED INSIGHTS SECTION
st.subheader("🧠 AI-Powered Insights")

# Calculate insights
insights = []

# Growth insights
if growth_rate > 10:
    insights.append(f"🚀 **Strong Growth**: {growth_rate:.1f}% growth indicates expanding market adoption")
elif growth_rate < -5:
    insights.append(f"⚠️ **Declining Usage**: {growth_rate:.1f}% decline suggests market challenges")

# Satisfaction insights
if avg_satisfaction > 4.0:
    insights.append("⭐ **High Satisfaction**: Customer satisfaction exceeds 4.0, indicating excellent service quality")
elif avg_satisfaction < 3.0:
    insights.append("📉 **Low Satisfaction**: Customer satisfaction below 3.0 requires immediate attention")

# Environmental insights
if avg_emissions < 2.0:
    insights.append("🌱 **Eco-Friendly**: Low emissions indicate environmentally sustainable transport")
elif avg_emissions > 5.0:
    insights.append("🌍 **High Emissions**: Consider green initiatives to reduce environmental impact")

# Best performing transport type
best_transport = top_performers.iloc[0]['Transport_Type'] if not top_performers.empty else "N/A"
insights.append(f"🏆 **Top Performer**: {best_transport} shows the best overall performance score")

# Display insights
for insight in insights:
    st.markdown(insight)

# 6. DETAILED DATA TABLE WITH CALCULATIONS
st.subheader("📊 Detailed Performance Metrics")

# Create enhanced data table
display_df = filtered_df.groupby(['Country', 'Transport_Type']).agg({
    'Annual_Usage': ['sum', 'mean'],
    'Customer_Satisfaction_Score': 'mean',
    'CO2_Emissions_kg_per_passenger': 'mean',
    'Urbanization_Rate_%': 'mean'
}).round(2)

display_df.columns = ['Total_Usage', 'Avg_Annual_Usage', 'Avg_Satisfaction', 'Avg_CO2_Emissions', 'Avg_Urbanization']
display_df = display_df.reset_index()

# Add calculated metrics
display_df['Usage_per_Urban_%'] = display_df['Total_Usage'] / display_df['Avg_Urbanization']
display_df['Satisfaction_Efficiency'] = display_df['Avg_Satisfaction'] / display_df['Avg_CO2_Emissions']

st.dataframe(display_df, use_container_width=True)

# Export functionality
csv = display_df.to_csv(index=False)
st.download_button(
    label="📥 Download Analysis Results",
    data=csv,
    file_name=f'transport_analysis_{datetime.now().strftime("%Y%m%d")}.csv',
    mime='text/csv'
)

# Footer with methodology
st.markdown("---")
st.markdown("""
**Methodology Notes:**
- Performance Score = (Satisfaction × 20) + (Environmental Score × 0.5)
- Efficiency Score = (Satisfaction × Usage) / CO2 Emissions  
- Environmental Score = 100 - CO2 Emissions per passenger
- Usage per Urban % = Total Usage / Urbanization Rate
""")
st.caption("Built with ❤️ using Streamlit and Altair | Advanced Analytics Dashboard")