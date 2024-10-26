import streamlit as st
import asyncio
import edge_tts
from datetime import datetime
import requests
import os
import base64
from googletrans import Translator
import json
from PIL import Image

class StreamlitCropDiseaseAnalyzer:
    def __init__(self):
        self.API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
        self.API_KEY = st.secrets["gemini"]["api_key"]
        self.WEATHER_API_KEY = st.secrets["visual_crossing"]["api_key"]
        self.VOICES = {
            'Telugu': 'te-IN-ShrutiNeural',
            'English': 'en-US-AriaNeural',
            'Hindi': 'hi-IN-SwaraNeural'
        }
        
        self.CROPS = {
            "Rice": {
                "image": "https://cdn.britannica.com/89/140889-050-EC3F00BF/Ripening-heads-rice-Oryza-sativa.jpg",
                "description": "A staple food crop grown in flooded fields",
                "stages": {
                    "Seedling": {"duration": 25, "npk_multiplier": 0.4},
                    "Vegetative": {"duration": 50, "npk_multiplier": 0.9},
                    "Flowering": {"duration": 30, "npk_multiplier": 1.2},
                    "Maturing": {"duration": 35, "npk_multiplier": 1.4}
                }
            },
            "Maize": {
                "image": "https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcTSQTwY5H90hpRERbth6Y70s48hYKQQ3EimRbhVpGTe_zCHc0II",
                "description": "Also known as corn, a versatile grain crop",
                "stages": {
                    "Seedling": {"duration": 20, "npk_multiplier": 0.5},
                    "Vegetative": {"duration": 45, "npk_multiplier": 1.0},
                    "Flowering": {"duration": 30, "npk_multiplier": 1.3},
                    "Maturing": {"duration": 35, "npk_multiplier": 1.6}
                }
            },
            "Sorghum": {
                "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQFyoo17z6OwjPUWoBWrKNMEfJf1Cd4wpx5atIJGCgtZU8E9zPQ",
                "description": "Drought-resistant cereal grain",
                "stages": {
                    "Seedling": {"duration": 22, "npk_multiplier": 0.5},
                    "Vegetative": {"duration": 40, "npk_multiplier": 1.0},
                    "Flowering": {"duration": 25, "npk_multiplier": 1.2},
                    "Maturing": {"duration": 30, "npk_multiplier": 1.4}
                }
            },
            "Cotton": {
                "image": "https://cdn.britannica.com/18/156618-050-39339EA2/cotton-harvesting.jpg",
                "description": "Important fiber crop",
                "stages": {
                    "Seedling": {"duration": 25, "npk_multiplier": 0.6},
                    "Vegetative": {"duration": 45, "npk_multiplier": 1.1},
                    "Flowering": {"duration": 30, "npk_multiplier": 1.5},
                    "Boll Formation": {"duration": 35, "npk_multiplier": 1.8}
                }
            },
            "Groundnut": {
                "image": "https://encrypted-tbn.gstatic.com/images?q=tbn:ANd9GcQX4-OuVBESIfeRVCsFnLstkRLvDRAUpeSlGA&s",
                "description": "Legume crop rich in protein and oil",
                "stages": {
                    "Seedling": {"duration": 20, "npk_multiplier": 0.5},
                    "Vegetative": {"duration": 40, "npk_multiplier": 1.0},
                    "Flowering": {"duration": 25, "npk_multiplier": 1.2},
                    "Pod Formation": {"duration": 30, "npk_multiplier": 1.5}
                }
            }
        }

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
        }

        self.translator = Translator()

    def get_weather_data(self, location):
        try:
            formatted_location = location.replace(" ", "%20")
            url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{formatted_location}/today?unitGroup=metric&key={self.WEATHER_API_KEY}&contentType=json"
            response = requests.get(url)
            if response.status_code != 200:
                st.error(f"Weather API returned status code: {response.status_code}")
                return None
            data = response.json()
            current_conditions = data.get('days', [{}])[0]
            return {
                'temperature': round(current_conditions.get('temp', 0), 1),
                'humidity': round(current_conditions.get('humidity', 0), 1),
                'windSpeed': round(current_conditions.get('windspeed', 0), 1),
                'precipitation': round(current_conditions.get('precip', 0), 2)
            }
        except requests.RequestException as e:
            st.error(f"Error fetching weather data: {str(e)}")
            return None
        except (KeyError, IndexError, ValueError) as e:
            st.error(f"Error parsing weather data: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Unexpected error getting weather data: {str(e)}")
            return None

    def calculate_growth_stage(self, sowing_date, crop):
        if crop not in self.CROPS:
            return "Unknown Stage"
        days_since_sowing = (datetime.now() - sowing_date).days
        stages = self.CROPS[crop]["stages"]
        days_accumulated = 0
        for stage, info in stages.items():
            days_accumulated += info["duration"]
            if days_since_sowing <= days_accumulated:
                return stage
        return list(stages.keys())[-1]

    def calculate_npk_requirements(self, crop, location, acres, growth_stage):
        if crop not in self.BASE_NPK_REQUIREMENTS:
            return {"N": 0, "P": 0, "K": 0}
        base_npk = self.BASE_NPK_REQUIREMENTS[crop]
        region = self._determine_region(location)
        regional_multipliers = self.REGIONAL_NPK.get(region, {"N": 1.0, "P": 1.0, "K": 1.0})
        stage_multiplier = self.CROPS[crop]["stages"].get(growth_stage, {}).get("npk_multiplier", 1.0)
        npk_requirements = {
            nutrient: base_amount * regional_multipliers[nutrient] * stage_multiplier * acres
            for nutrient, base_amount in base_npk.items()
        }
        return npk_requirements

    def _determine_region(self, location):
        city_regions = {
            'delhi': 'North',
            'mumbai': 'West',
            'kolkata': 'East',
            'chennai': 'South',
            'bangalore': 'South',
            'hyderabad': 'South',
            'ahmedabad': 'West',
            'pune': 'West',
            'jaipur': 'North',
            'lucknow': 'North',
            'bhopal': 'Central',
            'patna': 'East'
        }
        city = location.split(',')[0].strip().lower()
        return city_regions.get(city, 'Central')

    def query_gemini(self, input_text):
        headers = {
            'Authorization': f'Bearer {self.API_KEY}',
            'Content-Type': 'application/json'
        }
        data = {
            "prompt": input_text,
            "maxTokens": 300,
            "temperature": 0.7
        }
        response = requests.post(self.API_URL, headers=headers, json=data)
        if response.status_code != 200:
            st.error(f"Gemini API returned status code: {response.status_code}")
            return None
        response_data = response.json()
        return response_data.get('text', '')

    async def text_to_speech(self, text, language):
        voice = self.VOICES.get(language, self.VOICES['English'])
        communicate = edge_tts.Communicate(text, voice=voice)
        await communicate.save("audio.mp3")
        with open("audio.mp3", "rb") as audio_file:
            b64_audio = base64.b64encode(audio_file.read()).decode()
        return f'''
            <audio controls>
                <source src="data:audio/mpeg;base64,{b64_audio}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
        '''

    def main(self):
        st.title("Crop Disease Analyzer")
        st.sidebar.title("Navigation")
        selected = st.sidebar.selectbox("Choose an option", ["Analyze Crop Disease", "Weather Data", "NPK Requirements"])

        if selected == "Analyze Crop Disease":
            crop = st.selectbox("Select Crop", list(self.CROPS.keys()))
            sowing_date = st.date_input("Select Sowing Date", datetime.now())
            location = st.text_input("Enter Location")

            if st.button("Analyze"):
                growth_stage = self.calculate_growth_stage(sowing_date, crop)
                st.write(f"Current Growth Stage: {growth_stage}")
                st.write(self.CROPS[crop]["description"])
                st.image(self.CROPS[crop]["image"])

                disease_input = st.text_input("Describe the symptoms")
                if st.button("Get Disease Analysis"):
                    analysis_result = self.query_gemini(disease_input)
                    if analysis_result:
                        st.write("Disease Analysis Result:")
                        st.write(analysis_result)

        elif selected == "Weather Data":
            location = st.text_input("Enter Location")
            if st.button("Get Weather Data"):
                weather_data = self.get_weather_data(location)
                if weather_data:
                    st.write("Weather Data:")
                    st.write(f"Temperature: {weather_data['temperature']}°C")
                    st.write(f"Humidity: {weather_data['humidity']}%")
                    st.write(f"Wind Speed: {weather_data['windSpeed']} km/h")
                    st.write(f"Precipitation: {weather_data['precipitation']} mm")

        elif selected == "NPK Requirements":
            crop = st.selectbox("Select Crop", list(self.CROPS.keys()))
            acres = st.number_input("Enter Acres", min_value=1, value=1)
            location = st.text_input("Enter Location")
            growth_stage = st.selectbox("Select Growth Stage", list(self.CROPS[crop]["stages"].keys()))

            if st.button("Calculate NPK"):
                npk_requirements = self.calculate_npk_requirements(crop, location, acres, growth_stage)
                st.write(f"NPK Requirements for {crop}:")
                st.write(f"Nitrogen: {npk_requirements['N']} kg")
                st.write(f"Phosphorus: {npk_requirements['P']} kg")
                st.write(f"Potassium: {npk_requirements['K']} kg")

        st.sidebar.header("Text to Speech")
        text = st.text_input("Enter text for TTS")
        language = st.selectbox("Select Language", list(self.VOICES.keys()))
        if st.button("Convert to Speech"):
            audio_html = asyncio.run(self.text_to_speech(text, language))
            st.markdown(audio_html, unsafe_allow_html=True)

if __name__ == "__main__":
    analyzer = StreamlitCropDiseaseAnalyzer()
    analyzer.main()
