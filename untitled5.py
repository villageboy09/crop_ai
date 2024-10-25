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
        # API configurations
        self.API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
        self.API_KEY = st.secrets["gemini"]["api_key"]
        self.WEATHER_API_KEY = st.secrets["visual_crossing"]["api_key"]
        self.VOICES = {
            'Telugu': 'te-IN-ShrutiNeural',
            'English': 'en-US-AriaNeural',
            'Hindi': 'hi-IN-SwaraNeural'
        }
        
        # Extended crop data with image URLs and growth stages
        self.CROPS = {
            "Tomato": {
                "image": "https://example.com/tomato.jpg",
                "stages": {
                    "Seedling": {"duration": 20, "npk_multiplier": 0.5},
                    "Vegetative": {"duration": 40, "npk_multiplier": 1.0},
                    "Flowering": {"duration": 30, "npk_multiplier": 1.2},
                    "Fruiting": {"duration": 40, "npk_multiplier": 1.5}
                }
            },
            "Potato": {
                "image": "https://example.com/potato.jpg",
                "stages": {
                    "Sprouting": {"duration": 15, "npk_multiplier": 0.4},
                    "Vegetative": {"duration": 30, "npk_multiplier": 1.0},
                    "Tuber Formation": {"duration": 45, "npk_multiplier": 1.3},
                    "Maturation": {"duration": 30, "npk_multiplier": 0.8}
                }
            },
            "Rice": {
                "image": "https://example.com/rice.jpg",
                "stages": {
                    "Seedling": {"duration": 20, "npk_multiplier": 0.6},
                    "Tillering": {"duration": 30, "npk_multiplier": 1.2},
                    "Panicle Formation": {"duration": 30, "npk_multiplier": 1.4},
                    "Ripening": {"duration": 30, "npk_multiplier": 0.7}
                }
            },
            "Wheat": {
                "image": "https://example.com/wheat.jpg",
                "stages": {
                    "Germination": {"duration": 15, "npk_multiplier": 0.5},
                    "Tillering": {"duration": 35, "npk_multiplier": 1.1},
                    "Heading": {"duration": 30, "npk_multiplier": 1.3},
                    "Ripening": {"duration": 40, "npk_multiplier": 0.8}
                }
            },
            "Cotton": {
                "image": "https://example.com/cotton.jpg",
                "stages": {
                    "Emergence": {"duration": 15, "npk_multiplier": 0.4},
                    "Squaring": {"duration": 35, "npk_multiplier": 1.0},
                    "Flowering": {"duration": 40, "npk_multiplier": 1.4},
                    "Boll Development": {"duration": 50, "npk_multiplier": 1.2}
                }
            }
        }

        # Regional NPK requirements
        self.REGIONAL_NPK = {
            "North": {"N": 1.2, "P": 0.8, "K": 1.0},
            "South": {"N": 0.9, "P": 1.1, "K": 1.2},
            "East": {"N": 1.1, "P": 0.9, "K": 0.8},
            "West": {"N": 1.0, "P": 1.0, "K": 1.0},
            "Central": {"N": 1.1, "P": 1.0, "K": 0.9}
        }

        # Base NPK requirements for all crops
        self.BASE_NPK_REQUIREMENTS = {
            "Tomato": {"N": 120, "P": 80, "K": 100},
            "Potato": {"N": 150, "P": 100, "K": 120},
            "Rice": {"N": 100, "P": 50, "K": 80},
            "Wheat": {"N": 130, "P": 60, "K": 90},
            "Cotton": {"N": 140, "P": 70, "K": 110}
        }

        self.translator = Translator()

    def get_weather_data(self, location):
    """
    Fetch current weather data from Visual Crossing Weather API
    
    Args:
        location (str): Location string (e.g., "Delhi, India")
        
    Returns:
        dict: Weather data containing temperature, humidity, windSpeed, and precipitation
             Returns None if the API request fails
    """
    try:
        # Construct the API URL
        base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
        params = {
            'unitGroup': 'metric',
            'key': self.WEATHER_API_KEY,
            'contentType': 'json',
            'include': 'current'
        }
        
        # Format the location for URL
        formatted_location = location.replace(' ', '%20')
        url = f"{base_url}/{formatted_location}"
        
        # Make the API request
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for bad status codes
        
        # Parse the response
        data = response.json()
        current_conditions = data.get('currentConditions', {})
        
        # Extract relevant weather metrics
        weather_data = {
            'temperature': round(current_conditions.get('temp', 0), 1),
            'humidity': round(current_conditions.get('humidity', 0), 1),
            'windSpeed': round(current_conditions.get('windspeed', 0), 1),
            'precipitation': round(current_conditions.get('precip', 0), 1)
        }
        
        return weather_data
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching weather data: {str(e)}")
        return None
    except (KeyError, ValueError) as e:
        st.error(f"Error parsing weather data: {str(e)}")
        return None# ... (keep all the existing methods unchanged) ...

