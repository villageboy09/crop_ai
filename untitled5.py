import streamlit as st
import asyncio
import edge_tts
from datetime import datetime, timedelta
import requests
import os
import base64
from googletrans import Translator
import json
from PIL import Image
import pandas as pd


class StreamlitCropDiseaseAnalyzer:
    def __init__(self):
        # Existing API configurations
        self.API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
        self.API_KEY = st.secrets["gemini"]["api_key"]
        self.WEATHER_API_KEY = st.secrets["visual_crossing"]["api_key"]
        self.VOICES = {
            'Telugu': 'te-IN-ShrutiNeural',
            'English': 'en-US-AriaNeural',
            'Hindi': 'hi-IN-SwaraNeural'
        }
        
        # Crop data with image URLs and growth stages
        self.CROPS = {
    "Rice": {
        "image": "https://cdn.britannica.com/89/140889-050-EC3F00BF/Ripening-heads-rice-Oryza-sativa.jpg",
        "stages": {
            "Seedling": {"duration": 25, "npk_multiplier": 0.4},
            "Vegetative": {"duration": 50, "npk_multiplier": 0.9},
            "Flowering": {"duration": 30, "npk_multiplier": 1.2},
            "Maturing": {"duration": 35, "npk_multiplier": 1.4}
        }
    },
    "Maize": {
        "image": "https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcTSQTwY5H90hpRERbth6Y70s48hYKQQ3EimRbhVpGTe_zCHc0II",
        "stages": {
            "Seedling": {"duration": 20, "npk_multiplier": 0.5},
            "Vegetative": {"duration": 45, "npk_multiplier": 1.0},
            "Flowering": {"duration": 30, "npk_multiplier": 1.3},
            "Maturing": {"duration": 35, "npk_multiplier": 1.6}
        }
    },
    "Sorghum": {
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQFyoo17z6OwjPUWoBWrKNMEfJf1Cd4wpx5atIJGCgtZU8E9zPQ",
        "stages": {
            "Seedling": {"duration": 22, "npk_multiplier": 0.5},
            "Vegetative": {"duration": 40, "npk_multiplier": 1.0},
            "Flowering": {"duration": 25, "npk_multiplier": 1.2},
            "Maturing": {"duration": 30, "npk_multiplier": 1.4}
        }
    },
    "Cotton": {
        "image": "https://cdn.britannica.com/18/156618-050-39339EA2/cotton-harvesting.jpg",
        "stages": {
            "Seedling": {"duration": 25, "npk_multiplier": 0.6},
            "Vegetative": {"duration": 45, "npk_multiplier": 1.1},
            "Flowering": {"duration": 30, "npk_multiplier": 1.5},
            "Boll Formation": {"duration": 35, "npk_multiplier": 1.8}
        }
    },
    "Groundnut": {
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQX4-OuVBESIfeRVCsFnLstkRLvDRAUpeSlGA&s",
        "stages": {
            "Seedling": {"duration": 20, "npk_multiplier": 0.5},
            "Vegetative": {"duration": 40, "npk_multiplier": 1.0},
            "Flowering": {"duration": 25, "npk_multiplier": 1.2},
            "Pod Formation": {"duration": 30, "npk_multiplier": 1.5}
        }
    }
}

        # NPK requirements by region (example values - replace with actual data from maps)
        self.REGIONAL_NPK = {
            "North": {"N": 1.2, "P": 0.8, "K": 1.0},
            "South": {"N": 0.9, "P": 1.1, "K": 1.2},
            "East": {"N": 1.1, "P": 0.9, "K": 0.8},
            "West": {"N": 1.0, "P": 1.0, "K": 1.0},
            "Central": {"N": 1.1, "P": 1.0, "K": 0.9}
        }

        self.BASE_NPK_REQUIREMENTS = {
                "Rice": {"N": 100, "P": 50, "K": 80},
    "Maize": {"N": 120, "P": 60, "K": 100},
    "Sorghum": {"N": 90, "P": 40, "K": 70},
    "Cotton": {"N": 110, "P": 70, "K": 90},
    "Groundnut": {"N": 80, "P": 60, "K": 70}
            # ... other crops
        }

        self.translator = Translator()

    def get_weather_data(self, location):
        """Fetch weather data from Visual Crossing API"""
        try:
            # Base URL for Visual Crossing Weather API
            base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
            
            # Parameters for the API request
            params = {
                'unitGroup': 'metric',
                'key': self.WEATHER_API_KEY,
                'contentType': 'json',
                'include': 'current,days',
                'elements': 'temp,humidity,conditions,precip,cloudcover,windspeed,pressure'
            }
            
            # Construct the full URL
            url = f"{base_url}/{location}/today"
            
            # Make the API request
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'temperature': data['days'][0]['temp'],
                    'humidity': data['days'][0]['humidity'],
                    'conditions': data['days'][0]['conditions'],
                    'precipitation': data['days'][0].get('precip', 0),
                    'cloudCover': data['days'][0].get('cloudcover', 0),
                    'windSpeed': data['days'][0].get('windspeed', 0),
                    'pressure': data['days'][0].get('pressure', 0)
                }
            else:
                st.error(f"Weather API Error: Status {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Error fetching weather data: {str(e)}")
            return None

    def calculate_growth_stage(self, sowing_date, crop):
        """Calculate current growth stage based on sowing date"""
        days_since_sowing = (datetime.now() - sowing_date).days
        accumulated_days = 0
        
        for stage, info in self.CROPS[crop]["stages"].items():
            accumulated_days += info["duration"]
            if days_since_sowing <= accumulated_days:
                return stage
        return "Mature"

    def calculate_npk_requirements(self, crop, location, acres, growth_stage):
        """Calculate NPK requirements based on location, area, and growth stage"""
        base_npk = self.BASE_NPK_REQUIREMENTS[crop]
        regional_multiplier = self.REGIONAL_NPK[self.get_region(location)]
        stage_multiplier = self.CROPS[crop]["stages"][growth_stage]["npk_multiplier"]
        
        return {
            "N": base_npk["N"] * regional_multiplier["N"] * stage_multiplier * acres,
            "P": base_npk["P"] * regional_multiplier["P"] * stage_multiplier * acres,
            "K": base_npk["K"] * regional_multiplier["K"] * stage_multiplier * acres
        }

    def get_region(self, location):
        """Determine region based on location (simplified example)"""
        # This should be replaced with actual region determination logic
        # possibly using geocoding and region boundary data
        return "North"  # Default return

    def get_weather_based_recommendations(self, weather_data, crop, growth_stage):
        """Generate recommendations based on weather conditions"""
        recommendations = []
        
        if weather_data["temperature"] > 30:
            recommendations.append("High temperature detected. Increase irrigation frequency.")
        elif weather_data["temperature"] < 15:
            recommendations.append("Low temperature detected. Consider protective measures.")
            
        if weather_data["humidity"] > 80:
            recommendations.append("High humidity may increase disease risk. Ensure good ventilation.")
        
        return recommendations

    def query_gemini_api(self, crop, language):
        """Query Gemini API for crop disease information in specified language"""
        try:
            headers = {
                "Content-Type": "application/json"
            }

            # Adjust prompt based on language
            base_prompt = f"""
            Analyze and provide detailed information about common diseases in {crop} cultivation.
            For each disease, include:
            1. Disease name
            2. Symptoms
            3. Favorable conditions
            4. Prevention methods
            5. Treatment options
            
            Provide the response in {language} language.
            Format the response in a clear, structured way.
            """

            payload = {
                "contents": [{
                    "parts": [{
                        "text": base_prompt
                    }]
                }]
            }

            url = f"{self.API_URL}?key={self.API_KEY}"
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            else:
                error_msg = f"Error: API returned status code {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f"\nDetails: {error_detail.get('error', {}).get('message', 'No details available')}"
                except:
                    pass
                return error_msg

        except Exception as e:
            return f"Error querying API: {str(e)}"

    async def text_to_speech(self, text, output_file, language):
        """Convert text to speech using edge-tts"""
        voice = self.VOICES[language]
        try:
            clean_text = " ".join(word for word in text.split() if not word.startswith("#"))
            communicate = edge_tts.Communicate(clean_text, voice)
            await communicate.save(output_file)
        except Exception as e:
            st.error(f"Error during TTS conversion: {str(e)}")
            raise

    def get_binary_file_downloader_html(self, file_path, file_name):
        """Generate a download link for a binary file."""
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        b64 = base64.b64encode(file_bytes).decode()  # Convert to base64
        return f'<a href="data:file/unknown;base64,{b64}" download="{file_name}">Download {file_name}</a>'
    pass  # Note: Keep all the previous class implementation

