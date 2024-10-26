import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from PIL import Image
import io
import json
from googletrans import Translator
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelManager:
    """Handles ML model availability and loading"""
    
    @staticmethod
    def check_package(package_name):
        try:
            __import__(package_name)
            return True
        except ImportError:
            return False
    
    @staticmethod
    def load_model(model_path):
        """Safely load a model if it exists"""
        if not os.path.exists(model_path):
            logger.warning(f"Model file not found: {model_path}")
            return None
            
        try:
            import tensorflow as tf
            return tf.keras.models.load_model(model_path)
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return None

class SmartFarmingAssistant:
    def __init__(self):
        # Initialize basic components
        self.initialize_basic_components()
        # Attempt to initialize advanced features
        self.initialize_advanced_features()
        
    def initialize_basic_components(self):
        """Initialize core components that don't require optional dependencies"""
        # API configurations - with proper error handling
        try:
            self.WEATHER_API_KEY = st.secrets["visual_crossing"]["api_key"]
            self.GEMINI_API_KEY = st.secrets["gemini"]["api_key"]
        except KeyError:
            logger.warning("API keys not found in secrets. Some features will be disabled.")
            self.WEATHER_API_KEY = None
            self.GEMINI_API_KEY = None
        
        # Language support
        self.LANGUAGES = {
            'English': 'en',
            'Hindi': 'hi',
            'Telugu': 'te',
            'Tamil': 'ta',
            'Bengali': 'bn'
        }
        
        # Initialize core database
        self.initialize_crop_database()
        
        # Initialize translator with error handling
        try:
            self.translator = Translator()
        except Exception:
            logger.warning("Translation service initialization failed. Translation features will be disabled.")
            self.translator = None
        
        # Cache for optimization recommendations
        self.recommendations_cache = {}

    def initialize_crop_database(self):
        """Placeholder for crop database initialization"""
        # Add your database initialization code here if necessary
        pass

    def initialize_advanced_features(self):
        """Initialize features that require optional dependencies"""
        self.ml_capabilities = {
            'disease_detection': False,
            'yield_prediction': False,
            'image_processing': False
        }
        
        # Check for TensorFlow
        if ModelManager.check_package('tensorflow'):
            self.disease_model = ModelManager.load_model('models/disease_detection.h5')
            self.ml_capabilities['disease_detection'] = (self.disease_model is not None)
        
        # Check for scikit-learn
        if ModelManager.check_package('sklearn'):
            try:
                from sklearn.ensemble import RandomForestRegressor
                self.yield_model = RandomForestRegressor()
                self.ml_capabilities['yield_prediction'] = True
            except Exception as e:
                logger.warning(f"Error initializing yield prediction: {str(e)}")
        
        # Check for OpenCV
        self.ml_capabilities['image_processing'] = ModelManager.check_package('cv2')

    def get_capabilities_status(self):
        """Return current status of all capabilities"""
        return {
            'weather_api': self.WEATHER_API_KEY is not None,
            'translation': self.translator is not None,
            'ml_capabilities': self.ml_capabilities
        }

    def detect_disease(self, image):
        """Enhanced disease detection with proper error handling"""
        if not self.ml_capabilities['disease_detection']:
            return {
                'status': 'error',
                'message': "Disease detection is not available. Required packages: tensorflow, cv2"
            }
            
        if not self.ml_capabilities['image_processing']:
            return {
                'status': 'error',
                'message': "Image processing is not available. Required package: cv2"
            }
            
        try:
            import cv2
            # Preprocess image
            img = cv2.resize(image, (224, 224))
            img = img / 255.0
            img = np.expand_dims(img, axis=0)
            
            # Make prediction
            pred = self.disease_model.predict(img)
            return {
                'status': 'success',
                'prediction': self.process_disease_prediction(pred)
            }
        except Exception as e:
            logger.error(f"Error in disease detection: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error processing image: {str(e)}"
            }

    def process_disease_prediction(self, prediction):
        """Process disease prediction result"""
        # Assuming a specific format for disease prediction results for example purposes
        return {"disease_name": "Example Disease", "confidence": 0.95}

    def get_weather_forecast(self, location):
        """Enhanced weather forecast fetching with error handling"""
        if not self.WEATHER_API_KEY:
            return {
                'status': 'error',
                'message': "Weather API key not configured"
            }
            
        try:
            url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}?key={self.WEATHER_API_KEY}"
            response = requests.get(url, timeout=10)  # Added timeout
            response.raise_for_status()  # Raise exception for bad status codes
            return {
                'status': 'success',
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Weather API error: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error fetching weather data: {str(e)}"
            }

def main():
    st.set_page_config(
        page_title="Smart Farming Assistant",
        page_icon="🌾",
        layout="wide"
    )
    
    try:
        # Initialize the assistant
        assistant = SmartFarmingAssistant()
        
        # Get capability status
        capabilities = assistant.get_capabilities_status()
        
        # Show capability status in sidebar
        with st.sidebar:
            st.title("🌾 Smart Farming Assistant")
            
            if not all(capabilities.values()):
                st.warning("Some features are disabled. Check system status for details.")
            
            with st.expander("System Status"):
                st.write("Available Features:")
                for feature, status in capabilities['ml_capabilities'].items():
                    st.write(f"- {feature}: {'✅' if status else '❌'}")
                st.write(f"- Weather API: {'✅' if capabilities['weather_api'] else '❌'}")
                st.write(f"- Translation: {'✅' if capabilities['translation'] else '❌'}")
            
            # Rest of the sidebar UI...
            
        # Main content with error handling for each tab...
        
    except Exception as e:
        st.error(f"Application initialization error: {str(e)}")
        logger.error(f"Critical error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
