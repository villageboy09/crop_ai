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
        # Existing API configurations remain the same
        self.API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
        self.API_KEY = st.secrets["gemini"]["api_key"]
        self.WEATHER_API_KEY = st.secrets["visual_crossing"]["api_key"]
        self.VOICES = {
            'Telugu': 'te-IN-ShrutiNeural',
            'English': 'en-US-AriaNeural',
            'Hindi': 'hi-IN-SwaraNeural'
        }
        
        # Updated CROPS dictionary with standardized image dimensions
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
                "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQX4-OuVBESIfeRVCsFnLstkRLvDRAUpeSlGA&s",
                "description": "Legume crop rich in protein and oil",
                "stages": {
                    "Seedling": {"duration": 20, "npk_multiplier": 0.5},
                    "Vegetative": {"duration": 40, "npk_multiplier": 1.0},
                    "Flowering": {"duration": 25, "npk_multiplier": 1.2},
                    "Pod Formation": {"duration": 30, "npk_multiplier": 1.5}
                }
            }
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
            "Rice": {"N": 100, "P": 50, "K": 80},
            "Maize": {"N": 120, "P": 60, "K": 100},
            "Sorghum": {"N": 90, "P": 40, "K": 70},
            "Cotton": {"N": 110, "P": 70, "K": 90},
            "Groundnut": {"N": 80, "P": 60, "K": 70}
        }

        self.translator = Translator()

    def get_weather_data(self, location):
        """
        Fetches current weather data for a given location using Visual Crossing Weather API
        """
        try:
            # Format the location string for the URL
            formatted_location = location.replace(" ", "%20")
            
            # Construct the API URL
            url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{formatted_location}/today?unitGroup=metric&key={self.WEATHER_API_KEY}&contentType=json"
            
            # Make the API request
            response = requests.get(url)
            
            # Check if request was successful
            if response.status_code != 200:
                st.error(f"Weather API returned status code: {response.status_code}")
                return None
            
            # Parse the JSON response
            data = response.json()
            
            # Extract current conditions from the first day
            current_conditions = data.get('days', [{}])[0]
            
            # Return formatted weather data
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

def main():
    # ... previous code ...
    
    analyzer = StreamlitCropDiseaseAnalyzer()
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("### 📊 Configuration")
        selected_language = st.selectbox("Select Language", list(analyzer.VOICES.keys()))
        
        st.markdown("### 📍 Location Details")
        location = st.text_input("Enter your location (City, State)", "Delhi, India")
        acres = st.number_input("Enter area in acres", min_value=0.1, value=1.0, step=0.1)
    
    # Get weather data with proper error handling
    weather_data = analyzer.get_weather_data(location)
    
    if weather_data:
        st.markdown("### ☁️ Current Weather Conditions")
        cols = st.columns(4)
        
        with cols[0]:
            st.metric("Temperature", f"{weather_data['temperature']}°C")
        with cols[1]:
            st.metric("Humidity", f"{weather_data['humidity']}%")
        with cols[2]:
            st.metric("Wind Speed", f"{weather_data['windSpeed']} km/h")
        with cols[3]:
            st.metric("Precipitation", f"{weather_data['precipitation']} mm")
    else:
        st.warning("⚠️ Weather data is currently unavailable. Please check your location and try again.")

def calculate_growth_stage(self, sowing_date, crop):
    """
    Calculate the current growth stage based on sowing date and crop type.
    
    Args:
        sowing_date (datetime): The date when the crop was sown
        crop (str): The name of the crop
        
    Returns:
        str: Current growth stage of the crop
    """
    if crop not in self.CROPS:
        return "Unknown Stage"
        
    # Calculate days since sowing
    days_since_sowing = (datetime.now() - sowing_date).days
    
    # Get the growth stages for the specific crop
    stages = self.CROPS[crop]["stages"]
    
    # Calculate cumulative days for each stage
    days_accumulated = 0
    for stage, info in stages.items():
        days_accumulated += info["duration"]
        if days_since_sowing <= days_accumulated:
            return stage
            
    # If beyond all stages, return the last stage
    return list(stages.keys())[-1]

def calculate_npk_requirements(self, crop, location, acres, growth_stage):
    """
    Calculate NPK requirements based on crop, location, area, and growth stage.
    
    Args:
        crop (str): The name of the crop
        location (str): Location string (city, state)
        acres (float): Area in acres
        growth_stage (str): Current growth stage of the crop
        
    Returns:
        dict: NPK requirements in kg/acre
    """
    # Get base NPK requirements for the crop
    if crop not in self.BASE_NPK_REQUIREMENTS:
        return {"N": 0, "P": 0, "K": 0}
    
    base_npk = self.BASE_NPK_REQUIREMENTS[crop]
    
    # Determine region based on location
    region = self._determine_region(location)
    regional_multipliers = self.REGIONAL_NPK.get(region, {"N": 1.0, "P": 1.0, "K": 1.0})
    
    # Get stage-specific multiplier
    stage_multiplier = self.CROPS[crop]["stages"].get(growth_stage, {}).get("npk_multiplier", 1.0)
    
    # Calculate final NPK requirements
    npk_requirements = {
        nutrient: base_amount * regional_multipliers[nutrient] * stage_multiplier * acres
        for nutrient, base_amount in base_npk.items()
    }
    
    return npk_requirements

