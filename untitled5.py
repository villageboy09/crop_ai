import streamlit as st
import requests
import logging
from googletrans import Translator
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartFarmingAssistant:
    def __init__(self):
        # Initialize basic components
        self.initialize_basic_components()
        
    def initialize_basic_components(self):
        """Initialize core components that don't require optional dependencies"""
        # API configurations with error handling
        try:
            self.WEATHER_API_KEY = st.secrets["visual_crossing"]["api_key"]
        except KeyError:
            logger.warning("API keys not found in secrets. Weather feature will be disabled.")
            self.WEATHER_API_KEY = None
        
        # Language support
        self.LANGUAGES = {
            'English': 'en',
            'Hindi': 'hi',
            'Telugu': 'te',
        }
        
        # Initialize translator with error handling
        try:
            self.translator = Translator()
        except Exception:
            logger.warning("Translation service initialization failed.")
            self.translator = None

    def get_weather_forecast(self, location):
        """Fetch weather forecast with error handling"""
        if not self.WEATHER_API_KEY:
            return "Weather API key not configured"
        
        try:
            url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}?key={self.WEATHER_API_KEY}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Weather API error: {str(e)}")
            return f"Error fetching weather data: {str(e)}"

    def translate_text(self, text, dest_language):
        """Translate text to a selected language"""
        if self.translator:
            try:
                translation = self.translator.translate(text, dest=dest_language)
                return translation.text
            except Exception as e:
                logger.error(f"Translation error: {str(e)}")
                return "Translation failed"
        else:
            return "Translation service is not available."

def main():
    st.set_page_config(
        page_title="Smart Farming Assistant",
        page_icon="🌾",
        layout="wide"
    )

    assistant = SmartFarmingAssistant()

    # Sidebar: Features Status
    st.sidebar.title("🌾 Smart Farming Assistant")
    st.sidebar.write("Choose a feature from the main content.")

    # Main content
    st.title("Welcome to the Smart Farming Assistant")

    # Weather Forecast Feature
    st.subheader("Weather Forecast")
    location = st.text_input("Enter your location for a weather forecast:")
    if st.button("Get Weather Forecast"):
        if location:
            forecast = assistant.get_weather_forecast(location)
            st.write("Weather Data:", forecast if isinstance(forecast, str) else forecast.get('description', "Data not available"))
        else:
            st.warning("Please enter a location.")

    # Translation Feature
    st.subheader("Translation Service")
    text_to_translate = st.text_area("Enter text to translate:")
    language = st.selectbox("Select language:", list(assistant.LANGUAGES.keys()))
    if st.button("Translate Text"):
        if text_to_translate:
            translated_text = assistant.translate_text(text_to_translate, assistant.LANGUAGES[language])
            st.write("Translated Text:", translated_text)
        else:
            st.warning("Please enter text to translate.")

if __name__ == "__main__":
    main()
