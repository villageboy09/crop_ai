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
        # API configurations
        self.API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
        self.API_KEY = st.secrets["gemini"]["api_key"]
        self.WEATHER_API_KEY = st.secrets["visual_crossing"]["api_key"]
        self.VOICES = {
            'Telugu': 'te-IN-ShrutiNeural',
            'English': 'en-US-AriaNeural',
            'Hindi': 'hi-IN-SwaraNeural'
        }
        
        # Crop data with growth stages and NPK requirements
        self.CROPS = {
            "Tomato": {
                "image": "tomato.jpg",
                "stages": {
                    "Seedling": {"duration": 20, "npk_multiplier": 0.5},
                    "Vegetative": {"duration": 40, "npk_multiplier": 1.0},
                    "Flowering": {"duration": 30, "npk_multiplier": 1.2},
                    "Fruiting": {"duration": 40, "npk_multiplier": 1.5}
                }
            },
            "Potato": {
                "image": "potato.jpg",
                "stages": {
                    "Sprouting": {"duration": 25, "npk_multiplier": 0.4},
                    "Vegetative": {"duration": 30, "npk_multiplier": 1.0},
                    "Tuber Initiation": {"duration": 35, "npk_multiplier": 1.3},
                    "Tuber Bulking": {"duration": 40, "npk_multiplier": 1.4}
                }
            },
            "Rice": {
                "image": "rice.jpg",
                "stages": {
                    "Seedling": {"duration": 20, "npk_multiplier": 0.6},
                    "Tillering": {"duration": 30, "npk_multiplier": 1.1},
                    "Panicle Initiation": {"duration": 30, "npk_multiplier": 1.2},
                    "Flowering": {"duration": 35, "npk_multiplier": 1.0},
                    "Ripening": {"duration": 30, "npk_multiplier": 0.8}
                }
            },
            "Wheat": {
                "image": "wheat.jpg",
                "stages": {
                    "Germination": {"duration": 15, "npk_multiplier": 0.5},
                    "Tillering": {"duration": 30, "npk_multiplier": 1.0},
                    "Stem Extension": {"duration": 30, "npk_multiplier": 1.2},
                    "Heading": {"duration": 25, "npk_multiplier": 1.1},
                    "Ripening": {"duration": 30, "npk_multiplier": 0.7}
                }
            },
            "Cotton": {
                "image": "cotton.jpg",
                "stages": {
                    "Emergence": {"duration": 15, "npk_multiplier": 0.4},
                    "Vegetative": {"duration": 35, "npk_multiplier": 1.0},
                    "Flowering": {"duration": 40, "npk_multiplier": 1.3},
                    "Boll Development": {"duration": 45, "npk_multiplier": 1.2},
                    "Maturity": {"duration": 25, "npk_multiplier": 0.6}
                }
            }
        }

        # Regional NPK multipliers
        self.REGIONAL_NPK = {
            "North": {"N": 1.2, "P": 0.8, "K": 1.0},
            "South": {"N": 0.9, "P": 1.1, "K": 1.2},
            "East": {"N": 1.1, "P": 0.9, "K": 0.8},
            "West": {"N": 1.0, "P": 1.0, "K": 1.0},
            "Central": {"N": 1.1, "P": 1.0, "K": 0.9}
        }

        # Base NPK requirements for crops (per acre)
        self.BASE_NPK_REQUIREMENTS = {
            "Tomato": {"N": 120, "P": 80, "K": 100},
            "Potato": {"N": 150, "P": 100, "K": 120},
            "Rice": {"N": 100, "P": 50, "K": 50},
            "Wheat": {"N": 120, "P": 60, "K": 40},
            "Cotton": {"N": 140, "P": 70, "K": 70}
        }

        self.translator = Translator()

    async def generate_audio_analysis(self, text, language, crop_name):
        """Generate audio file from analysis text"""
        try:
            output_file = f"{crop_name}_analysis.mp3"
            clean_text = " ".join(word for word in text.split() if not word.startswith("#"))
            communicate = edge_tts.Communicate(clean_text, self.VOICES[language])
            await communicate.save(output_file)
            return output_file
        except Exception as e:
            st.error(f"Error during audio generation: {str(e)}")
            return None

    # [Rest of the methods remain the same as in your original code]
    def get_weather_data(self, location):
        """Fetch weather data from Visual Crossing API"""
        try:
            base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
            params = {
                'unitGroup': 'metric',
                'key': self.WEATHER_API_KEY,
                'contentType': 'json',
                'include': 'current,days',
                'elements': 'temp,humidity,conditions,precip,cloudcover,windspeed,pressure'
            }
            url = f"{base_url}/{location}/today"
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
        """Calculate the current growth stage based on sowing date"""
        today = datetime.now().date()
        days_since_sowing = (today - sowing_date).days
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
        """Determine the region based on location (simplified example)"""
        # This is a simplified version. You might want to implement a more sophisticated
        # region determination logic based on your needs
        location = location.lower()
        if any(city in location for city in ["delhi", "chandigarh", "lucknow"]):
            return "North"
        elif any(city in location for city in ["mumbai", "ahmedabad", "pune"]):
            return "West"
        elif any(city in location for city in ["chennai", "bangalore", "hyderabad"]):
            return "South"
        elif any(city in location for city in ["kolkata", "patna", "guwahati"]):
            return "East"
        else:
            return "Central"

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
            headers = {"Content-Type": "application/json"}
            base_prompt = f"""
            Analyze and provide detailed information about common diseases in {crop} cultivation.
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

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """Generate a link for downloading a binary file"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href

