import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from PIL import Image
import io
import json
from googletrans import Translator

# Define a function to check and install required packages
def check_dependencies():
    missing_packages = []
    optional_packages = {
        'tensorflow': 'Deep learning for disease detection',
        'cv2': 'Image processing',
        'plotly': 'Interactive visualizations',
        'sklearn': 'Machine learning for yield prediction'
    }
    
    for package, description in optional_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(f"- {package} ({description})")
    
    if missing_packages:
        st.warning("Some optional features are disabled. To enable all features, install the following packages:")
        st.code("pip install " + " ".join(optional_packages.keys()))
        st.write("Missing packages:")
        for package in missing_packages:
            st.write(package)

class SmartFarmingAssistant:
    def __init__(self):
        # API configurations
        self.WEATHER_API_KEY = st.secrets["visual_crossing"]["api_key"]
        self.GEMINI_API_KEY = st.secrets["gemini"]["api_key"]
        
        # Language support
        self.LANGUAGES = {
            'English': 'en',
            'Hindi': 'hi',
            'Telugu': 'te',
            'Tamil': 'ta',
            'Bengali': 'bn'
        }
        
        # Enhanced crop database with detailed parameters
        self.CROPS_DB = {
            "Rice": {
                "optimal_conditions": {
                    "soil_ph": {"min": 5.5, "max": 6.5},
                    "temperature": {"min": 20, "max": 35},
                    "humidity": {"min": 60, "max": 80},
                    "rainfall": {"min": 100, "max": 200},
                },
                "growth_stages": {
                    "Seedling": {
                        "duration": 20,
                        "water_req": 50,
                        "nutrient_req": {"N": 30, "P": 20, "K": 20},
                        "pest_risks": ["Stem Borer", "Leaf Roller"]
                    },
                    "Vegetative": {
                        "duration": 55,
                        "water_req": 100,
                        "nutrient_req": {"N": 50, "P": 30, "K": 30},
                        "pest_risks": ["Brown Plant Hopper", "Blast"]
                    },
                    "Reproductive": {
                        "duration": 35,
                        "water_req": 120,
                        "nutrient_req": {"N": 40, "P": 40, "K": 40},
                        "pest_risks": ["Neck Blast", "Sheath Blight"]
                    },
                    "Ripening": {
                        "duration": 30,
                        "water_req": 80,
                        "nutrient_req": {"N": 20, "P": 20, "K": 30},
                        "pest_risks": ["Grain Discoloration", "Rice Bug"]
                    }
                }
            },
        }
        
        # Initialize translator
        self.translator = Translator()
        
        # Cache for optimization recommendations
        self.recommendations_cache = {}
        
        # Try to load ML models if dependencies are available
        self.initialize_ml_components()

    def initialize_ml_components(self):
        """Initialize ML components if dependencies are available"""
        self.has_tensorflow = False
        self.has_sklearn = False
        
        try:
            import tensorflow as tf
            self.disease_model = tf.keras.models.load_model('models/disease_detection.h5')
            self.has_tensorflow = True
        except ImportError:
            pass
            
        try:
            from sklearn.ensemble import RandomForestRegressor
            self.yield_model = RandomForestRegressor()
            self.has_sklearn = True
        except ImportError:
            pass

    def detect_disease(self, image):
        """Detect crop diseases from image"""
        if not self.has_tensorflow:
            return "Disease detection requires TensorFlow. Please install it using: pip install tensorflow"
            
        try:
            import cv2
            # Preprocess image
            img = cv2.resize(image, (224, 224))
            img = img / 255.0
            img = np.expand_dims(img, axis=0)
            
            # Make prediction
            pred = self.disease_model.predict(img)
            return self.process_disease_prediction(pred)
        except ImportError:
            return "OpenCV (cv2) is required for image processing. Please install it using: pip install opencv-python"
        except Exception as e:
            return f"Error in disease detection: {str(e)}"

    def predict_yield(self, crop, weather_data, soil_data):
        """Predict crop yield based on conditions"""
        if not self.has_sklearn:
            return "Yield prediction requires scikit-learn. Please install it using: pip install scikit-learn"
            
        try:
            # Prepare features
            features = self.prepare_features(weather_data, soil_data)
            
            # Make prediction
            predicted_yield = self.yield_model.predict([features])[0]
            
            return {
                'predicted_yield': predicted_yield,
                'confidence': self.calculate_prediction_confidence()
            }
        except Exception as e:
            return f"Error in yield prediction: {str(e)}"

    def get_weather_forecast(self, location):
        """Fetch weather forecast data"""
        try:
            url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}?key={self.WEATHER_API_KEY}"
            response = requests.get(url)
            return response.json()
        except Exception as e:
            return f"Error fetching weather data: {str(e)}"

    def get_optimization_recommendations(self, crop, conditions, language='en'):
        """Generate resource optimization recommendations"""
        cache_key = f"{crop}_{language}"
        
        if cache_key in self.recommendations_cache:
            return self.recommendations_cache[cache_key]
            
        try:
            optimal = self.CROPS_DB[crop]["optimal_conditions"]
            current = conditions
            
            recommendations = {
                'water': self.calculate_water_recommendation(optimal, current),
                'fertilizer': self.calculate_fertilizer_recommendation(optimal, current),
                'pesticide': self.calculate_pesticide_recommendation(crop, current)
            }
            
            # Translate recommendations if needed
            if language != 'en':
                recommendations = self.translate_recommendations(recommendations, language)
                
            self.recommendations_cache[cache_key] = recommendations
            return recommendations
            
        except Exception as e:
            return f"Error generating recommendations: {str(e)}"

    def calculate_water_recommendation(self, optimal, current):
        """Calculate water recommendation based on conditions"""
        try:
            rainfall = current.get('rainfall', 0)
            humidity = current.get('humidity', 0)
            temperature = current.get('temperature', 0)
            
            # Basic water requirement calculation
            base_requirement = 100  # Base water requirement in mm
            
            # Adjust based on rainfall
            rainfall_adjustment = max(0, base_requirement - rainfall)
            
            # Adjust based on temperature and humidity
            temp_factor = max(1, (temperature - 20) * 0.1)  # Increase requirement for higher temperatures
            humidity_factor = max(0.5, 1 - (humidity / 100))  # Decrease requirement for higher humidity
            
            final_requirement = rainfall_adjustment * temp_factor * humidity_factor
            
            return {
                'recommendation': f"Water requirement: {final_requirement:.1f} mm",
                'details': {
                    'base_requirement': base_requirement,
                    'rainfall_adjustment': rainfall_adjustment,
                    'temperature_factor': temp_factor,
                    'humidity_factor': humidity_factor
                }
            }
        except Exception as e:
            return f"Error calculating water recommendation: {str(e)}"

    def calculate_fertilizer_recommendation(self, optimal, current):
        """Calculate fertilizer recommendation"""
        # Implement basic fertilizer calculation logic
        return {
            'recommendation': "Apply balanced NPK fertilizer",
            'details': {
                'N': "40 kg/ha",
                'P': "20 kg/ha",
                'K': "20 kg/ha"
            }
        }

    def calculate_pesticide_recommendation(self, crop, conditions):
        """Calculate pesticide recommendation"""
        # Implement basic pesticide recommendation logic
        return {
            'recommendation': "Monitor for common pests",
            'details': {
                'preventive': "Regular inspection recommended",
                'threshold': "Apply only when pest damage exceeds 10%"
            }
        }

