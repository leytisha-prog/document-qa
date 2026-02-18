import streamlit as st
import requests
# Location - City, State, Country
location = "Syracuse, NY, USA"

# FUNCTION to get current weather data
api_key = st.secrets["weather_api_key"]
Base_URL = "https://api.openweathermap.org/data/2.5/weather"

def get_current_weather(city_name):
    params = {
        "q": city_name,
        "appid": api_key,
        "units": "metric", # or "imperial" for Fahrenheit
    }

    response = requests.get(Base_URL, params=params)
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
city = st.text_input("Enter a city name:", value="Syracuse")

if st.button("Get Current Weather"):
    try:
        api_key = st.secrets["weather_api_key"]
        weather_data = get_current_weather(city, api_key)
        st.write(f"Current Weather in {weather_data['location']}:")
        st.write(f"Temperature: {weather_data['temperature']}°C or {round(weather_data['temperature'] * 9/5 + 32, 2)}°F")
        st.write(f"Feels Like: {weather_data['feels_like']}°C or {round(weather_data['feels_like'] * 9/5 + 32, 2)}°F")
        st.write(f"Min Temperature: {weather_data['temp_min']}°C or {round(weather_data['temp_min'] * 9/5 + 32, 2)}°F")
        st.write(f"Max Temperature: {weather_data['temp_max']}°C or {round(weather_data['temp_max'] * 9/5 + 32, 2)}°F")
        st.write(f"Humidity: {weather_data['humidity']}%")
        st.write(f"Weather Description: {weather_data['weather_description']}")
    except Exception as e:
        st.error(f"Error fetching weather data: {e}")

    else:
        st.error("Please enter a city name to get the current weather.")
        
else:
    st.warning("API error: refresh the page and try again.")
