import json
import time
import random
import requests 
import streamlit as st
from openai import OpenAI 
from streamlit_folium import st_folium
import folium  


# ---- Configuration 
st.set_page_config(page_title="Lab 5", page_icon="🧣", layout="wide")  
st.title("Lab 5 --> What to Wear Bot 🧣🌦🧥")
st.write("Enter a city and I'll tell you what to wear based on the current weather conditions!")

OPENAI_API_KEY = st.secrets["OPEN_AI_KEY"] # It's already set in Streamlit app settings
WEATHER_API_KEY = st.secrets["WEATHER_API_KEY"] # This also set in Streamlit app settings 

client = OpenAI(api_key=OPENAI_API_KEY)

# ------- SIDEBAR - UI settings 
st.sidebar.header("Settings")
unit = st.sidebar.selectbox("Units", ["imperial (°F)", "metric (°C)"], index=0)
units_param = "imperial" if unit.startswith("imperial") else "metric"
temp_symbol = "°F" if units_param == "imperial" else "°C"


# -------- Weather TOOL Function - used by LLM to get weather data
def get_weather(location: str) -> dict:
    """
    Tool function for OpenAI tool-calling 
    - If location is missing, default to 'Syracuse, NY' (lab requirement)
    - Uses OpenWeather Geocoding API to get lat/lon for the location
    - Uses OpenWeather Current Weather API -> weather details
    - Returns compact JSON including lat/lon for map rendering.
    """ 
    if not location or not location.strip():
        location = "Syracuse, NY" # if none is provided, default to Syracuse, NY
    # Step 1: Geocoding API to get lat/lon
    geocode_url = f"https://api.openweathermap.org/geo/1.0/direct"
    geocode_params = {
        "q": location,
        "limit": 1,
        "appid": WEATHER_API_KEY
    }
    geocode_response = requests.get(geocode_url, params=geocode_params, timeout=15)
    st.write("Geocode status:", geocode_response.status_code)
    st.write("Geocode raw response:", geocode_response.text)

    geocode_response.raise_for_status()
    geo = geocode_response.json()

    if not geo:
        return {"error": f"Could not geocode location: {location}", "location_requested": location}
    
    lat = geo[0] ["lat"]
    lon = geo[0] ["lon"]    
    name = geo[0].get("name", location)
    state = geo[0].get("state", "")
    country = geo[0].get("country", "")

    location_resolved = ", ".join([p for p in [name, state, country] if p]).strip()

    # Step 2: Current Weather API to get weather details - by lat/lon
    weather_url = f"http://api.openweathermap.org/data/2.5/weather"
    weather_params = {"lat": lat, "lon": lon, "appid": WEATHER_API_KEY, "units": units_param}
    weather_response = requests.get(weather_url, params=weather_params, timeout=15)

    # Error message if things go wrong 
    if weather_response.status_code == 401:
        return{"error": "401 Unauthorized - invalid API key."}
    weather_response.raise_for_status()

    data = weather_response.json()

    return{
        "location_requested": location,
        "location_resolved": location_resolved,
        "lat": lat,
        "lon": lon,
        "units": units_param,
        "temperature": data["main"]["temp"],
        "feels_like": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
        "wind_speed": data.get["wind", {}].get("speed"), 
        "conditions": data["weather"][0]["description"],

    }

# ------- OpenAI Tool Definition
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather conditions for a location (city, state, country). Returns lat/lon and weather details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and state, e.g. 'Syracuse, NY' or 'Paris, France'. If empty, defaults to 'Syracuse, NY'."
                    }
                },
                "required": ["location"]
            }
        }
    }
]


# ------- UI - Not a Chabot 
city = st.text_input("City (e.g., Syracuse, NY)", placeholder="Syracuse, NY")
run = st.button("Get clothing and activity suggestions")

if run:
    # 6. user inputs city; bot outputs advice (not chat)
    user_location = city.strip() if city else ""

    # First call - let the model decides if it needs weather (too_choice='auto')
    messages = [
        {
            "role": "system",
            "content": (
                "You are a 'What to Wear Bot' assistant."
                 "If you need current weather to answer, call the get_weather tool."
                 "Provide clothing details suggestions based on the weather conditions, temperature, and user preferences."
            ),
        },
        {
            "role": "user",
            "content": (
                f"My city is {user_location}. What should I wear today and what outdoor activities are appropriate?"
                if user_location
                else "What should I i wear today and what outdoor activities are appropriate?"
            ),
        },
    ]

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        temperature=0.3,
    )

    message = response.choices[0].message

    weather = None

    # If tool was requested, run it 
    if message.tool_calls:
        tool_call = message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)

        location = args.get("location") or "Syracuse, NY" # default if empty
        with st.spinner (f"Fetching weather for {location}..."):
            weather = get_weather(location)

        # If tool returned an error, show and stop
        if weather.get("error"):
            st.error(weather["error"])
            st.stop()

        # Second call: provide tool output to the model and ask for final advice
        messages.append(message) # assistant tool-call message
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": "get_weather",
                "content": json.dumps(weather),
            }
        )

        messages.append(
            {
                "role": "user",
                "content": (
                    "Using the weather data above, provide:\n"
                    "1. What to wear today (top, bottom, shoes, outerwear, accessories)\n"
                    "2. 2-4 outdoor activities appropriate for the weather conditions.\n"
                    "Be practical and specific."
                ),
            }
        )

        response2 = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            temperature=0.4,

        )
        
        advice = response2.choices[0].message.content
    
    else:
        # Model answered without using tool - just show the answer
        advice = message.content

    # ------- Display the advice and weather info - as well as map
    st.subheader("Advice and Weather Information")
    st.write(advice)

    if weather:
        st.subheader("Weather used (tool result)")
        st.json(weather)

        # Map visualization
        st.subheader("Map")
        m = folium.Map(location=[weather["lat"], weather["lon"]], zoom_start=11)
        folium.Marker(
            [weather["lat"], weather["lon"]],
            popup=weather["location_resolved"],
            tooltip=weather["location_resolved"],
        ).add_to(m)
        st_folium(m, width=800, height=450)
        