def main():
    st.set_page_config(
        page_title="Smart Farming Assistant",
        page_icon="🌾",
        layout="wide"
    )
    
    # Check dependencies first
    check_dependencies()
    
    # Initialize the assistant
    assistant = SmartFarmingAssistant()
    
    # Sidebar for user inputs
    with st.sidebar:
        st.title("🌾 Smart Farming Assistant")
        
        selected_language = st.selectbox(
            "Select Language",
            list(assistant.LANGUAGES.keys())
        )
        
        location = st.text_input("Enter Location", "Delhi, India")
        
        selected_crop = st.selectbox(
            "Select Crop",
            list(assistant.CROPS_DB.keys())
        )
        
        area = st.number_input("Field Area (acres)", 0.1, 100.0, 1.0)
        
        farming_type = st.selectbox(
            "Farming Type",
            ["Traditional", "Organic", "Mixed"]
        )

    # Main content
    st.title("Precision Farming Optimization")
    
    tabs = st.tabs([
        "📊 Dashboard",
        "🌱 Crop Monitor",
        "💧 Resource Optimizer",
        "🔬 Soil Analysis",
        "📈 Yield Predictor"
    ])
    
    # Dashboard Tab
    with tabs[0]:
        st.header("Farm Dashboard")
        
        weather_data = assistant.get_weather_forecast(location)
        if isinstance(weather_data, dict):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Temperature", f"{weather_data['currentConditions']['temp']}°C")
            with col2:
                st.metric("Humidity", f"{weather_data['currentConditions']['humidity']}%")
            with col3:
                st.metric("Rainfall", f"{weather_data['currentConditions']['precip']} mm")

    # Crop Monitor Tab
    with tabs[1]:
        st.header("Crop Health Monitor")
        
        uploaded_file = st.file_uploader(
            "Upload crop image for disease detection",
            type=['jpg', 'jpeg', 'png']
        )
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            if st.button("Analyze Image"):
                with st.spinner("Analyzing image..."):
                    results = assistant.detect_disease(image)
                    st.write(results)
    
    # Resource Optimizer Tab
    with tabs[2]:
        st.header("Resource Optimization")
        
        if isinstance(weather_data, dict):
            current_conditions = {
                "temperature": weather_data['currentConditions']['temp'],
                "humidity": weather_data['currentConditions']['humidity'],
                "rainfall": weather_data['currentConditions']['precip']
            }
            
            recommendations = assistant.get_optimization_recommendations(
                selected_crop,
                current_conditions,
                assistant.LANGUAGES[selected_language]
            )
            
            if isinstance(recommendations, dict):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.subheader("💧 Water Usage")
                    st.write(recommendations['water']['recommendation'])
                    
                with col2:
                    st.subheader("🌿 Fertilizer Usage")
                    st.write(recommendations['fertilizer']['recommendation'])
                    
                with col3:
                    st.subheader("🔄 Pesticide Usage")
                    st.write(recommendations['pesticide']['recommendation'])

    # Yield Predictor Tab
    with tabs[4]:
        st.header("Yield Prediction")
        
        soil_ph = st.slider("Soil pH", 0.0, 14.0, 7.0)
        soil_moisture = st.slider("Soil Moisture (%)", 0, 100, 50)
        
        if st.button("Predict Yield"):
            with st.spinner("Calculating expected yield..."):
                prediction = assistant.predict_yield(
                    selected_crop,
                    weather_data,
                    {"ph": soil_ph, "moisture": soil_moisture}
                )
                
                if isinstance(prediction, dict):
                    st.success(f"Predicted Yield: {prediction['predicted_yield']} tons/acre")
                    st.info(f"Prediction Confidence: {prediction['confidence']}%")
                else:
                    st.warning(prediction)  # Show the error/installation message

if __name__ == "__main__":
    main()
