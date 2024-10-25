import streamlit as st
import asyncio
import edge_tts
from datetime import datetime, timedelta
import requests
import os
import base64
from googletrans import Translator
import json

class StreamlitCropDiseaseAnalyzer:
    def __init__(self):
        # API and voice setup
        self.API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
        self.API_KEY = st.secrets["gemini"]["api_key"]
        self.WEATHER_API_KEY = st.secrets["visual_crossing"]["api_key"]
        self.VOICES = {
            'Telugu': 'te-IN-ShrutiNeural',
            'English': 'en-US-AriaNeural',
            'Hindi': 'hi-IN-SwaraNeural'
        }
        
        # CROPS dictionary with disease seasonality
        self.CROPS = {
            "Tomato": {
                "image": "tomato.jpg",
                "stages": {
                    "Seedling": {"duration": 20, "npk_multiplier": 0.5},
                    "Vegetative": {"duration": 40, "npk_multiplier": 1.0},
                    "Flowering": {"duration": 30, "npk_multiplier": 1.2},
                    "Fruiting": {"duration": 40, "npk_multiplier": 1.5}
                },
                "seasonal_diseases": {
                    1: ["Early Blight", "Frost Damage"],  # January
                    2: ["Early Blight", "Powdery Mildew"],
                    3: ["Early Blight", "Leaf Curl"],
                    4: ["Leaf Spot", "Blossom End Rot"],
                    5: ["Bacterial Wilt", "Leaf Spot"],
                    6: ["Bacterial Wilt", "Fusarium Wilt"],
                    7: ["Late Blight", "Bacterial Spot"],
                    8: ["Late Blight", "Bacterial Spot"],
                    9: ["Late Blight", "Fusarium Wilt"],
                    10: ["Early Blight", "Bacterial Spot"],
                    11: ["Early Blight", "Leaf Curl"],
                    12: ["Early Blight", "Frost Damage"]
                }
            },
            # Additional crops can be added here similarly
        }
        
        # NPK region-specific and base data
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
            "Rice": {"N": 100, "P": 50, "K": 50},
            "Wheat": {"N": 120, "P": 60, "K": 40},
            "Cotton": {"N": 140, "P": 70, "K": 70}
        }
        
        self.translator = Translator()

    def get_user_location(self):
        """Fetch user's location using IP-API"""
        try:
            response = requests.get('http://ip-api.com/json/')
            if response.status_code == 200:
                data = response.json()
                return f"{data['city']}, {data['country']}"
            return None
        except Exception as e:
            st.error(f"Error fetching location: {str(e)}")
            return None

    def query_gemini_api(self, crop, language, month):
        """Query Gemini API for month-specific crop disease information"""
        try:
            headers = {"Content-Type": "application/json"}
            
            # Get month-specific diseases
            current_diseases = self.CROPS[crop]["seasonal_diseases"].get(month, [])
            diseases_str = ", ".join(current_diseases)
            
            base_prompt = f"""
            Analyze and provide detailed information about the following specific diseases 
            in {crop} cultivation that are common during this month: {diseases_str}
            
            For each disease, include:
            1. Disease name
            2. Symptoms
            3. Favorable conditions
            4. Prevention methods
            5. Treatment options
            
            Provide the response in {language} language.
            """
            
            payload = {"contents": [{"parts": [{"text": base_prompt}]}]}
            url = f"{self.API_URL}?key={self.API_KEY}"
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return f"Error: API returned status code {response.status_code}"
        except Exception as e:
            return f"Error querying API: {str(e)}"

    def calculate_growth_stage(self, sowing_date, crop):
        """Calculate current growth stage based on sowing date"""
        today = datetime.now()
        days_since_sowing = (today - sowing_date).days
        
        stages = self.CROPS[crop]["stages"]
        total_days = sum(stage["duration"] for stage in stages.values())
        
        # Determine current growth stage
        current_days = 0
        for stage, data in stages.items():
            current_days += data["duration"]
            if days_since_sowing < current_days:
                return stage
        return "Mature"

    def calculate_npk_requirements(self, crop, location, acres, growth_stage):
        """Calculate NPK requirements based on crop and growth stage"""
        base_npk = self.BASE_NPK_REQUIREMENTS[crop]
        
        # Get region from location (simplified for this example)
        region = "North"  # You may want to implement a real region lookup based on location
        
        npk_multiplier = self.CROPS[crop]["stages"][growth_stage]["npk_multiplier"]
        
        # Calculate NPK requirements
        N = base_npk["N"] * npk_multiplier * acres
        P = base_npk["P"] * npk_multiplier * acres
        K = base_npk["K"] * npk_multiplier * acres
        
        return {"N": N, "P": P, "K": K}

    async def generate_audio_analysis(self, analysis_text, language, crop):
        """Generate audio analysis using edge-tts"""
        try:
            voice = self.VOICES[language]
            output_file = f"{crop}_analysis.wav"
            communicate = edge_tts.Communicate(analysis_text, voice=voice)
            await communicate.save(output_file)
            return output_file
        except Exception as e:
            st.error(f"Error generating audio: {str(e)}")
            return None

    def get_weather_data(self, location):
        """Fetch weather data for the given location"""
        try:
            url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}?key={self.WEATHER_API_KEY}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return {
                    "temperature": data["currentConditions"]["temp"],
                    "humidity": data["currentConditions"]["humidity"],
                    "conditions": data["currentConditions"]["conditions"]
                }
            else:
                return None
        except Exception as e:
            st.error(f"Error fetching weather data: {str(e)}")
            return None

