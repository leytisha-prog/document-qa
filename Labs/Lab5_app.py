import streamlit as st
import requests
from streamlit_folium import st_folium
import folium  
from geopy.geocoders import Nominatim   

# ---- Configuration
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
api_key = st.secrets["WEATHER_API_KEY"]  # Ensure you have your API key in Streamlit secrets

# Create a geolocator once to reuse for multiple geocoding requests
geolocator = Nominatim(user_agent="Current_Weather_App")

# Sidebar for user input (choices for temp units, metric/imperial)
st.sidebar.title("Settings")
unit = st.sidebar.selectbox("Units", ["imperial (°F)", "metric (°C)"])
units_param = "imperial" if unit.startswith("imperial") else "metric"
temp_symbol = "°F" if units_param == "imperial" else "°C"

# -------- Helper functions 
def get_location_coords(city_name):
    """Converts a city name to latitude and longitude using geopy."""
    loc = geolocator.geocode(city_name)
    if loc:
        return loc.latitude, loc.longitude, loc.address
    return None, None, None

def fetch_current_weather(lat, lon, api_key):
    """Fetches current weather from OpenWeatherMap by coordinates."""
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": units_param,
    }
    response = requests.get(BASE_URL, params=params, timeout=15)
    if response.status_code == 401:
        raise Exception("401 Unauthorized: Invalid API key.")
    if response.status_code == 404:
        raise Exception("404 Not Found: location not found by API.")
    response.raise_for_status()

    return response.json()

# ----------- UI 
city = st.text_input("Enter a city name (e.g., 'Syracuse, NY'):")

if st.button("Get Weather"):
    if not city:
        st.warning("Please enter a city name.")
        st.stop ()
    
    lat, lon, full_address = get_location_coords(city)

    if lat is None or lon is None:
        st.error("Could not find that city. Try adding state/country (e.g., 'Syracuse, NY').")
        st.error()

    st.success(f"Found location: {full_address} (Lat: {lat:.4f}, Lon: {lon:.4f})")

    try:
        weather_data = fetch_current_weather(lat, lon, api_key)
    except Exception as e: 
        st.error(f"Could not fetch weather data: {e}")
        st.stop()

# -------- Display weather data 
if st.button("Show Weather Data"):

    st.subheader(f"Current Weather: {weather_data['name']}")

    temp = weather_data["main"]["temp"]
    humidity = weather_data["main"]["humidity"]
    desc = weather_data["weather"][0]["description"].capitalize()

    col1, col2, col3 = st.columns(3)
    col1.metric("Temperature", f"{temp}{temp_symbol}")
    col2.metric("Humidity", f"{humidity}%")
    col3.metric("Condition", desc)

    # Map
    st.subheader("Location Map")
    m = folium.Map(location=[lat, lon], zoom_start=12)
    folium.Marker([lat, lon], popup=weather_data["name"]).add_to(m)
    st_folium(m, width=700, height=500)