def main():
    # Configure the page with a dark theme and custom styles
        st.set_page_config(
        page_title="Your Title",
        page_icon=":shark:",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Updated CSS with better text contrast and visibility
        st.markdown("""
        <style>
        /* Base theme colors and text visibility */
        .stApp {
            background: #f0f2f6;
            color: #1a1a1a;
        }
        
        /* Main header styling */
        .main-header {
            text-align: center;
            padding: 2rem 0;
            color: #1f4d7a;
            font-weight: bold;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        
        /* Card styling with improved contrast */
        .crop-card {
            background: white;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.2s;
            color: #1a1a1a;
            margin-bottom: 1rem;
        }
        
        .crop-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        /* Metric card styling */
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 0.5rem 0;
            color: #1a1a1a;
        }
        
        /* Section headers with better visibility */
        .section-header {
            color: #1f4d7a;
            margin: 2rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #1f4d7a;
            font-weight: bold;
            background: white;
            padding: 1rem;
            border-radius: 10px 10px 0 0;
        }
        
        /* Sidebar styling */
        .sidebar-header {
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 1rem;
            color: #1f4d7a;
            background: white;
            padding: 1rem;
            border-radius: 5px;
        }
        
        /* Recommendation card styling */
        .recommendation-card {
            background: white;
            padding: 1rem;
            border-left: 4px solid #1f4d7a;
            margin: 0.5rem 0;
            border-radius: 0 5px 5px 0;
            color: #1a1a1a;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Alert section styling */
        .alert-section {
            background: white;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        
        /* Override Streamlit's default text colors */
        .stMarkdown, .stText {
            color: #1a1a1a !important;
        }
        
        /* Improve button visibility */
        .stButton > button {
            background-color: #1f4d7a;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            font-weight: bold;
        }
        
        .stButton > button:hover {
            background-color: #2c6ca3;
        }
        
        /* Metric value colors */
        .stMetric .metric-value {
            color: #1f4d7a !important;
            font-weight: bold;
        }
        
        /* Make all text inputs and selects more visible */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select {
            color: #1a1a1a !important;
            background-color: white !important;
        }
        
        /* Ensure warning messages are visible */
        .stAlert {
            background-color: #fff3cd;
            color: #856404;
            padding: 1rem;
            border-radius: 5px;
            border-left: 4px solid #ffeeba;
        }
        </style>
    """, unsafe_allow_html=True)

# Initialize the analyzer
analyzer = StreamlitCropDiseaseAnalyzer()

# Main header with gradient background
st.markdown('<h1 class="main-header">🌾 AI Kiosk Platform For Farmers</h1>', unsafe_allow_html=True)

# Sidebar with improved organization
with st.sidebar:
    st.markdown('<p class="sidebar-header">Configuration Settings</p>', unsafe_allow_html=True)

    # Language selection with custom styling
    selected_language = st.selectbox(
        "🌐 Select Language",
        list(analyzer.VOICES.keys()),
        key="language_select"
    )
    
    # Location input with validation
    location = st.text_input(
        "📍 Location (City, State)",
        "Delhi, India",
        help="Enter your current location"
    )
    
    # Area input with improved UX
    acres = st.number_input(
        "🌱 Area (in acres)",
        min_value=0.1,
        value=1.0,
        step=0.1,
        format="%.1f",
        help="Enter the size of your farming area"
    )
    
    # Date selection with better formatting
    sowing_date = st.date_input(
        "📅 Sowing Date",
        datetime.now() - timedelta(days=30),
        help="Select the date when you sowed your crop"
    )

# Create an elegant crop selection grid
st.markdown('<h2 class="section-header">Select Your Crop</h2>', unsafe_allow_html=True)

crop_cols = st.columns(5)
selected_crop = None

for idx, (crop, data) in enumerate(analyzer.CROPS.items()):
    with crop_cols[idx % 5]:
        st.markdown(f'<div class="crop-card">', unsafe_allow_html=True)
        if st.button(
            f"🌿 {crop}",
            key=f"crop_{idx}",
            use_container_width=True
        ):
            selected_crop = crop
        st.image(data["image"], caption=crop, use_column_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

if selected_crop:
    st.markdown(f'<h2 class="section-header">Analysis for {selected_crop}</h2>', unsafe_allow_html=True)

    # Weather data display with improved visualization
    weather_data = analyzer.get_weather_data(location)
    if weather_data:
        st.markdown('<h3 class="section-header">Current Weather Conditions</h3>', unsafe_allow_html=True)

        # Create a more organized weather metrics display
        weather_cols = st.columns(4)

        # Primary metrics
        with weather_cols[0]:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("🌡️ Temperature", f"{weather_data['temperature']}°C")
            st.markdown('</div>', unsafe_allow_html=True)

        with weather_cols[1]:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("💧 Humidity", f"{weather_data['humidity']}%")
            st.markdown('</div>', unsafe_allow_html=True)

        with weather_cols[2]:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("🌪️ Wind Speed", f"{weather_data['windSpeed']} km/h")
            st.markdown('</div>', unsafe_allow_html=True)

        with weather_cols[3]:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("🌧️ Precipitation", f"{weather_data['precipitation']} mm")
            st.markdown('</div>', unsafe_allow_html=True)

        # Weather alerts with improved visibility
        if weather_data['humidity'] > 80 or weather_data['precipitation'] > 10:
            st.markdown('<div class="alert-section">', unsafe_allow_html=True)
            if weather_data['humidity'] > 80:
                st.warning("⚠️ High Humidity Alert: Monitor crops for potential disease risk")
            if weather_data['precipitation'] > 10:
                st.warning("⚠️ Rainfall Alert: Ensure proper drainage systems")
            st.markdown('</div>', unsafe_allow_html=True)

    # Growth stage and NPK requirements
    growth_stage = analyzer.calculate_growth_stage(
        datetime.combine(sowing_date, datetime.min.time()),
        selected_crop
    )

    # Display growth stage with custom styling
    st.markdown(
        f'<div class="metric-card"><h3>Current Growth Stage: {growth_stage}</h3></div>',
        unsafe_allow_html=True
    )

    # NPK requirements with enhanced visualization
    npk_req = analyzer.calculate_npk_requirements(
        selected_crop, 
        location, 
        acres,
        growth_stage
    )

    st.markdown('<h3 class="section-header">Fertilizer Recommendations</h3>', unsafe_allow_html=True)
    npk_cols = st.columns(3)

    with npk_cols[0]:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Nitrogen (N)", f"{npk_req['N']:.1f} kg/acre")
        st.markdown('</div>', unsafe_allow_html=True)

    with npk_cols[1]:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Phosphorus (P)", f"{npk_req['P']:.1f} kg/acre")
        st.markdown('</div>', unsafe_allow_html=True)

    with npk_cols[2]:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Potassium (K)", f"{npk_req['K']:.1f} kg/acre")
        st.markdown('</div>', unsafe_allow_html=True)

    # Weather-based recommendations with improved presentation
    if weather_data:
        recommendations = analyzer.get_weather_based_recommendations(
            weather_data,
            selected_crop,
            growth_stage
        )
        if recommendations:
            st.markdown('<h3 class="section-header">Weather-based Recommendations</h3>', unsafe_allow_html=True)
            for rec in recommendations:
                st.markdown(f'<div class="recommendation-card">🌱 {rec}</div>', unsafe_allow_html=True)

    # Disease analysis section with progress indication
    with st.spinner('Analyzing crop diseases...'):
        analysis_text = analyzer.query_gemini_api(selected_crop, selected_language)
        
        if "Error:" not in analysis_text:
            st.markdown('<h3 class="section-header">Disease Analysis</h3>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-card">{analysis_text}</div>', unsafe_allow_html=True)
            
            # Audio generation with progress indication
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_file = f"crop_disease_analysis_{selected_crop.lower()}_{timestamp}.mp3"
            
            with st.spinner('Generating audio summary...'):
                asyncio.run(analyzer.text_to_speech(analysis_text, audio_file, selected_language))
            
            # Audio player with download option
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            with open(audio_file, 'rb') as audio_data:
                st.audio(audio_data.read(), format='audio/mp3')
            st.markdown(
                analyzer.get_binary_file_downloader_html(audio_file, 'Download Audio Summary'),
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

            # Cleanup
            try:
                os.remove(audio_file)
            except:
                pass
        else:
            st.error(analysis_text)

if __name__ == "__main__":
    main()