def main():
    st.set_page_config(page_title="Enhanced Crop Disease Analyzer", page_icon="🌱", layout="wide")
    st.title("🌱 Enhanced Crop Disease Analyzer")

    analyzer = StreamlitCropDiseaseAnalyzer()

    # Sidebar inputs
    selected_language = st.sidebar.selectbox("Select Language", list(analyzer.VOICES.keys()))
    
    # Auto-fetch location for weather data
    default_location = analyzer.get_user_location() or "Delhi, India"
    location = st.sidebar.text_input("Enter your location (City, State)", value=default_location)
    
    acres = st.sidebar.number_input("Enter area in acres", min_value=0.1, value=1.0)
    sowing_date = st.sidebar.date_input("Select Sowing Date", datetime.now() - timedelta(days=30))

    # Display crops as cards in a grid
    st.markdown("### Select Your Crop")
    cols = st.columns(3)  # Create 3 columns for the grid
    
    selected_crop = None
    for idx, (crop_name, crop_data) in enumerate(analyzer.CROPS.items()):
        with cols[idx % 3]:
            card = st.container()
            with card:
                st.image(crop_data["image"], caption=crop_name, use_column_width=True)
                if st.button(f"Select {crop_name}",
                if st.button(f"Select {crop_name}"):
                    selected_crop = crop_name

    if selected_crop:
        st.markdown(f"### Selected Crop: **{selected_crop}**")
        
        # Determine current growth stage
        growth_stage = analyzer.calculate_growth_stage(sowing_date, selected_crop)
        st.write(f"Current Growth Stage: {growth_stage}")

        # Get current month
        current_month = datetime.now().month

        # Query the Gemini API for disease information
        disease_info = analyzer.query_gemini_api(selected_crop, selected_language, current_month)
        st.write(disease_info)

        # Calculate NPK requirements
        npk_requirements = analyzer.calculate_npk_requirements(selected_crop, location, acres, growth_stage)
        st.markdown("### NPK Requirements")
        st.write(f"Nitrogen (N): {npk_requirements['N']} kg")
        st.write(f"Phosphorus (P): {npk_requirements['P']} kg")
        st.write(f"Potassium (K): {npk_requirements['K']} kg")

        # Generate weather data
        weather_data = analyzer.get_weather_data(location)
        if weather_data:
            st.markdown("### Current Weather Conditions")
            st.write(f"Temperature: {weather_data['temperature']} °C")
            st.write(f"Humidity: {weather_data['humidity']} %")
            st.write(f"Conditions: {weather_data['conditions']}")

        # Generate audio analysis
        audio_file = asyncio.run(analyzer.generate_audio_analysis(disease_info, selected_language, selected_crop))
        if audio_file:
            st.markdown("### Audio Analysis")
            audio_file = open(audio_file, "rb")
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/wav")

if __name__ == "__main__":
    main()
