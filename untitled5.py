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
        
        # Enhanced crop data with stage-specific diseases
        self.CROPS = {
            "Rice": {
                "image": "https://cdn.britannica.com/89/140889-050-EC3F00BF/Ripening-heads-rice-Oryza-sativa.jpg",
                "stages": {
                    "Seedling": {
                        "duration": 25,
                        "npk_multiplier": 0.4,
                        "common_diseases": ["Seed Rot", "Seedling Blight", "Root Rot"]
                    },
                    "Vegetative": {
                        "duration": 50,
                        "npk_multiplier": 0.9,
                        "common_diseases": ["Bacterial Leaf Blight", "Leaf Blast", "Sheath Blight"]
                    },
                    "Flowering": {
                        "duration": 30,
                        "npk_multiplier": 1.2,
                        "common_diseases": ["Neck Blast", "False Smut", "Bacterial Leaf Streak"]
                    },
                    "Maturing": {
                        "duration": 35,
                        "npk_multiplier": 1.4,
                        "common_diseases": ["Grain Discoloration", "Brown Spot", "Stem Rot"]
                    }
                }
            },
            "Maize": {
                "image": "https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcTSQTwY5H90hpRERbth6Y70s48hYKQQ3EimRbhVpGTe_zCHc0II",
                "stages": {
                    "Seedling": {
                        "duration": 20,
                        "npk_multiplier": 0.5,
                        "common_diseases": ["Seed Rot", "Damping Off", "Seedling Blight"]
                    },
                    "Vegetative": {
                        "duration": 45,
                        "npk_multiplier": 1.0,
                        "common_diseases": ["Northern Leaf Blight", "Common Rust", "Gray Leaf Spot"]
                    },
                    "Flowering": {
                        "duration": 30,
                        "npk_multiplier": 1.3,
                        "common_diseases": ["Southern Rust", "Common Smut", "Head Smut"]
                    },
                    "Maturing": {
                        "duration": 35,
                        "npk_multiplier": 1.6,
                        "common_diseases": ["Ear Rot", "Stalk Rot", "Kernel Rot"]
                    }
                }
            }
            # Add similar structure for other crops
        }

        # Other existing configurations remain the same
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
        
        # Cache for disease analysis
        self.disease_analysis_cache = {}

    def get_stage_specific_diseases(self, crop, growth_stage):
        """Get list of common diseases for specific growth stage"""
        try:
            return self.CROPS[crop]["stages"][growth_stage]["common_diseases"]
        except KeyError:
            return []

    def background_disease_analysis(self, crop, growth_stage, language):
        """Perform background analysis of diseases specific to growth stage"""
        cache_key = f"{crop}_{growth_stage}_{language}"
        
        if cache_key in self.disease_analysis_cache:
            return self.disease_analysis_cache[cache_key]

        diseases = self.get_stage_specific_diseases(crop, growth_stage)
        if not diseases:
            return None

        try:
            headers = {
                "Content-Type": "application/json"
            }

            prompt = f"""
            Analyze the following diseases commonly found in {crop} during the {growth_stage} stage:
            {', '.join(diseases)}

            For each disease, provide:
            1. Brief description
            2. Key symptoms to look for at this growth stage
            3. Immediate control measures
            4. Prevention tips specific to {growth_stage} stage

            Keep the response concise and practical for farmers.
            Provide the response in {language} language.
            """

            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }

            url = f"{self.API_URL}?key={self.API_KEY}"
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                analysis = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                self.disease_analysis_cache[cache_key] = analysis
                return analysis
            else:
                return f"Error: API returned status code {response.status_code}"

        except Exception as e:
            return f"Error in disease analysis: {str(e)}"

    # Existing methods remain the same
    def get_weather_data(self, location):
        """Fetch weather data from Visual Crossing API"""
        # Implementation remains the same
        pass

    def calculate_growth_stage(self, sowing_date, crop):
        """Calculate current growth stage based on sowing date"""
        # Implementation remains the same
        pass

    def calculate_npk_requirements(self, crop, location, acres, growth_stage):
        """Calculate NPK requirements based on location, area, and growth stage"""
        # Implementation remains the same
        pass

    async def text_to_speech(self, text, output_file, language):
        """Convert text to speech using edge-tts"""
        # Implementation remains the same
        pass

def main():
    st.set_page_config(page_title="Enhanced Crop Disease Analyzer", page_icon="🌱", layout="wide")
    st.title("🌱 AI Based Kiosk Platform For Farmers")
    
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

        # Calculate growth stage
        growth_stage = analyzer.calculate_growth_stage(
            datetime.combine(sowing_date, datetime.min.time()),
            selected_crop
        )

        # Display current stage with progress
        st.subheader("Crop Growth Stage")
        stages = list(analyzer.CROPS[selected_crop]["stages"].keys())
        current_stage_idx = stages.index(growth_stage)
        progress = (current_stage_idx + 1) / len(stages)
        
        st.progress(progress)
        st.info(f"Current Growth Stage: {growth_stage}")

        # Weather data and recommendations
        col1, col2 = st.columns([2, 1])
        
        with col1:
            weather_data = analyzer.get_weather_data(location)
            if weather_data:
                st.subheader("Current Weather Conditions")
                
                # Weather metrics
                wcol1, wcol2, wcol3, wcol4 = st.columns(4)
                with wcol1:
                    st.metric("Temperature", f"{weather_data['temperature']}°C")
                with wcol2:
                    st.metric("Humidity", f"{weather_data['humidity']}%")
                with wcol3:
                    st.metric("Wind Speed", f"{weather_data['windSpeed']} km/h")
                with wcol4:
                    st.metric("Precipitation", f"{weather_data['precipitation']} mm")

        with col2:
            # NPK requirements
            npk_req = analyzer.calculate_npk_requirements(
                selected_crop, 
                location, 
                acres,
                growth_stage
            )
            
            st.subheader("Fertilizer Needs")
            st.metric("Nitrogen (N)", f"{npk_req['N']:.1f} kg/acre")
            st.metric("Phosphorus (P)", f"{npk_req['P']:.1f} kg/acre")
            st.metric("Potassium (K)", f"{npk_req['K']:.1f} kg/acre")

        # Disease analysis specific to growth stage
        st.subheader(f"Disease Analysis for {growth_stage} Stage")
        
        with st.spinner(f'Analyzing potential diseases for {selected_crop} in {growth_stage} stage...'):
            analysis = analyzer.background_disease_analysis(
                selected_crop,
                growth_stage,
                selected_language
            )
            
            if analysis and "Error:" not in analysis:
                st.markdown(analysis)
                
                # Generate audio file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                audio_file = f"stage_disease_analysis_{selected_crop.lower()}_{timestamp}.mp3"

                with st.spinner('Generating audio summary...'):
                    asyncio.run(analyzer.text_to_speech(analysis, audio_file, selected_language))

                # Audio player
                with open(audio_file, 'rb') as audio_data:
                    st.audio(audio_data.read(), format='audio/mp3')
                
                # Clean up audio file
                try:
                    os.remove(audio_file)
                except:
                    pass
            else:
                st.error("Unable to generate disease analysis at this time.")

        # Weather-based alerts
        if weather_data:
            st.subheader("Weather Alerts")
            if weather_data['humidity'] > 80:
                st.warning("⚠️ High humidity detected - Increased risk of fungal diseases")
            if weather_data['precipitation'] > 10:
                st.warning("⚠️ Significant rainfall - Monitor for water-borne diseases")
            if weather_data['temperature'] > 35:
                st.warning("⚠️ High temperature - Watch for heat stress symptoms")

if __name__ == "__main__":
    main()
