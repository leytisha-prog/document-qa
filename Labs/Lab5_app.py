import streamlit as st
import requests
# Location - City, State, Country
location = "City, State, Country"  # Replace with your desired location

# FUNCTION to get current weather data
api_key = st.secrets["WEATHER_API_KEY"] 
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

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

if st.button("Get Current Weather"):
    if city:
        get_current_weather = get_current_weather(city)
        if get_current_weather:
            main_data = get_current_weather['main']
            st.success(f"Current weather in {city}: {main_data['temp']}°C, {main_data['weather_description']}")
        else:
            st.error("Could not retrieve weather data. Please check the city name and try again.")
    else:
        st.warning("Please enter a city name to get the current weather.")
