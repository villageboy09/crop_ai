import streamlit as st
import asyncio
import edge_tts
import requests
import os
from datetime import datetime
from googletrans import Translator
from PIL import Image

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
        
        # Updated CROPS dictionary with disease seasons and placeholder images
        self.CROPS = {
            "Tomato": {
                "image": "https://via.placeholder.com/300x200.png?text=Tomato",
                "diseases": {
                    "summer": ["Early Blight", "Leaf Spot"],
                    "winter": ["Late Blight", "Powdery Mildew"],
                    "monsoon": ["Bacterial Wilt", "Fungal Rot"]
                }
            },
            "Potato": {
                "image": "https://via.placeholder.com/300x200.png?text=Potato",
                "diseases": {
                    "summer": ["Common Scab", "Black Scurf"],
                    "winter": ["Late Blight", "Early Blight"],
                    "monsoon": ["Bacterial Wilt", "Soft Rot"]
                }
            }
        }

        self.translator = Translator()

    async def text_to_speech(self, text, output_file, language):
        """Generate speech from text using edge-tts"""
        try:
            voice = self.VOICES.get(language, 'en-US-AriaNeural')
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_file)
            return True
        except Exception as e:
            st.error(f"Error generating speech: {str(e)}")
            return False

    def get_weather_data(self, location):
        """Fetch weather data from Visual Crossing API"""
        try:
            base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
            
            params = {
                'unitGroup': 'metric',
                'key': self.WEATHER_API_KEY,
                'contentType': 'json',
                'include': 'current',
                'elements': 'temp,humidity,conditions,precip,cloudcover,windspeed'
            }
            
            clean_location = location.replace(' ', '').replace(',', '/')
            url = f"{base_url}/{clean_location}"
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                current = data.get('currentConditions', {})
                return {
                    'temperature': current.get('temp', 0),
                    'humidity': current.get('humidity', 0),
                    'conditions': current.get('conditions', ''),
                    'precipitation': current.get('precip', 0),
                    'cloudCover': current.get('cloudcover', 0),
                    'windSpeed': current.get('windspeed', 0)
                }
            else:
                st.error(f"Weather API Error: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Error fetching weather data: {str(e)}")
            return None
            
    def get_user_location(self):
        """Auto-fetch user's location using IP-API"""
        try:
            response = requests.get(self.IPAPI_URL, timeout=5)
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

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.API_KEY}"
            }
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }

            response = requests.post(self.API_URL, headers=headers, json=payload)

            if response.status_code == 200:
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return f"Error: API returned status code {response.status_code}"

        except Exception as e:
            return f"Error querying API: {str(e)}"

def create_crop_card(crop_name, image_url):
    """Create a styled card for crop selection"""
    return f"""
        <div style="
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 10px;
            margin: 5px;
            text-align: center;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <img src="{image_url}" 
                style="width: 100%; 
                       height: 150px; 
                       object-fit: cover; 
                       border-radius: 4px;">
            <h3 style="margin-top: 10px; color: #2c3e50;">{crop_name}</h3>
        </div>
    """

def main():
    st.set_page_config(
        page_title="Smart Crop Disease Analyzer",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🌱 Smart Crop Disease Analyzer")
    
    analyzer = StreamlitCropDiseaseAnalyzer()

    # Sidebar configuration
    with st.sidebar:
        st.header("Settings")
        
        # Auto-fetch user location
        user_location = analyzer.get_user_location()
        if user_location and user_location['city']:
            location_str = f"{user_location['city']}, {user_location['region']}, {user_location['country']}"
            st.success(f"📍 Location detected: {location_str}")
            location = st.text_input("Or enter different location:", location_str)
        else:
            location = st.text_input("Enter your location:", "Delhi, India")

        # Language selection
        selected_language = st.selectbox(
            "Select Language",
            list(analyzer.VOICES.keys()),
            index=list(analyzer.VOICES.keys()).index("English")
        )

        # Display current season
        current_season = analyzer.get_current_season()
        st.info(f"🗓️ Current Season: {current_season.capitalize()}")

    # Main content area
    st.subheader("Select a Crop for Analysis")
    
    # Create crop selection grid
    cols = st.columns(len(analyzer.CROPS))
    selected_crop = None
    
    for idx, (crop, data) in enumerate(analyzer.CROPS.items()):
        with cols[idx]:
            if st.markdown(create_crop_card(crop, data["image"]), unsafe_allow_html=True):
                selected_crop = crop
            if st.button(f"Analyze {crop}"):
                selected_crop = crop

    if selected_crop:
        st.markdown(f"## Analysis for {selected_crop}")

        # Weather data display
        weather_data = analyzer.get_weather_data(location)
        if weather_data:
            st.subheader("☁️ Current Weather Conditions")
            
            cols = st.columns(4)
            with cols[0]:
                st.metric("🌡️ Temperature", f"{weather_data['temperature']}°C")
            with cols[1]:
                st.metric("💧 Humidity", f"{weather_data['humidity']}%")
            with cols[2]:
                st.metric("🌬️ Wind Speed", f"{weather_data['windSpeed']} km/h")
            with cols[3]:
                st.metric("🌧️ Precipitation", f"{weather_data['precipitation']} mm")

            # Weather risk assessment
            if weather_data['humidity'] > 80:
                st.warning("⚠️ High humidity alert - Increased risk of fungal diseases")
            if weather_data['temperature'] > 30:
                st.warning("⚠️ High temperature alert - Monitor for heat stress")

        # Disease analysis
        with st.spinner(f'Analyzing seasonal diseases for {selected_crop}...'):
            analysis = analyzer.query_gemini_api(
                selected_crop, 
                selected_language,
                current_season
            )
            
            if "Error:" not in analysis:
                st.markdown(analysis)
                
                # Audio generation
                audio_file = f"temp_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                
                with st.spinner('Generating audio summary...'):
                    success = asyncio.run(analyzer.text_to_speech(
                        analysis,
                        audio_file,
                        selected_language
                    ))
                
                if success:
                    with open(audio_file, 'rb') as audio_data:
                        audio_bytes = audio_data.read()
                        st.audio(audio_bytes, format='audio/mp3')
                        st.download_button(
                            label="📥 Download Audio Summary",
                            data=audio_bytes,
                            file_name=f"{selected_crop}_analysis.mp3",
                            mime="audio/mp3"
                        )
                    
                    # Cleanup
                    try:
                        os.remove(audio_file)
                    except Exception:
                        pass
            else:
                st.error(analysis)

if __name__ == "__main__":
    main()
