import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import io
import tensorflow as tf
import cv2
import json
from sklearn.ensemble import RandomForestRegressor
from googletrans import Translator

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
                "image": "rice.jpg",
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
            # Add similar structure for other crops
        }
        
        # Initialize ML models
        self.load_models()
        
        # Initialize translator
        self.translator = Translator()
        
        # Cache for optimization recommendations
        self.recommendations_cache = {}

    def load_models(self):
        """Load or initialize ML models"""
        try:
            # Load disease detection model
            self.disease_model = tf.keras.models.load_model('models/disease_detection.h5')
            
            # Initialize yield prediction model
            self.yield_model = RandomForestRegressor()
            # In production, load pretrained model
            
        except Exception as e:
            st.error(f"Error loading models: {str(e)}")

    def detect_disease(self, image):
        """Detect crop diseases from image"""
        try:
            # Preprocess image
            img = cv2.resize(image, (224, 224))
            img = img / 255.0
            img = np.expand_dims(img, axis=0)
            
            # Make prediction
            pred = self.disease_model.predict(img)
            return self.process_disease_prediction(pred)
        except Exception as e:
            return f"Error in disease detection: {str(e)}"

    def predict_yield(self, crop, weather_data, soil_data):
        """Predict crop yield based on conditions"""
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

    def get_optimization_recommendations(self, crop, conditions, language='en'):
        """Generate resource optimization recommendations"""
        cache_key = f"{crop}_{language}"
        
        if cache_key in self.recommendations_cache:
            return self.recommendations_cache[cache_key]
            
        try:
            optimal = self.CROPS_DB[crop]["optimal_conditions"]
            current = conditions
            
            recommendations = {
                'water': self.optimize_water_usage(optimal, current),
                'fertilizer': self.optimize_fertilizer_usage(optimal, current),
                'pesticide': self.optimize_pesticide_usage(crop, current)
            }
            
            # Translate recommendations if needed
            if language != 'en':
                recommendations = self.translate_recommendations(recommendations, language)
                
            self.recommendations_cache[cache_key] = recommendations
            return recommendations
            
        except Exception as e:
            return f"Error generating recommendations: {str(e)}"

    def optimize_water_usage(self, optimal, current):
        """Calculate optimal water usage"""
        # Implementation of water optimization logic
        pass

    def optimize_fertilizer_usage(self, optimal, current):
        """Calculate optimal fertilizer usage"""
        # Implementation of fertilizer optimization logic
        pass

    def optimize_pesticide_usage(self, crop, conditions):
        """Calculate optimal pesticide usage"""
        # Implementation of pesticide optimization logic
        pass

    def get_weather_forecast(self, location):
        """Fetch weather forecast data"""
        try:
            url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}?key={self.WEATHER_API_KEY}"
            response = requests.get(url)
            return response.json()
        except Exception as e:
            return f"Error fetching weather data: {str(e)}"

    def analyze_soil_image(self, image):
        """Analyze soil quality from image"""
        try:
            # Implement soil analysis logic
            # This could use another ML model specific to soil analysis
            pass
        except Exception as e:
            return f"Error in soil analysis: {str(e)}"

def main():
    st.set_page_config(
        page_title="Smart Farming Assistant",
        page_icon="🌾",
        layout="wide"
    )
    
    # Initialize the assistant
    assistant = SmartFarmingAssistant()
    
    # Sidebar for user inputs
    with st.sidebar:
        st.title("🌾 Smart Farming Assistant")
        
        # Language selection
        selected_language = st.selectbox(
            "Select Language",
            list(assistant.LANGUAGES.keys())
        )
        
        # Location input
        location = st.text_input("Enter Location", "Delhi, India")
        
        # Crop selection
        selected_crop = st.selectbox(
            "Select Crop",
            list(assistant.CROPS_DB.keys())
        )
        
        # Area input
        area = st.number_input("Field Area (acres)", 0.1, 100.0, 1.0)
        
        # Farming type
        farming_type = st.selectbox(
            "Farming Type",
            ["Traditional", "Organic", "Mixed"]
        )

    # Main content area
    st.title("Precision Farming Optimization")
    
    # Create tabs for different features
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
        
        # Weather information
        col1, col2, col3 = st.columns(3)
        
        weather_data = assistant.get_weather_forecast(location)
        if isinstance(weather_data, dict):
            with col1:
                st.metric("Temperature", f"{weather_data['currentConditions']['temp']}°C")
            with col2:
                st.metric("Humidity", f"{weather_data['currentConditions']['humidity']}%")
            with col3:
                st.metric("Rainfall", f"{weather_data['currentConditions']['precip']} mm")
        
        # Crop status summary
        st.subheader("Crop Status")
        status_cols = st.columns(4)
        
        # Add crop status metrics
        
    # Crop Monitor Tab
    with tabs[1]:
        st.header("Crop Health Monitor")
        
        # Image upload for disease detection
        uploaded_file = st.file_uploader(
            "Upload crop image for disease detection",
            type=['jpg', 'jpeg', 'png']
        )
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            if st.button("Analyze Image"):
                with st.spinner("Analyzing image..."):
                    # Process image and show results
                    results = assistant.detect_disease(image)
                    st.write(results)
    
    # Resource Optimizer Tab
    with tabs[2]:
        st.header("Resource Optimization")
        
        # Get current conditions
        current_conditions = {
            "temperature": weather_data['currentConditions']['temp'],
            "humidity": weather_data['currentConditions']['humidity'],
            "rainfall": weather_data['currentConditions']['precip']
        }
        
        # Get optimization recommendations
        recommendations = assistant.get_optimization_recommendations(
            selected_crop,
            current_conditions,
            assistant.LANGUAGES[selected_language]
        )
        
        # Display recommendations
        if isinstance(recommendations, dict):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("💧 Water Usage")
                st.write(recommendations['water'])
                
            with col2:
                st.subheader("🌿 Fertilizer Usage")
                st.write(recommendations['fertilizer'])
                
            with col3:
                st.subheader("🔄 Pesticide Usage")
                st.write(recommendations['pesticide'])
    
    # Soil Analysis Tab
    with tabs[3]:
        st.header("Soil Analysis")
        
        # Soil image upload
        soil_image = st.file_uploader(
            "Upload soil image for analysis",
            type=['jpg', 'jpeg', 'png']
        )
        
        if soil_image:
            image = Image.open(soil_image)
            st.image(image, caption="Soil Sample", use_column_width=True)
            
            if st.button("Analyze Soil"):
                with st.spinner("Analyzing soil quality..."):
                    # Process soil image and show results
                    soil_results = assistant.analyze_soil_image(image)
                    st.write(soil_results)
    
    # Yield Predictor Tab
    with tabs[4]:
        st.header("Yield Prediction")
        
        # Collect additional data for yield prediction
        soil_ph = st.slider("Soil pH", 0.0, 14.0, 7.0)
        soil_moisture = st.slider("Soil Moisture (%)", 0, 100, 50)
        
        if st.button("Predict Yield"):
            with st.spinner("Calculating expected yield..."):
                # Make yield prediction
                prediction = assistant.predict_yield(
                    selected_crop,
                    weather_data,
                    {"ph": soil_ph, "moisture": soil_moisture}
                )
                
                if isinstance(prediction, dict):
                    st.success(f"Predicted Yield: {prediction['predicted_yield']} tons/acre")
                    st.info(f"Prediction Confidence: {prediction['confidence']}%")

if __name__ == "__main__":
    main()
