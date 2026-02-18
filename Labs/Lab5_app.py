import streamlit as st
import requests
import pandas as pd
from streamlit_folium import st_folium
import folium  
from geopy.geocoders import Nominatim   


geolocator = Nominatim(user_agent="Current_Weather_App")
# Geocode an address
address = "107 College Pl, Syracuse, NY"  # Example address
location = geolocator.geocode(address)

if location:
    print(f"Address: {location.address}")
    print(f"Latitude: {location.latitude}, Longitude: {location.longitude}")
else:
    print("Location not found.")

# Location - City, State, Country
location = "City, State, Country"  # Replace with your desired location

# FUNCTION to get current weather data
api_key = st.secrets["WEATHER_API_KEY"] 
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

def get_current_weather(lat, lon, api_key):
    """Fetches current weather data from OpenWeatherMap API."""
    url = f"{BASE_URL}?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_location_coords(city_name):
    """Converts a city name to latitude and longitude using geopy."""
    geolocator = Nominatim(user_agent="Current_Weather_App")
    location = geolocator.geocode(city_name)
    if location:
        return location.latitude, location.longitude
    else:
        return None, None



def get_current_weather(city_name):
    params = {
        "q": city_name,
        "appid": st.secrets["WEATHER_API_KEY"],
        "units": "metric", # or "imperial" for Fahrenheit
    }

    response = requests.get(BASE_URL, params=params)
    if response.status_code == 401:
        raise Exception('Authentication failed. Invalid API key (401 unauthorized).')
    
    if response.status_code == 404:
        error_message = response.json().get('message')
        raise Exception(f'404 Not Found: {error_message}')
    
    data=response.json()
    temperature = data['main']['temp']
    feels_like = data['main']['feels_like']
    temp_min = data['main']['temp_min']
    temp_max = data['main']['temp_max']
    humidity = data['main']['humidity']
    weather_description = data['weather'][0]['description'] 

    return {'location': location,
            'temperature': round(temperature, 2),
            'feels_like': round(feels_like, 2),
            'temp_min': round(temp_min, 2),
            'temp_max': round(temp_max, 2),
            'humidity': round(humidity, 2),
            'weather_description': weather_description
    }
    
st.title("Current Weather App")
city = st.text_input("Enter a city name:")

if st.button("Get Weather"):
    if city:
        lat, lon = get_location_coords(city)
        
        if lat is not None and lon is not None:
            st.success(f"Found location: {city} (Lat: {lat}, Lon: {lon})")
            
            # 1. Fetch weather data
            weather_data = get_current_weather(lat, lon, api_key)
            
            if weather_data:
                # 2. Display weather data
                st.subheader(f"Current Weather in {weather_data['name']}")
                col1, col2, col3 = st.columns(3)
                col1.metric("Temperature", f"{weather_data['main']['temp']}°C", )
                col2.metric("Humidity", f"{weather_data['main']['humidity']}%")
                col3.metric("Condition", weather_data['weather'][0]['description'].capitalize())
                
                # 3. Display map using streamlit-folium for better interactivity/control
                st.subheader("Location Map")
                m = folium.Map(location=[lat, lon], zoom_start=12)
                folium.Marker([lat, lon], popup=f"{weather_data['name']}").add_to(m)
                st_folium(m, width=700, height=500)
                
            else:
                st.error("Could not fetch weather data. Check your API key or try again.")
        else:
            st.error("Could not find the city. Please check the name and try again.")
    else:
        st.warning("Please enter a city name.")
