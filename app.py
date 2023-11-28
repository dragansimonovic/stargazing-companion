import streamlit as st
import pandas as pd
import time
from datetime import datetime, date, timedelta
import requests
import openai

openai.api_key = st.secrets["openai_api_key"]
weather_api_key = st.secrets["weather_api_key"]
opencage_api_key = st.secrets["opencage_api_key"]

def get_coordinates(city):
    url = f"https://api.opencagedata.com/geocode/v1/json"
    params = {'q': city, 'key': opencage_api_key}
    response = requests.get(url, params=params)
    if response.status_code == 200 and response.json()['results']:
        location = response.json()['results'][0]['geometry']
        return location['lat'], location['lng']
    else:
        return None, None

def get_gpt3_content(prompt):
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=150  # Adjust as needed
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"An error occurred: {str(e)}"

def get_astronomical_info(city, date_str):
    constellations_prompt = f"Describe the constellations visible in {city} on {date_str}."
    planets_prompt = f"List the planets visible in {city} on {date_str} and provide brief details about them."
    events_prompt = f"Describe any upcoming celestial events visible in {city} around {date_str}."

    constellations_info = get_gpt3_content(constellations_prompt)
    planets_info = get_gpt3_content(planets_prompt)
    events_info = get_gpt3_content(events_prompt)

    return constellations_info, planets_info, events_info

def get_stargazing_location(lat, lng):
    # Simplified logic to find a nearby rural area (adjusting latitude and longitude)
    rural_lat = lat + 0  # Adjust the value as needed
    rural_lng = lng + 0  # Adjust the value as needed
    return rural_lat, rural_lng

def get_weather_info(city, date_str, weather_api_key):
    # Convert the date to datetime object for comparison
    target_date = datetime.strptime(date_str, "%Y-%m-%d")
    target_date_end = target_date + timedelta(days=1)

    # Fetch weather data
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={weather_api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        forecast_data = response.json()['list']
        for data in forecast_data:
            forecast_date = datetime.fromtimestamp(data['dt'])
            if target_date <= forecast_date < target_date_end:
                # Found the data for the selected date
                return {
                    "Main": data['weather'][0]['main'],
                    "Description": data['weather'][0]['description'],
                    "Temperature": data['main']['temp'],
                    "Feels Like": data['main']['feels_like'],
                    "Clouds": data['clouds']['all'],
                    "Visibility": data['visibility']
                }
    return None

def main():
    st.title(":telescope: Stargazing Companion")
        
    with st.form("stargazing_form"):
        header_image_path = 'header_image.png'
        st.image(header_image_path, use_column_width=True, caption='Explore the wonders of the night sky')
        
        st.markdown('Simply input your location and the date of your stargazing adventure, and Stargazing Companion will curate a personalized guide showcasing visible constellations, planets, and notable cosmic occurrences that await you in your night sky journey!')
        
        col1, col2 = st.columns(2)
        
        with col1:
            city = st.text_input("Enter your city:")
        with col2:
            selected_date = st.date_input("Select a date for stargazing:", min_value=date.today())
        submit_button = st.form_submit_button("Get Stargazing Info", type="primary")

    if submit_button and city:
        lat, lng = get_coordinates(city)
        date_str = selected_date.strftime("%Y-%m-%d")

        if lat is not None and lng is not None:
            with st.status("Fetching your personalized stargazing information...", expanded=True) as status:
                st.write("Searching for data...")
                constellations_info, planets_info, events_info = get_astronomical_info(city, date_str)
                #time.sleep(1)
                st.write("Analyzing data...")
                weather_info = get_weather_info(city, date_str, weather_api_key)
                time.sleep(1)
                st.write("Putting everything together...")
                rural_lat, rural_lng = get_stargazing_location(lat, lng)
                time.sleep(1)
                status.update(label="Done!", state="complete", expanded=False)
            
            with st.empty():
                st.write("&nbsp;", unsafe_allow_html=True)

            formatted_date = selected_date.strftime("%b %d, %Y")
            st.subheader(f":thermometer: Weather conditions in {city} on {formatted_date}")
            
            if weather_info:
                wcol1, wcol2, wcol3, wcol4, wcol5 = st.columns(5)
                with wcol1:
                    description_title_case = weather_info['Description'].title()
                    st.markdown(f"{weather_info['Main']}:<br>**{description_title_case}**", unsafe_allow_html=True)
                with wcol2:
                    st.markdown(f"Temperature:<br>**{weather_info['Temperature']} °C**", unsafe_allow_html=True)
                with wcol3:
                    st.markdown(f"Feels Like:<br>**{weather_info['Feels Like']} °C**", unsafe_allow_html=True)
                with wcol4:
                    st.markdown(f"Clouds:<br>**{weather_info['Clouds']}%**", unsafe_allow_html=True)
                with wcol5:
                    st.markdown(f"Visibility:<br>**{weather_info['Visibility']} meters**", unsafe_allow_html=True)
            else:
                st.error("Weather data not available for the selected date.")

            
            # Create a DataFrame for the map
            map_data = pd.DataFrame({
                'lat': [rural_lat],
                'lon': [rural_lng]
            })
            st.map(map_data)
            
            st.subheader("Constellations")
            st.write(constellations_info)

            st.subheader("Planets")
            st.write(planets_info)

            st.subheader("Upcoming Celestial Events")
            st.write(events_info)
            
            #st.subheader("Observation Tips")
            #st.write("A nearby rural area, away from city lights, is recommended for the best stargazing experience.")

        else:
            st.error("Unable to fetch location data. Please try a different city.")

if __name__ == "__main__":
    main()