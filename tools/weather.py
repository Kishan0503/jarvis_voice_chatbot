import json # Keep import, but don't use json.dumps for returns
import requests
import os
from typing import Dict, Any, Union

# Import app_config for API key
from config import app_config

# Import Tool and FunctionDeclaration types from google.generativeai
from google.generativeai.types import Tool, FunctionDeclaration

# Retrieve OpenWeatherMap API Key
OPENWEATHER_API_KEY = app_config.OPENWEATHER_API_KEY

def get_current_weather(location: str, unit: str = "celsius") -> Dict[str, Any]:
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric" if unit.lower() == "celsius" else "imperial"
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("cod") == 200:
            temp = data["main"]["temp"]
            conditions = data["weather"][0]["description"]
            city_name = data["name"]
            country_code = data["sys"]["country"]
            temp_unit_symbol = "°C" if unit.lower() == "celsius" else "°F"

            return {
                "status": "success",
                "location": f"{city_name}, {country_code}",
                "temperature": f"{temp}{temp_unit_symbol}",
                "conditions": conditions.capitalize()
            }
        else:
            error_message = data.get("message", "Could not retrieve weather data.")
            return {
                "status": "error",
                "message": error_message,
                "location": location
            }

    except requests.exceptions.HTTPError as http_err:
        return {
            "status": "error",
            "message": f"HTTP error: {http_err.response.status_code if http_err.response else 'N/A'}",
            "location": location
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "message": "Network error connecting to weather service.",
            "location": location
        }
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "Weather service request timed out.",
            "location": location
        }
    except requests.exceptions.RequestException as req_err:
        return {
            "status": "error",
            "message": f"Request exception: {str(req_err)}",
            "location": location
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Internal error: {str(e)}",
            "location": location
        }

# Define the FunctionDeclaration for the weather tool (NO CHANGE HERE)
weather_tool_declaration = FunctionDeclaration(
    name="get_current_weather",
    description="Gets the current weather for a given location (city, state, or country).",
    parameters={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "The city, state, or country, e.g. San Francisco, CA, London, or India."},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "description": "The unit for the temperature. Can be 'celsius' or 'fahrenheit'. Defaults to 'celsius'."},
        },
        "required": ["location"],
    },
)

# You might want to define a dictionary mapping tool names to their actual Python functions (NO CHANGE HERE)
tool_functions = {
    "get_current_weather": get_current_weather
}