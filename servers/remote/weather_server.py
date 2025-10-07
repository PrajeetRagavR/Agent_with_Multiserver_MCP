# import os
# import requests
# from mcp.server.fastmcp import FastMCP

# # ---------------------------------------------------------------------
# # Initialize the MCP Server
# # ---------------------------------------------------------------------
# mcp = FastMCP("Weather")

# # ---------------------------------------------------------------------
# # Configuration
# # ---------------------------------------------------------------------
# WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")  # Set this in your .env or shell
# BASE_WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"

# # Default server configuration (override with env vars)
# HOST = os.getenv("MCP_HOST", "0.0.0.0")   # Use "localhost" for local-only
# PORT = int(os.getenv("MCP_PORT", "9000")) # Default port 9000
# ROOT_PATH = os.getenv("MCP_ROOT_PATH", "") # Optional URL prefix, e.g. "/weather"

# # ---------------------------------------------------------------------
# # Define MCP Tool
# # ---------------------------------------------------------------------
# @mcp.tool()
# def get_current_weather(city: str) -> str:
#     """
#     Fetch the current weather for a given city from OpenWeatherMap API.
#     """
#     if not WEATHER_API_KEY:
#         return "❌ Weather API key not set. Please set WEATHER_API_KEY in your environment."

#     params = {
#         "q": city,
#         "appid": WEATHER_API_KEY,
#         "units": "metric"  # Use 'imperial' for Fahrenheit
#     }

#     try:
#         response = requests.get(BASE_WEATHER_URL, params=params, timeout=5)
#         response.raise_for_status()
#         data = response.json()

#         if data.get("cod") == "404":
#             return f"⚠️ City '{city}' not found."

#         # Extract key weather details
#         main = data.get("main", {})
#         desc = data.get("weather", [{}])[0].get("description", "N/A").capitalize()
#         temp = main.get("temp", "N/A")
#         feels = main.get("feels_like", "N/A")
#         humidity = main.get("humidity", "N/A")

#         # Build human-readable response
#         return (
#             f"🌤️ Weather in {city}:\n"
#             f"- Condition: {desc}\n"
#             f"- Temperature: {temp}°C (feels like {feels}°C)\n"
#             f"- Humidity: {humidity}%"
#         )

#     except requests.exceptions.RequestException as e:
#         return f"⚠️ Network error while fetching weather data: {e}"
#     except Exception as e:
#         return f"🚨 Unexpected error occurred: {e}"

# if __name__ == "__main__":
#     mcp.run(transport="streamable-http", host="127.0.0.1", port=8002)

