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
from pytube import Search
import re


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
    "Rice": {
        "image": "https://cdn.britannica.com/89/140889-050-EC3F00BF/Ripening-heads-rice-Oryza-sativa.jpg",
        "stages": {
            "Seedling": {"duration": 25, "npk_multiplier": 0.4},
            "Vegetative": {"duration": 50, "npk_multiplier": 0.9},
            "Flowering": {"duration": 30, "npk_multiplier": 1.2},
            "Maturing": {"duration": 35, "npk_multiplier": 1.4}
        }
    },
    "Maize": {
        "image": "https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcTSQTwY5H90hpRERbth6Y70s48hYKQQ3EimRbhVpGTe_zCHc0II",
        "stages": {
            "Seedling": {"duration": 20, "npk_multiplier": 0.5},
            "Vegetative": {"duration": 45, "npk_multiplier": 1.0},
            "Flowering": {"duration": 30, "npk_multiplier": 1.3},
            "Maturing": {"duration": 35, "npk_multiplier": 1.6}
        }
    },
    "Sorghum": {
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQFyoo17z6OwjPUWoBWrKNMEfJf1Cd4wpx5atIJGCgtZU8E9zPQ",
        "stages": {
            "Seedling": {"duration": 22, "npk_multiplier": 0.5},
            "Vegetative": {"duration": 40, "npk_multiplier": 1.0},
            "Flowering": {"duration": 25, "npk_multiplier": 1.2},
            "Maturing": {"duration": 30, "npk_multiplier": 1.4}
        }
    },
    "Cotton": {
        "image": "https://cdn.britannica.com/18/156618-050-39339EA2/cotton-harvesting.jpg",
        "stages": {
            "Seedling": {"duration": 25, "npk_multiplier": 0.6},
            "Vegetative": {"duration": 45, "npk_multiplier": 1.1},
            "Flowering": {"duration": 30, "npk_multiplier": 1.5},
            "Boll Formation": {"duration": 35, "npk_multiplier": 1.8}
        }
    },
    "Groundnut": {
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQX4-OuVBESIfeRVCsFnLstkRLvDRAUpeSlGA&s",
        "stages": {
            "Seedling": {"duration": 20, "npk_multiplier": 0.5},
            "Vegetative": {"duration": 40, "npk_multiplier": 1.0},
            "Flowering": {"duration": 25, "npk_multiplier": 1.2},
            "Pod Formation": {"duration": 30, "npk_multiplier": 1.5}
        }
    }
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
                "Rice": {"N": 100, "P": 50, "K": 80},
    "Maize": {"N": 120, "P": 60, "K": 100},
    "Sorghum": {"N": 90, "P": 40, "K": 70},
    "Cotton": {"N": 110, "P": 70, "K": 90},
    "Groundnut": {"N": 80, "P": 60, "K": 70}
            # ... other crops
        }
        self.VIDEO_CATEGORIES = {
            "cultivation": "cultivation techniques",
            "diseases": "disease management",
            "harvesting": "harvesting methods",
            "marketing": "marketing tips",
            "organic": "organic farming"
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

    def query_gemini_api(self, crop, language):
        """Query Gemini API for crop disease information in specified language"""
        try:
            headers = {
                "Content-Type": "application/json"
            }

            # Adjust prompt based on language
            base_prompt = f"""
            Analyze and provide detailed information about common diseases in {crop} cultivation.
            For each disease, include:
            1. Disease name
            2. Symptoms
            3. Favorable conditions
            4. Prevention methods
            5. Treatment options
            
            Provide the response in {language} language.
            Format the response in a clear, structured way.
            """

            payload = {
                "contents": [{
                    "parts": [{
                        "text": base_prompt
                    }]
                }]
            }

            url = f"{self.API_URL}?key={self.API_KEY}"
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            else:
                error_msg = f"Error: API returned status code {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f"\nDetails: {error_detail.get('error', {}).get('message', 'No details available')}"
                except:
                    pass
                return error_msg

        except Exception as e:
            return f"Error querying API: {str(e)}"

    async def text_to_speech(self, text, output_file, language):
        """Convert text to speech using edge-tts"""
        voice = self.VOICES[language]
        try:
            clean_text = " ".join(word for word in text.split() if not word.startswith("#"))
            communicate = edge_tts.Communicate(clean_text, voice)
            await communicate.save(output_file)
        except Exception as e:
            st.error(f"Error during TTS conversion: {str(e)}")
            raise

    def get_binary_file_downloader_html(self, file_path, file_name):
        """Generate a download link for a binary file."""
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        b64 = base64.b64encode(file_bytes).decode()  # Convert to base64
        return f'<a href="data:file/unknown;base64,{b64}" download="{file_name}">Download {file_name}</a>'

   def search_youtube_videos(self, crop, max_results=6):
       try:
        # Create a focused search query for farming videos
            search_query = f"{crop} farming cultivation guide"
            s = Search(search_query)
        
        videos = []
        for video in s.results[:max_results]:
            try:
                # Extract video ID using regex
                video_id = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', video.watch_url)
                if video_id:
                    video_id = video_id.group(1)
                    
                    # Safely handle None values for length and views
                    duration = "N/A"
                    if video.length is not None:
                        try:
                            duration = str(timedelta(seconds=int(video.length)))
                        except:
                            duration = "N/A"
                    
                    views = "N/A"
                    if video.views is not None:
                        try:
                            views = f"{int(video.views):,}"
                        except:
                            views = "N/A"
                    
                    videos.append({
                        'title': video.title or "Untitled",
                        'url': video.watch_url,
                        'thumbnail': f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
                        'duration': duration,
                        'views': views,
                        'embed_url': f"https://www.youtube.com/embed/{video_id}"
                    })
            except Exception as e:
                continue  # Skip videos that cause errors
            
        if not videos:
            return []
        
        return videos
        
    except Exception as e:
        st.error(f"Error searching YouTube videos: {str(e)}")
        return []



def main():
    # Configure the page with a custom theme and wide layout
    st.set_page_config(
        page_title="Smart Farmer Assistant",
        page_icon="🌾",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for dark mode styling
    st.markdown("""
        <style>
        /* Dark mode colors */
        :root {
            --bg-color: #1E1E1E;
            --card-bg: #2D2D2D;
            --hover-bg: #383838;
            --text-color: #E0E0E0;
            --border-color: #404040;
            --shadow-color: rgba(0,0,0,0.3);
            --accent-color: #4CAF50;
            --gradient-start: #1a237e;
            --gradient-end: #4CAF50;
        }

        .main {
            background-color: var(--bg-color);
            color: var(--text-color);
            padding: 2rem;
        }

        .stButton>button {
            width: 100%;
            border-radius: 10px;
            height: 3em;
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            transition: all 0.3s ease;
        }

        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px var(--shadow-color);
            background-color: var(--hover-bg);
        }

        .crop-card {
            background-color: var(--card-bg);
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px var(--shadow-color);
            transition: all 0.3s ease;
            border: 1px solid var(--border-color);
            margin-bottom: 1rem;
        }

        .crop-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px var(--shadow-color);
            background-color: var(--hover-bg);
        }

        .metric-card {
            background-color: var(--card-bg);
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px var(--shadow-color);
            text-align: center;
            border: 1px solid var(--border-color);
            margin-bottom: 1rem;
        }

        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px var(--shadow-color);
        }

        .header-container {
            padding: 2rem 0;
            text-align: center;
            background: linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-end) 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px var(--shadow-color);
        }

        /* Override Streamlit's default dark mode styles */
        .stTextInput>div>div>input {
            background-color: var(--card-bg);
            color: var(--text-color);
            border-color: var(--border-color);
        }

        .stSelectbox>div>div>select {
            background-color: var(--card-bg);
            color: var(--text-color);
            border-color: var(--border-color);
        }

        .stDateInput>div>div>input {
            background-color: var(--card-bg);
            color: var(--text-color);
            border-color: var(--border-color);
        }

        /* Custom styles for expandable sections */
        .streamlit-expanderHeader {
            background-color: var(--card-bg);
            border-radius: 10px;
            border: 1px solid var(--border-color);
        }

        .streamlit-expanderContent {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 0 0 10px 10px;
        }

        /* Progress indicators */
        .stage-indicator {
            padding: 0.5rem;
            border-radius: 5px;
            text-align: center;
            margin: 0.5rem 0;
        }

        .stage-complete {
            background-color: rgba(76, 175, 80, 0.2);
            border: 1px solid #4CAF50;
        }

        .stage-current {
            background-color: rgba(33, 150, 243, 0.2);
            border: 1px solid #2196F3;
        }

        .stage-pending {
            background-color: rgba(158, 158, 158, 0.2);
            border: 1px solid #9E9E9E;
        }

        /* Alert styling */
        .stAlert {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            color: var(--text-color);
        }
        /* Add styles for video section */
        .video-card {
            background-color: var(--card-bg);
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px var(--shadow-color);
            margin-bottom: 1rem;
            border: 1px solid var(--border-color);
        }
        
        .video-thumbnail {
            width: 100%;
            border-radius: 5px;
            margin-bottom: 0.5rem;
        }
        
        .video-title {
            color: var(--text-color);
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        
        .video-stats {
            color: var(--text-color);
            opacity: 0.8;
            font-size: 0.9rem;
        }

        </style>
    """, unsafe_allow_html=True)

    # Create header with gradient background
    st.markdown("""
        <div class='header-container'>
            <h1>🌾 Smart Farmer Assistant</h1>
            <p>Your AI-powered companion for smart farming</p>
        </div>
    """, unsafe_allow_html=True)

    analyzer = StreamlitCropDiseaseAnalyzer()

    # Sidebar with dark mode styling
    with st.sidebar:
        st.markdown("### 🔧 Settings")
        selected_language = st.selectbox(
            "🌐 Select Language",
            list(analyzer.VOICES.keys()),
            format_func=lambda x: f"📢 {x}"
        )
        
        st.markdown("### 📍 Location Details")
        location = st.text_input(
            "Location",
            "Delhi, India",
            help="Enter your city and state/country"
        )
        
        acres = st.number_input(
            "📏 Field Size (acres)",
            min_value=0.1,
            value=1.0,
            step=0.1,
            format="%.1f"
        )
        
        st.markdown("### 📅 Crop Timeline")
        sowing_date = st.date_input(
            "Sowing Date",
            datetime.now() - timedelta(days=30)
        )

    # Crop selection grid
    st.markdown("### 🌱 Select Your Crop")
    cols = st.columns(5)
    selected_crop = None

    for idx, (crop, data) in enumerate(analyzer.CROPS.items()):
        with cols[idx % 5]:
            st.markdown(f"""
                <div class='crop-card'>
                    <h4 style='text-align: center; color: var(--text-color);'>{crop}</h4>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Select", key=f"crop_{idx}"):
                selected_crop = crop
            st.image(data["image"], use_column_width=True)

    if selected_crop:
        st.markdown(f"""
            <div class='crop-card' style='margin: 2rem 0;'>
                <h2 style='text-align: center; color: var(--text-color);'>Analysis for {selected_crop}</h2>
            </div>
        """, unsafe_allow_html=True)
        

        # Weather data section
        weather_data = analyzer.get_weather_data(location)
        if weather_data:
            st.markdown("### 🌤️ Current Weather Conditions")
            
            weather_cols = st.columns(4)
            metrics = [
                ("🌡️ Temperature", f"{weather_data['temperature']}°C", "#FF6B6B"),
                ("💧 Humidity", f"{weather_data['humidity']}%", "#4ECDC4"),
                ("💨 Wind Speed", f"{weather_data['windSpeed']} km/h", "#45B7D1"),
                ("🌧️ Precipitation", f"{weather_data['precipitation']} mm", "#96CEB4")
            ]
            
            for col, (label, value, color) in zip(weather_cols, metrics):
                with col:
                    st.markdown(f"""
                        <div class='metric-card' style='border-left: 4px solid {color};'>
                            <h4 style='color: var(--text-color);'>{label}</h4>
                            <h2 style='color: {color};'>{value}</h2>
                        </div>
                    """, unsafe_allow_html=True)

            # Weather alerts
            if weather_data['humidity'] > 80:
                st.warning("⚠️ High Humidity Alert: Monitor crops for potential disease risks")
            if weather_data['precipitation'] > 10:
                st.warning("⚠️ Rainfall Alert: Ensure proper drainage systems are functioning")

        # Growth stage indicator
        growth_stage = analyzer.calculate_growth_stage(
            datetime.combine(sowing_date, datetime.min.time()),
            selected_crop
        )
        
        st.markdown("### 🌱 Growth Progress")
        stages = list(analyzer.CROPS[selected_crop]["stages"].keys())
        current_stage_idx = stages.index(growth_stage)
        
        progress_cols = st.columns(len(stages))
        for idx, (col, stage) in enumerate(zip(progress_cols, stages)):
            with col:
                if idx < current_stage_idx:
                    st.markdown(f"""
                        <div class='stage-indicator stage-complete'>
                            ✅ {stage}
                        </div>
                    """, unsafe_allow_html=True)
                elif idx == current_stage_idx:
                    st.markdown(f"""
                        <div class='stage-indicator stage-current'>
                            🔄 <strong>{stage}</strong>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class='stage-indicator stage-pending'>
                            ⏳ {stage}
                        </div>
                    """, unsafe_allow_html=True)

        # NPK recommendations
        npk_req = analyzer.calculate_npk_requirements(
            selected_crop, 
            location, 
            acres,
            growth_stage
        )
        
        st.markdown("### 🌿 Fertilizer Recommendations")
        npk_cols = st.columns(3)
        
        nutrients = [
            ("Nitrogen (N)", npk_req['N'], "#4CAF50"),
            ("Phosphorus (P)", npk_req['P'], "#2196F3"),
            ("Potassium (K)", npk_req['K'], "#FFC107")
        ]
        
        for col, (nutrient, value, color) in zip(npk_cols, nutrients):
            with col:
                st.markdown(f"""
                    <div class='metric-card' style='border-left: 4px solid {color};'>
                        <h4 style='color: var(--text-color);'>{nutrient}</h4>
                        <h2 style='color: {color};'>{value:.1f} kg/acre</h2>
                    </div>
                """, unsafe_allow_html=True)

        # Disease analysis section
        with st.spinner('Analyzing diseases...'):
            analysis_text = analyzer.query_gemini_api(selected_crop, selected_language)
            
            if "Error:" not in analysis_text:
                st.markdown("### 🔍 Disease Analysis")
                with st.expander("View Detailed Analysis", expanded=True):
                    st.markdown(analysis_text)
                
                # Audio generation
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                audio_file = f"crop_disease_analysis_{selected_crop.lower()}_{timestamp}.mp3"

                with st.spinner('Generating audio summary...'):
                    asyncio.run(analyzer.text_to_speech(analysis_text, audio_file, selected_language))

                # Audio player
                st.markdown("### 🎧 Audio Summary")
                with open(audio_file, 'rb') as audio_data:
                    st.audio(audio_data.read(), format='audio/mp3')

                # Download button
                st.download_button(
                    label="📥 Download Audio Summary",
                    data=open(audio_file, 'rb'),
                    file_name=audio_file,
                    mime='audio/mp3',
                    key='download-audio'
                )

                # Cleanup
                try:
                    os.remove(audio_file)
                except:
                    pass
            else:
                st.error(analysis_text)
                st.markdown("### 📺 Educational Farming Videos")
    with st.spinner('Loading farming videos...'):
        videos = analyzer.search_youtube_videos(selected_crop)
        
        if videos:
            video_cols = st.columns(3)
            for idx, video in enumerate(videos):
                with video_cols[idx % 3]:
                    st.markdown(f"""
                        <div class='video-card'>
                            <img src='{video["thumbnail"]}' class='video-thumbnail'>
                            <div class='video-title'>{video["title"][:60]}...</div>
                            <div class='video-stats'>
                                <span>Duration: {video["duration"]}</span><br>
                                <span>Views: {video["views"]}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Embed video player
                    try:
                        st.components.v1.iframe(
                            video["embed_url"],
                            width=None,
                            height=200,
                            scrolling=False
                        )
                    except Exception as e:
                        st.error(f"Error loading video player: {str(e)}")
        else:
            st.warning("""
                No videos found at the moment. 
                This could be due to:
                - Internet connectivity issues
                - YouTube API limitations
                - Temporary service unavailability
                
                Please try again in a few moments.
            """)


if __name__ == "__main__":
    main()