def get_binary_file_downloader_html(file_path, button_text):
    """Generate HTML for file download button"""
    with open(file_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    button_uuid = f'download_button_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    custom_css = f"""
        <style>
            #{button_uuid} {{
                background-color: rgb(255, 255, 255);
                color: rgb(38, 39, 48);
                padding: 0.25em 0.38em;
                position: relative;
                text-decoration: none;
                border-radius: 4px;
                border-width: 1px;
                border-style: solid;
                border-color: rgb(230, 234, 241);
                border-image: initial;
            }}
            #{button_uuid}:hover {{
                border-color: rgb(246, 51, 102);
                color: rgb(246, 51, 102);
            }}
        </style>
    """
    dl_link = custom_css + f'<a download="{os.path.basename(file_path)}" id="{button_uuid}" href="data:application/octet-stream;base64,{b64}">{button_text}</a><br></br>'
    return dl_link

def main():
    st.set_page_config(page_title="Enhanced Crop Disease Analyzer", page_icon="🌱", layout="wide")
    st.title("🌱 Enhanced Crop Disease Analyzer")
    
    analyzer = StreamlitCropDiseaseAnalyzer()

    # Sidebar inputs
    with st.sidebar:
        st.header("Configuration")
        selected_language = st.selectbox("Select Language", list(analyzer.VOICES.keys()))
        location = st.text_input("Enter your location (City, State)", "Delhi, India")
        acres = st.number_input("Enter area in acres", min_value=0.1, value=1.0, step=0.1)
        sowing_date = st.date_input(
            "Select sowing date",
            datetime.now() - timedelta(days=30)
        )

    # Improved crop selection with columns and images
    st.subheader("Select a Crop")
    
    # Calculate number of rows needed (2 crops per row)
    num_crops = len(analyzer.CROPS)
    num_rows = (num_crops + 1) // 2
    
    selected_crop = None
    
    # Create grid layout
    for row in range(num_rows):
        col1, col2 = st.columns(2)
        
        # First crop in the row
        idx = row * 2
        if idx < num_crops:
            crop = list(analyzer.CROPS.keys())[idx]
            with col1:
                st.image(
                    "https://picsum.photos/200/150",  # Placeholder image
                    caption=crop,
                    use_column_width=True
                )
                if st.button(f"Select {crop}", key=f"crop_{idx}"):
                    selected_crop = crop
        
        # Second crop in the row
        idx = row * 2 + 1
        if idx < num_crops:
            crop = list(analyzer.CROPS.keys())[idx]
            with col2:
                st.image(
                    "https://picsum.photos/200/150",  # Placeholder image
                    caption=crop,
                    use_column_width=True
                )
                if st.button(f"Select {crop}", key=f"crop_{idx}"):
                    selected_crop = crop

    # Analysis section
    if selected_crop:
        st.markdown(f"## Analysis for {selected_crop}")
        
        # Create tabs for different analysis sections
        tabs = st.tabs(["Weather", "Growth Stage", "Fertilizer", "Disease Analysis"])
        
        with tabs[0]:
            # Weather analysis
            weather_data = analyzer.get_weather_data(location)
            if weather_data:
                st.subheader("Current Weather Conditions")
                
                col1, col2, col3, col4 = st.columns(4)
                metrics = [
                    ("Temperature", f"{weather_data['temperature']}°C"),
                    ("Humidity", f"{weather_data['humidity']}%"),
                    ("Wind Speed", f"{weather_data['windSpeed']} km/h"),
                    ("Precipitation", f"{weather_data['precipitation']} mm")
                ]
                
                for col, (label, value) in zip([col1, col2, col3, col4], metrics):
                    with col:
                        st.metric(label, value)
                
                # Weather alerts
                if weather_data['humidity'] > 80:
                    st.warning("⚠️ High humidity detected - Monitor for disease risk")
                if weather_data['precipitation'] > 10:
                    st.warning("⚠️ Significant rainfall - Check drainage systems")
        
        with tabs[1]:
            # Growth stage analysis
            growth_stage = analyzer.calculate_growth_stage(
                datetime.combine(sowing_date, datetime.min.time()),
                selected_crop
            )
            st.info(f"Current Growth Stage: {growth_stage}")
            
            # Add growth stage timeline
            stages = list(analyzer.CROPS[selected_crop]["stages"].keys())
            current_stage_idx = stages.index(growth_stage)
            
            # Create progress bars for each stage
            for idx, stage in enumerate(stages):
                if idx < current_stage_idx:
                    st.progress(1.0, text=stage)
                elif idx == current_stage_idx:
                    st.progress(0.5, text=f"Current: {stage}")
                else:
                    st.progress(0.0, text=stage)
        
        with tabs[2]:
            # Fertilizer recommendations
            npk_req = analyzer.calculate_npk_requirements(
                selected_crop, 
                location, 
                acres,
                growth_stage
            )
            
            st.subheader("Fertilizer Recommendations")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Nitrogen (N)", f"{npk_req['N']:.1f} kg/acre")
            with col2:
                st.metric("Phosphorus (P)", f"{npk_req['P']:.1f} kg/acre")
            with col3:
                st.metric("Potassium (K)", f"{npk_req['K']:.1f} kg/acre")
        
        with tabs[3]:
            # Disease analysis
            with st.spinner(f'Analyzing diseases for {selected_crop}...'):
                analysis_text = analyzer.query_gemini_api(selected_crop, selected_language)
                
                if "Error:" not in analysis_text:
                    st.markdown(analysis_text)
                    
                    # Generate audio file
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    audio_file = f"crop_disease_analysis_{selected_crop.lower()}_{timestamp}.mp3"
                    
                    with st.spinner('Generating audio...'):
                        asyncio.run(analyzer.text_to_speech(analysis_text, audio_file, selected_language))
                    
                    # Audio player and download
                    with open(audio_file, 'rb') as audio_data:
                        st.audio(audio_data.read(), format='audio/mp3')
                        st.markdown(
                            get_binary_file_downloader_html(audio_file, 'Download Audio Summary'),
                            unsafe_allow_html=True
                        )
                    
                    # Cleanup
                    try:
                        os.remove(audio_file)
                    except:
                        pass
                else:
                    st.error(analysis_text)

if __name__ == "__main__":
    main()