def main():
    st.set_page_config(page_title="Enhanced Crop Disease Analyzer", page_icon="🌱", layout="wide")
    st.title("🌱 Enhanced Crop Disease Analyzer")

    analyzer = StreamlitCropDiseaseAnalyzer()

    # Sidebar inputs
    selected_language = st.sidebar.selectbox("Select Language", list(analyzer.VOICES.keys()))
    location = st.sidebar.text_input("Enter your location (City, State)", "Delhi, India")
    acres = st.sidebar.number_input("Enter area in acres", min_value=0.1, value=1.0)
    sowing_date = st.sidebar.date_input("Select Sowing Date", datetime.now() - timedelta(days=30))
    
    selected_crop = st.selectbox("Select Crop", list(analyzer.CROPS.keys()))

    if st.button("Analyze Crop"):
        with st.spinner("Analyzing crop and generating audio..."):
            st.markdown(f"## Analysis for {selected_crop}")

            # Weather data
            weather_data = analyzer.get_weather_data(location)
            if weather_data:
                st.markdown(f"### Current Weather in {location}:")
                st.markdown(f"- Temperature: {weather_data['temperature']}°C")
                st.markdown(f"- Humidity: {weather_data['humidity']}%")
                st.markdown(f"- Conditions: {weather_data['conditions']}")

            # Growth stage calculation
            growth_stage = analyzer.calculate_growth_stage(sowing_date, selected_crop)
            st.markdown(f"### Current Growth Stage: {growth_stage}")

            # NPK requirements
            npk_requirements = analyzer.calculate_npk_requirements(selected_crop, location, acres, growth_stage)
            st.markdown(f"### NPK Requirements for {acres} acre(s):")
            st.markdown(f"- Nitrogen (N): {npk_requirements['N']:.2f} kg")
            st.markdown(f"- Phosphorus (P): {npk_requirements['P']:.2f} kg")
            st.markdown(f"- Potassium (K): {npk_requirements['K']:.2f} kg")

            # Weather-based recommendations
            if weather_data:
                recommendations = analyzer.get_weather_based_recommendations(weather_data, selected_crop, growth_stage)
                if recommendations:
                    st.markdown(f"### Weather-Based Recommendations:")
                    for rec in recommendations:
                        st.markdown(f"- {rec}")

            # Crop disease analysis using Gemini API
            st.markdown(f"### Disease Analysis for {selected_crop}:")
            disease_analysis = analyzer.query_gemini_api(selected_crop, selected_language)
            st.markdown(disease_analysis)

            # Automatically generate audio file
            output_file = asyncio.run(analyzer.generate_audio_analysis(
                disease_analysis, 
                selected_language, 
                selected_crop
            ))
            
            if output_file:
                st.success("🔊 Audio analysis has been generated!")
                st.audio(output_file)
                st.markdown("### Download Audio Analysis")
                st.markdown(
                    get_binary_file_downloader_html(output_file, f"{selected_crop} Audio Analysis"), 
                    unsafe_allow_html=True
                )
            else:
                st.error("Failed to generate audio analysis. Please try again.")

if __name__ == "__main__":
    main()
