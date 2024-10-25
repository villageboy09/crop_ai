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
            "Tomato": {
                "image": "https://picsum.photos/200/300",
                "stages": {
                    "Seedling": {"duration": 20, "npk_multiplier": 0.5},
                    "Vegetative": {"duration": 40, "npk_multiplier": 1.0},
                    "Flowering": {"duration": 30, "npk_multiplier": 1.2},
                    "Fruiting": {"duration": 40, "npk_multiplier": 1.5}
                }
            },
            # Add similar structure for other crops
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
            "Tomato": {"N": 120, "P": 80, "K": 100},
            "Potato": {"N": 150, "P": 100, "K": 120},
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

    # ... (keep existing methods like query_gemini_api, text_to_speech, etc.)

def main():
    st.set_page_config(page_title="Enhanced Crop Disease Analyzer", page_icon="🌱", layout="wide")
    st.title("🌱 Enhanced Crop Disease Analyzer")
    
    analyzer = StreamlitCropDiseaseAnalyzer()

    # Language selection
    selected_language = st.sidebar.selectbox("Select Language", list(analyzer.VOICES.keys()))

    # Location input
    location = st.sidebar.text_input("Enter your location (City, State)", "Delhi, India")
    acres = st.sidebar.number_input("Enter area in acres", min_value=0.1, value=1.0, step=0.1)
    
    # Date selection
    sowing_date = st.sidebar.date_input(
        "Select sowing date",
        datetime.now() - timedelta(days=30)
    )

    # Create crop selection grid
    st.subheader("Select a Crop")
    cols = st.columns(5)
    selected_crop = None
    
    for idx, (crop, data) in enumerate(analyzer.CROPS.items()):
        with cols[idx % 5]:
            if st.button(crop, key=f"crop_{idx}"):
                selected_crop = crop
            st.image(data["image"], caption=crop, use_column_width=True)

    if selected_crop:
        st.markdown(f"## Analysis for {selected_crop}")

        # Fetch and display weather data
        weather_data = analyzer.get_weather_data(location)
        if weather_data:
            st.subheader("Current Weather Conditions")
            
            # Create two rows of metrics for weather data
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Temperature", f"{weather_data['temperature']}°C")
            with col2:
                st.metric("Humidity", f"{weather_data['humidity']}%")
            with col3:
                st.metric("Wind Speed", f"{weather_data['windSpeed']} km/h")
            with col4:
                st.metric("Precipitation", f"{weather_data['precipitation']} mm")
                
            # Second row of weather metrics
            col5, col6, col7, col8 = st.columns(4)
            with col5:
                st.metric("Cloud Cover", f"{weather_data['cloudCover']}%")
            with col6:
                st.metric("Pressure", f"{weather_data['pressure']} mb")
            with col7:
                st.metric("Conditions", weather_data['conditions'])
            
            # Weather-based alerts
            if weather_data['humidity'] > 80:
                st.warning("⚠️ High humidity detected - Monitor for disease risk")
            if weather_data['precipitation'] > 10:
                st.warning("⚠️ Significant rainfall - Check drainage systems")

        # Calculate and display growth stage
        growth_stage = analyzer.calculate_growth_stage(
            datetime.combine(sowing_date, datetime.min.time()),
            selected_crop
        )
        st.info(f"Current Growth Stage: {growth_stage}")

        # Calculate and display NPK requirements
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

        # Display weather-based recommendations
        if weather_data:
            recommendations = analyzer.get_weather_based_recommendations(
                weather_data,
                selected_crop,
                growth_stage
            )
            if recommendations:
                st.subheader("Weather-based Recommendations")
                for rec in recommendations:
                    st.write(f"• {rec}")

        # Continue with disease analysis and audio generation
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
                        get_binary_file_downloader_html(audio_file, 'Audio Summary'),
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