def _determine_region(self, location):
    """
    Determine the region based on location string.
    
    Args:
        location (str): Location string (city, state)
        
    Returns:
        str: Region (North, South, East, West, or Central)
    """
    # Dictionary of major cities and their regions
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
    
    # Extract city from location string and convert to lowercase
    city = location.split(',')[0].strip().lower()
    
    # Return the region for the city if found, otherwise return 'Central' as default
    return city_regions.get(city, 'Central')

def query_gemini_api(self, crop, language):
    """
    Query the Gemini API for crop disease analysis and translate the response.
    
    Args:
        crop (str): The name of the crop
        language (str): Target language for translation
        
    Returns:
        str: Translated analysis text
    """
    try:
        # Construct the prompt for disease analysis
        prompt = f"""
        Provide a comprehensive yet concise analysis of common diseases affecting {crop} crops, including:
        1. Top 3 most common diseases
        2. Early warning signs
        3. Prevention measures
        4. Basic treatment options
        Format the response with clear headers and bullet points.
        """
        
        # Prepare the API request
        headers = {
            "Content-Type": "application/json",
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "safety_settings": {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        }
        
        # Make the API request
        url = f"{self.API_URL}?key={self.API_KEY}"
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code != 200:
            return f"Error: API request failed with status code {response.status_code}"
            
        # Parse the response
        response_data = response.json()
        analysis_text = response_data['candidates'][0]['content']['parts'][0]['text']
        
        # Translate if necessary
        if language != "English":
            analysis_text = self.translator.translate(
                analysis_text, 
                dest=self._get_language_code(language)
            ).text
            
        return analysis_text
        
    except Exception as e:
        return f"Error: Failed to generate analysis: {str(e)}"

def _get_language_code(self, language):
    """
    Convert language name to ISO code for translation.
    
    Args:
        language (str): Language name
        
    Returns:
        str: ISO language code
    """
    language_codes = {
        'Telugu': 'te',
        'English': 'en',
        'Hindi': 'hi'
    }
    return language_codes.get(language, 'en')

async def text_to_speech(self, text, output_file, language):
    """
    Convert text to speech using edge-tts.
    
    Args:
        text (str): Text to convert to speech
        output_file (str): Output audio file path
        language (str): Language for text-to-speech
    """
    try:
        # Get the appropriate voice for the language
        voice = self.VOICES.get(language, 'en-US-AriaNeural')
        
        # Initialize edge-tts communicate
        tts = edge_tts.Communicate(text, voice)
        
        # Save audio to file
        await tts.save(output_file)
        
    except Exception as e:
        st.error(f"Error generating audio: {str(e)}")

def get_binary_file_downloader_html(self, file_path, file_label):
    """
    Create an HTML download button for a binary file.
    
    Args:
        file_path (str): Path to the file
        file_label (str): Label for the download button
        
    Returns:
        str: HTML for download button
    """
    try:
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        b64 = base64.b64encode(file_bytes).decode()
        download_filename = os.path.basename(file_path)
        
        return f'''
            <a href="data:application/octet-stream;base64,{b64}" 
               download="{download_filename}" 
               style="text-decoration: none;">
                <button style="
                    background-color: #4CAF50;
                    border: none;
                    color: white;
                    padding: 12px 24px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 16px;
                    margin: 4px 2px;
                    cursor: pointer;
                    border-radius: 4px;">
                    📥 Download {file_label}
                </button>
            </a>
        '''
    except Exception as e:
        return f"Error creating download button: {str(e)}"
    # All other methods remain the same...

def main():
    # Set page config with custom theme
    st.set_page_config(
        page_title="Enhanced Crop Disease Analyzer",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for better styling
    st.markdown("""
        <style>
        .stButton>button {
            width: 100%;
            height: 60px;
            font-size: 20px;
            margin: 5px 0;
            border-radius: 10px;
        }
        .crop-card {
            padding: 10px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin: 10px 0;
            background-color: white;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
        }
        .main-header {
            text-align: center;
            padding: 20px;
            background-color: #f0f2f6;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Main header with improved styling
    st.markdown("""
        <div class="main-header">
            <h1>🌱 AI Based Kiosk Platform For Farmers</h1>
            <p style="font-size: 1.2em;">Your Smart Farming Assistant</p>
        </div>
    """, unsafe_allow_html=True)

    analyzer = StreamlitCropDiseaseAnalyzer()

    # Sidebar with improved organization
    with st.sidebar:
        st.markdown("### 📊 Configuration")
        selected_language = st.selectbox("Select Language", list(analyzer.VOICES.keys()))
        
        st.markdown("### 📍 Location Details")
        location = st.text_input("Enter your location (City, State)", "Delhi, India")
        acres = st.number_input("Enter area in acres", min_value=0.1, value=1.0, step=0.1)
        
        st.markdown("### 📅 Crop Timeline")
        sowing_date = st.date_input(
            "Select sowing date",
            datetime.now() - timedelta(days=30)
        )

    # Create crop selection grid with improved styling
    st.subheader("🌾 Select Your Crop")
    
    # Create rows with 3 crops each for better organization
    crops_list = list(analyzer.CROPS.items())
    for i in range(0, len(crops_list), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(crops_list):
                crop, data = crops_list[i + j]
                with cols[j]:
                    st.markdown(f"""
                        <div class="crop-card">
                            <h3 style="text-align: center;">{crop}</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button("Select", key=f"crop_{i+j}"):
                        selected_crop = crop
                    st.image(data["image"], caption=data["description"], use_column_width=True)

    if 'selected_crop' in locals():
        st.markdown(f"## Analysis for {selected_crop}")

        # Weather data display with improved styling
        weather_data = analyzer.get_weather_data(location)
        if weather_data:
            st.markdown("### ☁️ Current Weather Conditions")
            
            # Create two rows of metrics with consistent styling
            cols = st.columns(4)
            metrics = [
                ("🌡️ Temperature", f"{weather_data['temperature']}°C"),
                ("💧 Humidity", f"{weather_data['humidity']}%"),
                ("💨 Wind Speed", f"{weather_data['windSpeed']} km/h"),
                ("🌧️ Precipitation", f"{weather_data['precipitation']} mm")
            ]
            
            for i, (label, value) in enumerate(metrics):
                with cols[i]:
                    st.markdown(f"""
                        <div class="metric-card">
                            <h4>{label}</h4>
                            <h2>{value}</h2>
                        </div>
                    """, unsafe_allow_html=True)

            # Weather alerts with improved visibility
            if weather_data['humidity'] > 80:
                st.warning("⚠️ High humidity alert! Monitor for potential disease risks")
            if weather_data['precipitation'] > 10:
                st.warning("⚠️ Significant rainfall detected! Check your drainage systems")

        # Growth stage and NPK requirements with improved styling
        growth_stage = analyzer.calculate_growth_stage(
            datetime.combine(sowing_date, datetime.min.time()),
            selected_crop
        )
        
        # Display growth stage with progress indication
        st.markdown("### 🌱 Crop Growth Stage")
        st.info(f"Current Stage: {growth_stage}")
        
        # Calculate and display NPK requirements with improved styling
        npk_req = analyzer.calculate_npk_requirements(
            selected_crop, 
            location, 
            acres,
            growth_stage
        )
        
        st.markdown("### 🧪 Fertilizer Recommendations")
        cols = st.columns(3)
        with cols[0]:
            st.markdown("""
                <div class="metric-card">
                    <h4>Nitrogen (N)</h4>
                    <h2>{:.1f} kg/acre</h2>
                </div>
            """.format(npk_req['N']), unsafe_allow_html=True)
        with cols[1]:
            st.markdown("""
                <div class="metric-card">
                    <h4>Phosphorus (P)</h4>
                    <h2>{:.1f} kg/acre</h2>
                </div>
            """.format(npk_req['P']), unsafe_allow_html=True)
        with cols[2]:
            st.markdown("""
                <div class="metric-card">
                    <h4>Potassium (K)</h4>
                    <h2>{:.1f} kg/acre</h2>
                </div>
            """.format(npk_req['K']), unsafe_allow_html=True)

        # Disease analysis section with improved styling
        with st.spinner('📊 Analyzing crop diseases...'):
            analysis_text = analyzer.query_gemini_api(selected_crop, selected_language)
            
            if "Error:" not in analysis_text:
                st.markdown("### 🔍 Disease Analysis")
                st.markdown(analysis_text)
                
                # Audio generation with improved UI
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                audio_file = f"crop_disease_analysis_{selected_crop.lower()}_{timestamp}.mp3"

                with st.spinner('🎵 Generating audio summary...'):
                    asyncio.run(analyzer.text_to_speech(analysis_text, audio_file, selected_language))

                # Audio player with improved styling
                st.markdown("### 🎧 Audio Summary")
                with open(audio_file, 'rb') as audio_data:
                    st.audio(audio_data.read(), format='audio/mp3')

                # Download button with improved styling
                st.markdown("""
                    <div style="text-align: center; margin: 20px 0;">
                        {}
                    </div>
                """.format(analyzer.get_binary_file_downloader_html(audio_file, 'Audio Summary')), 
                unsafe_allow_html=True)

                # Cleanup
                try:
                    os.remove(audio_file)
                except:
                    pass
            else:
                st.error(analysis_text)

if __name__ == "__main__":
    main()
