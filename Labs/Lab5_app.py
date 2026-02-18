import requests
# Location - City, State, Country
location = "Syracuse, NY, USA"

# FUNCTION to get current weather data

def get_current_weather(location, api_key, units="imperial"):
    url=(
        f'https://api.openweathermap.org/data/2.5/weather'
        f'?q={location}&appid={api_key}&units={units}'
    )

    response = requests.get(url)
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
    