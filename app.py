import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
import os
from datetime import datetime

# -------------------------------------------------
# Page configuration
# -------------------------------------------------
st.set_page_config(
    page_title="India Climate Digital Twin - Time Travel",
    page_icon="🌍",
    layout="wide"
)

# -------------------------------------------------
# Custom CSS for better UI
# -------------------------------------------------
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-top: 0;
    }
    .feature-badge {
        background-color: #ff6b6b;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.8rem;
        display: inline-block;
    }
    .stMetric {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# Title Section
# -------------------------------------------------
st.markdown('<h1 class="main-header">🌍 India Climate Digital Twin</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Visualizing Rainfall Patterns Across India (2015-2024)</p>', unsafe_allow_html=True)
st.markdown('<span class="feature-badge">⭐ X-Factor: Time Travel Simulation</span>', unsafe_allow_html=True)
st.markdown("---")

# -------------------------------------------------
# Load data with caching
# -------------------------------------------------
@st.cache_data
def load_all_data():
    """Load data from CSV files"""
    # Try combined file first
    if os.path.exists('monthly_rainfall_all_years.csv'):
        df = pd.read_csv('monthly_rainfall_all_years.csv')
        if not df.empty:
            return df
    
    # Try individual year files
    all_dfs = []
    for year in range(2015, 2025):
        filename = f'monthly_rainfall_{year}.csv'
        if os.path.exists(filename):
            df = pd.read_csv(filename)
            if not df.empty:
                all_dfs.append(df)
    
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    
    return None

@st.cache_data
def filter_india_data(df):
    """Filter data to India boundaries"""
    INDIA_LAT_MIN = 6.5
    INDIA_LAT_MAX = 38.5
    INDIA_LON_MIN = 66.5
    INDIA_LON_MAX = 100.5
    
    return df[
        (df['lat'] >= INDIA_LAT_MIN) & 
        (df['lat'] <= INDIA_LAT_MAX) & 
        (df['lon'] >= INDIA_LON_MIN) & 
        (df['lon'] <= INDIA_LON_MAX)
    ].copy()

# Load data
df_all = load_all_data()

# -------------------------------------------------
# Handle missing data
# -------------------------------------------------
if df_all is None:
    st.error("❌ No data found! Please run test_imdlib.py first.")
    st.info("📝 Run this command in your terminal: `python test_imdlib.py`")
    
    # Show manual data loading option
    st.warning("⚠️ Or make sure you have CSV files in the current directory:")
    files = os.listdir('.')
    csv_files = [f for f in files if f.endswith('.csv')]
    if csv_files:
        st.write("Found these CSV files:")
        for f in csv_files:
            st.write(f"  - {f}")
    st.stop()

# Filter to India only
df_india = filter_india_data(df_all)

if df_india.empty:
    st.error("❌ No data within India boundaries. Please check your data.")
    st.stop()

# Get available years
available_years = sorted(df_india['year'].unique())
min_year = int(available_years[0])
max_year = int(available_years[-1])

st.sidebar.success(f"✅ Loaded {len(df_india):,} data points from {min_year} to {max_year}")

# -------------------------------------------------
# Sidebar - Time Travel Controls
# -------------------------------------------------
st.sidebar.header("⏳ Time Travel Controls")
st.sidebar.markdown("*Explore climate patterns across different years*")

# Year slider - X-Factor Feature!
selected_year = st.sidebar.slider(
    "🎯 Select Year",
    min_value=min_year,
    max_value=max_year,
    value=min_year,
    step=1,
    format="%d"
)

# Month selector
months = ['January', 'February', 'March', 'April', 'May', 'June', 
          'July', 'August', 'September', 'October', 'November', 'December']
selected_month_name = st.sidebar.selectbox("📅 Select Month", months)
selected_month = months.index(selected_month_name) + 1

# Auto-play option
auto_play = st.sidebar.checkbox("▶️ Auto-play through years")

# Display current time period
st.sidebar.info(f"📊 Showing: **{selected_month_name} {selected_year}**")

# Progress bar for time travel
years_progress = (selected_year - min_year) / (max_year - min_year) if max_year > min_year else 0
st.sidebar.progress(years_progress)

# -------------------------------------------------
# Filter data for selected year and month
# -------------------------------------------------
month_df = df_india[(df_india['year'] == selected_year) & (df_india['month'] == selected_month)].copy()

if month_df.empty:
    st.warning(f"No data available for {selected_month_name} {selected_year}")
    st.stop()

# -------------------------------------------------
# Key Metrics
# -------------------------------------------------
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("🌧️ Total Rainfall", f"{month_df['rainfall'].sum():.1f} mm")
with col2:
    st.metric("📊 Average", f"{month_df['rainfall'].mean():.2f} mm")
with col3:
    st.metric("⬆️ Max", f"{month_df['rainfall'].max():.1f} mm")
with col4:
    st.metric("📍 Data Points", f"{len(month_df):,}")
with col5:
    # Year-over-year change (if data available)
    prev_year_data = df_india[(df_india['year'] == selected_year - 1) & (df_india['month'] == selected_month)]
    if not prev_year_data.empty:
        prev_avg = prev_year_data['rainfall'].mean()
        curr_avg = month_df['rainfall'].mean()
        change = ((curr_avg - prev_avg) / prev_avg) * 100 if prev_avg > 0 else 0
        st.metric("📈 YoY Change", f"{change:+.1f}%")
    else:
        st.metric("📈 YoY Change", "N/A")

# -------------------------------------------------
# Map Visualization with Perfect India Focus
# -------------------------------------------------
st.subheader(f"🗺️ Rainfall Map - {selected_month_name} {selected_year}")

# Create map with perfect India focus
m = folium.Map(
    location=[21.0, 80.0],
    zoom_start=5,
    tiles='CartoDB Positron',
    attr='© CartoDB',
    max_bounds=True,
    min_zoom=4,
    max_zoom=7,
    zoom_control=True,
    no_wrap=True,
    prefer_canvas=True,
    control_scale=True
)

# Force fit bounds to India
m.fit_bounds(
    [[6.0, 66.0], [38.0, 102.0]],
    padding=(20, 20)
)

# Add India boundary
INDIA_LAT_MIN, INDIA_LAT_MAX = 6.5, 38.5
INDIA_LON_MIN, INDIA_LON_MAX = 66.5, 100.5

folium.Rectangle(
    bounds=[[INDIA_LAT_MIN, INDIA_LON_MIN], [INDIA_LAT_MAX, INDIA_LON_MAX]],
    color='red',
    weight=3,
    fill=False,
    dash_array='5,5',
    popup='🇮🇳 India',
    tooltip='India Boundary'
).add_to(m)

# Add year label
folium.Marker(
    [35.5, 97.0],
    popup=f"Year: {selected_year}",
    icon=folium.DivIcon(
        html=f'<div style="font-size:28px;font-weight:bold;color:red;text-shadow: 2px 2px 4px white;">{selected_year}</div>'
    )
).add_to(m)

# Add major Indian cities
cities = {
    'New Delhi': [28.6139, 77.2090],
    'Mumbai': [19.0760, 72.8777],
    'Chennai': [13.0827, 80.2707],
    'Kolkata': [22.5726, 88.3639],
    'Bengaluru': [12.9716, 77.5946],
    'Hyderabad': [17.3850, 78.4867],
    'Ahmedabad': [23.0225, 72.5714],
    'Pune': [18.5204, 73.8567],
    'Jaipur': [26.9124, 75.7873],
    'Lucknow': [26.8467, 80.9462]
}

for city, coords in cities.items():
    folium.CircleMarker(
        coords,
        radius=3,
        color='blue',
        fill=True,
        fill_opacity=0.7,
        popup=city,
        tooltip=city
    ).add_to(m)

# Heatmap data
heat_data = [[row['lat'], row['lon'], row['rainfall']] for _, row in month_df.iterrows()]

if heat_data:
    HeatMap(
        heat_data,
        radius=10,
        blur=12,
        min_opacity=0.4,
        max_zoom=7,
        gradient={
            0.2: 'blue',
            0.4: 'cyan',
            0.6: 'lime',
            0.8: 'yellow',
            1.0: 'red'
        }
    ).add_to(m)

col_map, col_stats = st.columns([2, 1])

with col_map:
    st_folium(m, width=700, height=500)

with col_stats:
    st.markdown("### 📊 Map Statistics")
    st.markdown(f"**Year:** {selected_year}")
    st.markdown(f"**Month:** {selected_month_name}")
    st.markdown(f"**Total Points:** {len(month_df):,}")
    
    # Rainfall categories
    low = month_df[month_df['rainfall'] < 1.0]['rainfall'].count()
    medium = month_df[(month_df['rainfall'] >= 1.0) & (month_df['rainfall'] < 5.0)]['rainfall'].count()
    high = month_df[month_df['rainfall'] >= 5.0]['rainfall'].count()
    
    st.markdown("**Rainfall Distribution:**")
    st.markdown(f"- 🔵 Light (<1mm): {low} points")
    st.markdown(f"- 🟡 Moderate (1-5mm): {medium} points")
    st.markdown(f"- 🔴 Heavy (>5mm): {high} points")

# -------------------------------------------------
# Monthly Rainfall Pattern Chart
# -------------------------------------------------
st.subheader("📈 Monthly Rainfall Pattern")

# Aggregate by month for all years
monthly_all_years = df_india.groupby(['year', 'month'])['rainfall'].mean().reset_index()

# Filter for selected year
monthly_selected_year = monthly_all_years[monthly_all_years['year'] == selected_year].copy()
monthly_selected_year['month_name'] = monthly_selected_year['month'].apply(lambda x: months[x-1])

# Create bar chart
fig = px.bar(
    monthly_selected_year,
    x='month_name',
    y='rainfall',
    title=f'Average Monthly Rainfall Across India - {selected_year}',
    labels={'month_name': 'Month', 'rainfall': 'Average Rainfall (mm)'},
    color='rainfall',
    color_continuous_scale='Blues'
)

# Highlight selected month
fig.add_vline(
    x=selected_month - 0.5,
    line_dash="dash",
    line_color="red",
    annotation_text=f"{selected_month_name}",
    annotation_position="top right"
)

# Add year-over-year comparison (previous year)
if selected_year > min_year:
    prev_year_data = monthly_all_years[monthly_all_years['year'] == selected_year - 1]
    if not prev_year_data.empty:
        prev_year_data['month_name'] = prev_year_data['month'].apply(lambda x: months[x-1])
        fig.add_trace(go.Scatter(
            x=prev_year_data['month_name'],
            y=prev_year_data['rainfall'],
            mode='lines+markers',
            name=f'{selected_year - 1}',
            line=dict(color='orange', dash='dash')
        ))

st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------
# Year-over-Year Trend Analysis
# -------------------------------------------------
st.subheader("📉 Year-over-Year Trends")

# Calculate yearly averages
yearly_avg = df_india.groupby('year')['rainfall'].mean().reset_index()

fig_trend = px.line(
    yearly_avg,
    x='year',
    y='rainfall',
    title='Average Annual Rainfall Trend (2015-2024)',
    labels={'year': 'Year', 'rainfall': 'Average Rainfall (mm)'},
    markers=True
)

# Add trend line
fig_trend.add_trace(go.Scatter(
    x=yearly_avg['year'],
    y=yearly_avg['rainfall'].rolling(window=3).mean(),
    mode='lines',
    name='3-Year Moving Average',
    line=dict(color='red', dash='dash')
))

# Highlight selected year
fig_trend.add_vline(
    x=selected_year,
    line_dash="dash",
    line_color="green",
    annotation_text=f"{selected_year}",
    annotation_position="top right"
)

st.plotly_chart(fig_trend, use_container_width=True)

# -------------------------------------------------
# Regional Analysis
# -------------------------------------------------
st.subheader("🗺️ Regional Rainfall Analysis")

# Create lat/lon bins for regions
month_df['lat_bin'] = pd.cut(month_df['lat'], bins=4, labels=['South', 'Central-South', 'Central-North', 'North'])
month_df['lon_bin'] = pd.cut(month_df['lon'], bins=3, labels=['West', 'Central', 'East'])

# Pivot table for heatmap
region_data = month_df.pivot_table(
    values='rainfall',
    index='lat_bin',
    columns='lon_bin',
    aggfunc='mean'
)

# Display as heatmap
fig_region = px.imshow(
    region_data,
    text_auto='.1f',
    title=f'Average Rainfall by Region - {selected_month_name} {selected_year}',
    labels=dict(x="Longitude", y="Latitude", color="Rainfall (mm)"),
    color_continuous_scale='Blues'
)

st.plotly_chart(fig_region, use_container_width=True)

# -------------------------------------------------
# Data Explorer
# -------------------------------------------------
st.subheader("📊 Data Explorer")

# Data filters
col_filter1, col_filter2, col_filter3 = st.columns(3)

with col_filter1:
    filter_year = st.selectbox("Filter by Year", ['All Years'] + list(available_years))
with col_filter2:
    filter_month = st.selectbox("Filter by Month", ['All Months'] + months)
with col_filter3:
    min_rainfall = st.slider("Minimum Rainfall (mm)", 0.0, 50.0, 0.0)

# Apply filters
filtered_df = df_india.copy()
if filter_year != 'All Years':
    filtered_df = filtered_df[filtered_df['year'] == int(filter_year)]
if filter_month != 'All Months':
    filtered_month_num = months.index(filter_month) + 1
    filtered_df = filtered_df[filtered_df['month'] == filtered_month_num]
filtered_df = filtered_df[filtered_df['rainfall'] >= min_rainfall]

st.write(f"Showing {len(filtered_df):,} data points")

# Show raw data
if st.checkbox("Show raw data"):
    st.dataframe(filtered_df.head(100))

# Download button
csv = filtered_df.to_csv(index=False)
st.download_button(
    label="📥 Download Filtered Data as CSV",
    data=csv,
    file_name=f"rainfall_data_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

# -------------------------------------------------
# Auto-play Logic
# -------------------------------------------------
if auto_play:
    if selected_year < max_year:
        st.sidebar.info(f"⏳ Playing... Next year: {selected_year + 1}")
        # Auto-advance using session state
        if 'year' not in st.session_state:
            st.session_state.year = selected_year
        st.session_state.year = selected_year + 1
        # Note: Streamlit will rerun with new year
    else:
        st.sidebar.success("🎉 Reached the end! Uncheck and recheck to restart.")

# -------------------------------------------------
# Footer
# -------------------------------------------------
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns(3)

with col_footer1:
    st.markdown("**🚀 Built for Bharatiya Antariksh Hackathon 2026**")
with col_footer2:
    st.markdown(f"**📅 Data Range:** {min_year} - {max_year}")
with col_footer3:
    st.markdown("**🇮🇳 Powered by IMD Data**")

st.caption("💡 Tip: Use the slider above to travel through time! Drag it to see climate patterns change.")
st.caption("🗺️ Map shows rainfall intensity: Blue=Low, Cyan=Moderate, Yellow=High, Red=Very High")