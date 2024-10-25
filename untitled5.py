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
        # Previous configurations remain the same
        self.API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
        self.API_KEY = st.secrets["gemini"]["api_key"]
        self.WEATHER_API_KEY = st.secrets["visual_crossing"]["api_key"]
        self.VOICES = {
            'Telugu': 'te-IN-ShrutiNeural',
            'English': 'en-US-AriaNeural',
            'Hindi': 'hi-IN-SwaraNeural'
        }
        
        # Updated CROPS dictionary with disease seasonality
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
            # Add similar seasonal disease data for other crops
            # ... [other crops data remains the same]
        }
        
        # Rest of the initialization remains the same
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

    # [Other methods remain the same]

def main():
    st.set_page_config(page_title="Enhanced Crop Disease Analyzer", page_icon="🌱", layout="wide")
    st.title("🌱 Enhanced Crop Disease Analyzer")

    analyzer = StreamlitCropDiseaseAnalyzer()

    # Sidebar inputs
    selected_language = st.sidebar.selectbox("Select Language", list(analyzer.VOICES.keys()))
    
    # Auto-fetch location
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
                st.image(crop_data["image"], caption="", use_column_width=True)
                if st.button(f"Select {crop_name}", key=f"btn_{crop_name}"):
                    selected_crop = crop_name

    if selected_crop:
        st.success(f"Selected crop: {selected_crop}")
        
        if st.button("Analyze Crop"):
            with st.spinner("Analyzing crop and generating audio..."):
                current_month = datetime.now().month
                
                # [Rest of the analysis code remains the same, but uses current_month]
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
                npk_requirements = analyzer.calculate_npk_requirements(
                    selected_crop, location, acres, growth_stage
                )
                st.markdown(f"### NPK Requirements for {acres} acre(s):")
                st.markdown(f"- Nitrogen (N): {npk_requirements['N']:.2f} kg")
                st.markdown(f"- Phosphorus (P): {npk_requirements['P']:.2f} kg")
                st.markdown(f"- Potassium (K): {npk_requirements['K']:.2f} kg")

                # Weather-based recommendations
                if weather_data:
                    recommendations = analyzer.get_weather_based_recommendations(
                        weather_data, selected_crop, growth_stage
                    )
                    if recommendations:
                        st.markdown(f"### Weather-Based Recommendations:")
                        for rec in recommendations:
                            st.markdown(f"- {rec}")

                # Month-specific disease analysis
                st.markdown(f"### Disease Analysis for {selected_crop} (Current Month):")
                disease_analysis = analyzer.query_gemini_api(
                    selected_crop, selected_language, current_month
                )
                st.markdown(disease_analysis)

                # Generate audio analysis
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
                        get_binary_file_downloader_html(
                            output_file, 
                            f"{selected_crop} Audio Analysis"
                        ),
                        unsafe_allow_html=True
                    )
                else:
                    st.error("Failed to generate audio analysis. Please try again.")

if __name__ == "__main__":
    main()
