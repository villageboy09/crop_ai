import streamlit as st
import asyncio
import edge_tts
from datetime import datetime, timedelta
import requests
import os
import base64
from googletrans import Translator
from PIL import Image

class FarmerFriendlyCropAnalyzer:
    def __init__(self):
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
                "image": "https://picsum.photos/200/300?random=1",
                "stages": {
                    "Seedling": {
                        "duration": 25,
                        "npk_multiplier": 0.4,
                        "common_diseases": ["Damping off", "Seedling blight"]
                    },
                    "Vegetative": {
                        "duration": 50,
                        "npk_multiplier": 0.9,
                        "common_diseases": ["Bacterial leaf blight", "Sheath blight"]
                    },
                    "Flowering": {
                        "duration": 30,
                        "npk_multiplier": 1.2,
                        "common_diseases": ["Rice blast", "False smut"]
                    },
                    "Maturing": {
                        "duration": 35,
                        "npk_multiplier": 1.4,
                        "common_diseases": ["Grain discoloration", "Brown spot"]
                    }
                }
            },
            # Similar structure for other crops...
        }

    def query_stage_specific_diseases(self, crop, growth_stage, language):
        """Query Gemini API for stage-specific disease information"""
        diseases = self.CROPS[crop]["stages"][growth_stage]["common_diseases"]
        diseases_list = ", ".join(diseases)
        
        prompt = f"""
        For {crop} plants in the {growth_stage} stage, provide detailed information about these specific diseases: {diseases_list}
        
        For each disease, provide:
        1. Early warning signs (in simple terms)
        2. What the farmer should look for in the field
        3. Simple prevention steps
        4. Basic treatment methods using commonly available solutions
        
        Make the response very simple and practical for farmers.
        Provide the response in {language} language using common terms.
        Use bullet points and simple language.
        """

        try:
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
                return f"Error: Unable to get disease information (Status code: {response.status_code})"
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    st.set_page_config(
        page_title="Farmer's Crop Guide", 
        page_icon="🌾",
        layout="wide"
    )
    
    # Custom CSS for better visual hierarchy
    st.markdown("""
        <style>
        .big-font {
            font-size:30px !important;
            font-weight: bold;
        }
        .medium-font {
            font-size:24px !important;
            color: #2c3e50;
        }
        .highlight {
            padding: 20px;
            border-radius: 10px;
            background-color: #f8f9fa;
            margin: 10px 0;
        }
        .crop-button {
            border: 2px solid #4CAF50;
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            margin: 5px;
            cursor: pointer;
        }
        .crop-button:hover {
            background-color: #4CAF50;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header with local language support
    st.markdown('<p class="big-font">🌾 किसान का साथी | Farmer\'s Companion | రైతు సహాయకుడు</p>', unsafe_allow_html=True)

    analyzer = FarmerFriendlyCropAnalyzer()

    # Simplified language selection with icons
    col1, col2 = st.columns([1, 3])
    with col1:
        selected_language = st.selectbox(
            "🗣️ भाषा | Language | భాష",
            list(analyzer.VOICES.keys()),
            index=1  # Default to English
        )

    # Simple location input with map
    location = st.text_input("📍 Your Village/Town", "Delhi")
    
    # Visual calendar for sowing date
    sowing_date = st.date_input(
        "🌱 When did you sow your crop?",
        datetime.now() - timedelta(days=30)
    )

    # Visual crop selection with images
    st.markdown('<p class="medium-font">Select Your Crop</p>', unsafe_allow_html=True)
    crop_cols = st.columns(5)
    selected_crop = None
    
    for idx, (crop, data) in enumerate(analyzer.CROPS.items()):
        with crop_cols[idx % 5]:
            st.markdown(f"""
                <div class="crop-button">
                    <img src="{data['image']}" style="width:100%; border-radius:5px;">
                    <p style="margin-top:10px;">{crop}</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"Select {crop}", key=f"crop_{idx}"):
                selected_crop = crop

    if selected_crop:
        st.markdown(f'<p class="medium-font">🌿 {selected_crop} Care Guide</p>', unsafe_allow_html=True)
        
        # Calculate growth stage
        growth_stage = analyzer.calculate_growth_stage(
            datetime.combine(sowing_date, datetime.min.time()),
            selected_crop
        )

        # Visual growth stage indicator
        stages = list(analyzer.CROPS[selected_crop]["stages"].keys())
        current_stage_idx = stages.index(growth_stage)
        
        st.markdown('<div class="highlight">', unsafe_allow_html=True)
        progress_cols = st.columns(len(stages))
        for idx, stage in enumerate(stages):
            with progress_cols[idx]:
                if idx < current_stage_idx:
                    st.markdown(f"✅ {stage}")
                elif idx == current_stage_idx:
                    st.markdown(f"🔆 {stage} (Current)")
                else:
                    st.markdown(f"⭕ {stage}")
        st.markdown('</div>', unsafe_allow_html=True)

        # Get and display stage-specific diseases
        with st.spinner('Loading disease information...'):
            disease_info = analyzer.query_stage_specific_diseases(
                selected_crop,
                growth_stage,
                selected_language
            )
            
            if "Error:" not in disease_info:
                st.markdown('<div class="highlight">', unsafe_allow_html=True)
                st.markdown("### 🔍 What to Watch For:")
                st.markdown(disease_info)
                st.markdown('</div>', unsafe_allow_html=True)

                # Generate audio guidance
                audio_file = f"guidance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                with st.spinner('Creating voice guidance...'):
                    asyncio.run(analyzer.text_to_speech(disease_info, audio_file, selected_language))
                
                # Audio player with clear instructions
                st.markdown("### 🔊 Listen to Guidance:")
                with open(audio_file, 'rb') as audio_data:
                    st.audio(audio_data.read(), format='audio/mp3')
                
                # Cleanup
                try:
                    os.remove(audio_file)
                except:
                    pass
            else:
                st.error("Unable to get disease information. Please try again.")

if __name__ == "__main__":
    main()
