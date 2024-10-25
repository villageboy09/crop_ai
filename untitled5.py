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
        self.API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
        self.API_KEY = st.secrets["gemini"]["api_key"]
        self.WEATHER_API_KEY = st.secrets["visual_crossing"]["api_key"]
        self.IPAPI_URL = "https://ipapi.co/json/"
        
        self.VOICES = {
            'Telugu': 'te-IN-ShrutiNeural',
            'English': 'en-US-AriaNeural',
            'Hindi': 'hi-IN-SwaraNeural'
        }
        
        # Updated CROPS dictionary with actual image URLs and disease seasons
        self.CROPS = {
            "Tomato": {
                "image": "https://example.com/tomato.jpg",  # Replace with actual image URLs
                "diseases": {
                    "summer": ["Early Blight", "Leaf Spot"],
                    "winter": ["Late Blight", "Powdery Mildew"],
                    "monsoon": ["Bacterial Wilt", "Fungal Rot"]
                }
            },
            "Potato": {
                "image": "https://example.com/potato.jpg",
                "diseases": {
                    "summer": ["Common Scab", "Black Scurf"],
                    "winter": ["Late Blight", "Early Blight"],
                    "monsoon": ["Bacterial Wilt", "Soft Rot"]
                }
            }
            # Add more crops with their respective seasonal diseases
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
            
            # Clean location string and construct the full URL
            clean_location = location.replace(' ', '').replace(',', '/')
            url = f"{base_url}/{clean_location}/today"
            
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
            
    def get_user_location(self):
        """Auto-fetch user's location using IP-API"""
        try:
            response = requests.get(self.IPAPI_URL)
            if response.status_code == 200:
                data = response.json()
                return {
                    'city': data.get('city', ''),
                    'region': data.get('region', ''),
                    'country': data.get('country_name', ''),
                    'latitude': data.get('latitude', 0),
                    'longitude': data.get('longitude', 0)
                }
            return None
        except Exception as e:
            st.error(f"Error fetching location: {str(e)}")
            return None

    def get_current_season(self):
        """Determine current season based on month"""
        month = datetime.now().month
        if 3 <= month <= 5:
            return "summer"
        elif 6 <= month <= 9:
            return "monsoon"
        else:
            return "winter"

    def query_gemini_api(self, crop, language, season):
        """Query Gemini API for season-specific crop disease information"""
        try:
            # Get seasonal diseases for the crop
            seasonal_diseases = self.CROPS[crop]["diseases"][season]
            diseases_list = ", ".join(seasonal_diseases)
            
            prompt = f"""
            Analyze and provide detailed information about the following seasonal diseases 
            in {crop} cultivation during {season} season: {diseases_list}
            
            For each disease, include:
            1. Symptoms
            2. Favorable conditions
            3. Prevention methods
            4. Treatment options
            
            Provide the response in {language} language.
            Format the response in a clear, structured way.
            """

            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }

            url = f"{self.API_URL}?key={self.API_KEY}"
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return f"Error: API returned status code {response.status_code}"

        except Exception as e:
            return f"Error querying API: {str(e)}"

def create_crop_card(crop_name, image_url):
    """Create a styled card for crop selection"""
    card_html = f"""
        <div style="
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 10px;
            margin: 5px;
            text-align: center;
            cursor: pointer;
            transition: transform 0.2s;
            hover: transform: scale(1.05);
        ">
            <img src="{image_url}" style="width: 100%; height: 150px; object-fit: cover; border-radius: 4px;">
            <h3 style="margin-top: 10px;">{crop_name}</h3>
        </div>
    """
    return card_html

def main():
    st.set_page_config(page_title="Smart Crop Disease Analyzer", page_icon="🌱", layout="wide")
    st.title("🌱 Smart Crop Disease Analyzer")
    
    analyzer = StreamlitCropDiseaseAnalyzer()

    # Auto-fetch user location
    user_location = analyzer.get_user_location()
    if user_location:
        location_str = f"{user_location['city']}, {user_location['region']}, {user_location['country']}"
        st.sidebar.success(f"📍 Location detected: {location_str}")
    else:
        location_str = st.sidebar.text_input("Enter your location", "Delhi, India")

    # Language selection
    selected_language = st.sidebar.selectbox("Select Language", list(analyzer.VOICES.keys()))

    # Get current season
    current_season = analyzer.get_current_season()
    st.sidebar.info(f"Current Season: {current_season.capitalize()}")

    # Create crop selection grid
    st.subheader("Select a Crop for Analysis")
    cols = st.columns(4)  # Create 4 columns for the grid
    
    selected_crop = None
    for idx, (crop, data) in enumerate(analyzer.CROPS.items()):
        with cols[idx % 4]:
            card_html = create_crop_card(crop, data["image"])
            if st.markdown(card_html, unsafe_allow_html=True):
                selected_crop = crop

    if selected_crop:
        st.markdown(f"## Analysis for {selected_crop}")

        # Fetch and display weather data
        weather_data = analyzer.get_weather_data(location_str)
        if weather_data:
            st.subheader("Current Weather Conditions")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Temperature", f"{weather_data['temperature']}°C")
            with col2:
                st.metric("Humidity", f"{weather_data['humidity']}%")
            with col3:
                st.metric("Wind Speed", f"{weather_data['windSpeed']} km/h")
            with col4:
                st.metric("Precipitation", f"{weather_data['precipitation']} mm")

            # Weather alerts
            if weather_data['humidity'] > 80:
                st.warning("⚠️ High humidity alert - Increased disease risk")

        # Get and display season-specific disease analysis
        with st.spinner(f'Analyzing seasonal diseases for {selected_crop}...'):
            analysis_text = analyzer.query_gemini_api(
                selected_crop, 
                selected_language,
                current_season
            )
            
            if "Error:" not in analysis_text:
                st.markdown(analysis_text)
                
                # Generate audio summary
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                audio_file = f"crop_analysis_{selected_crop.lower()}_{timestamp}.mp3"
                
                with st.spinner('Generating audio summary...'):
                    asyncio.run(analyzer.text_to_speech(
                        analysis_text,
                        audio_file,
                        selected_language
                    ))
                
                # Audio player and download option
                with open(audio_file, 'rb') as audio_data:
                    st.audio(audio_data.read(), format='audio/mp3')
                    st.download_button(
                        label="Download Audio Summary",
                        data=audio_data,
                        file_name=audio_file,
                        mime="audio/mp3"
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
