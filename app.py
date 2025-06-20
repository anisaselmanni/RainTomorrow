import joblib as jl
import streamlit as st
import numpy as np  # Import numpy for array creation

# --- Load the model (assuming rain_model.pkl is in the same directory) ---
# In a real deployed environment, you would ensure 'rain_model.pkl' is accessible.
# For local development, place it in the same folder as this Streamlit script.
try:
    model = jl.load('rain_model.pkl')
    st.sidebar.success("Model 'rain_model.pkl' loaded successfully!")
except FileNotFoundError:
    st.error("Error: 'rain_model.pkl' not found. Please ensure the model file is in the same directory as this script.")
    st.stop()  # Stop the script if the model isn't found
except Exception as e:
    st.error(f"Error loading the model: {e}")
    st.stop()

st.title('☔ Weather Prediction in Australia 🇦🇺')
st.markdown("""
Enter the weather parameters below to predict if it will rain tomorrow.
""")

# Define the features your model expects in the exact order
features_list = [
    'MinTemp', 'MaxTemp', 'Rainfall', 'WindGustSpeed', 'WindSpeed9am',
    'WindSpeed3pm', 'Humidity9am', 'Humidity3pm', 'Pressure9am',
    'Pressure3pm', 'Cloud9am', 'Cloud3pm', 'Temp9am', 'Temp3pm', 'RainToday', 'Month',  # Added 'RainToday'
    'WindGustDir_ENE', 'WindGustDir_ESE', 'WindGustDir_N', 'WindGustDir_NE',
    'WindGustDir_NNE', 'WindGustDir_NNW', 'WindGustDir_NW', 'WindGustDir_S',
    'WindGustDir_SE', 'WindGustDir_SSE', 'WindGustDir_SSW', 'WindGustDir_SW',
    'WindGustDir_W', 'WindGustDir_WNW', 'WindGustDir_WSW'
]

# Create a dictionary to hold input values for each feature
input_data = {}

# --- Input Widgets for Numerical Features ---
st.header("Daily Weather Measurements")

# Layout numerical inputs in two columns for better organization
col1, col2 = st.columns(2)

with col1:
    st.subheader("Temperature, Rainfall & Humidity")
    input_data['MinTemp'] = st.number_input('Minimum Temperature (°C)', value=13.4, step=0.1, format="%.1f",
                                            help="Lowest temperature recorded in the 24 hours to 9am")
    input_data['MaxTemp'] = st.number_input('Maximum Temperature (°C)', value=22.9, step=0.1, format="%.1f",
                                            help="Highest temperature recorded in the 24 hours to 3pm")
    input_data['Rainfall'] = st.number_input('Rainfall (mm)', value=0.6, step=0.1, format="%.1f",
                                             help="Amount of rainfall recorded in the 24 hours to 9am (0.0 for no rain)")
    input_data['Humidity9am'] = st.slider('Humidity at 9am (%)', 0, 100, 71, help="Humidity (percent) at 9am")
    input_data['Humidity3pm'] = st.slider('Humidity at 3pm (%)', 0, 100, 22, help="Humidity (percent) at 3pm")

with col2:
    st.subheader("Wind & Pressure")
    input_data['WindGustSpeed'] = st.number_input('Wind Gust Speed (km/h)', value=44.0, step=1.0, format="%.1f",
                                                  help="Speed (km/h) of the strongest wind gust in the 24 hours to midnight")
    input_data['WindSpeed9am'] = st.number_input('Wind Speed at 9am (km/h)', value=20.0, step=1.0, format="%.1f",
                                                 help="Wind speed (km/h) averaged over 10 minutes prior to 9am")
    input_data['WindSpeed3pm'] = st.number_input('Wind Speed at 3pm (km/h)', value=24.0, step=1.0, format="%.1f",
                                                 help="Wind speed (km/h) averaged over 10 minutes prior to 3pm")
    input_data['Pressure9am'] = st.number_input('Pressure at 9am (hPa)', value=1007.7, step=0.1, format="%.1f",
                                                help="Atmospheric pressure (hpa) reduced to mean sea level at 9am")
    input_data['Pressure3pm'] = st.number_input('Pressure at 3pm (hPa)', value=1007.1, step=0.1, format="%.1f",
                                                help="Atmospheric pressure (hpa) reduced to mean sea level at 3pm")

# Cloud and Temperature at specific times, RainToday, and Month
st.subheader("Additional Measurements")
cloud_col1, cloud_col2, temp_col1, temp_col2, rain_today_col, month_col = st.columns(
    6)  # Increased columns to accommodate RainToday
with cloud_col1:
    input_data['Cloud9am'] = st.slider('Cloud Cover at 9am (oktas)', 0, 9, 8,
                                       help="Fraction of sky obscured by cloud at 9am. 0=clear, 8=overcast.")
with cloud_col2:
    input_data['Cloud3pm'] = st.slider('Cloud Cover at 3pm (oktas)', 0, 9, 5,
                                       help="Fraction of sky obscured by cloud at 3pm. 0=clear, 8=overcast.")
with temp_col1:
    input_data['Temp9am'] = st.number_input('Temperature at 9am (°C)', value=16.9, step=0.1, format="%.1f",
                                            help="Temperature (degrees C) at 9am")
with temp_col2:
    input_data['Temp3pm'] = st.number_input('Temperature at 3pm (°C)', value=21.8, step=0.1, format="%.1f",
                                            help="Temperature (degrees C) at 3pm")
with rain_today_col:
    # Assuming RainToday is a binary (Yes/No or 1/0) feature
    rain_today_option = st.radio(
        'Did it rain today?',
        ('No', 'Yes'),
        index=0,  # Default to 'No'
        help="Did it rain in the 24 hours to 9am today? 'Yes' if Rainfall >= 1mm, otherwise 'No'."
    )
    input_data['RainToday'] = 1 if rain_today_option == 'Yes' else 0
with month_col:
    input_data['Month'] = st.slider('Month', 1, 12, 12, help="Month of the year (1 for January, 12 for December)")

# --- Input Widget for One-Hot Encoded Categorical Features (Wind Gust Direction) ---
st.subheader("Wind Gust Direction")
wind_directions = [
    'ENE', 'ESE', 'N', 'NE', 'NNE', 'NNW', 'NW', 'S', 'SE', 'SSE',
    'SSW', 'SW', 'W', 'WNW', 'WSW'
]
# Add 'None' option if the direction is unknown or not specified
selected_wind_dir = st.radio(
    "Select the predominant Wind Gust Direction:",
    ['None'] + wind_directions,
    index=0,  # 'None' selected by default
    help="Direction of the strongest wind gust in the 24 hours to midnight (e.g., W, ENE, N)"
)

# Initialize all one-hot encoded wind direction features to 0
for direction in wind_directions:
    input_data[f'WindGustDir_{direction}'] = 0

# Set the selected wind direction to 1 if one is chosen
if selected_wind_dir != 'None':
    input_data[f'WindGustDir_{selected_wind_dir}'] = 1

st.markdown("---")  # Separator

# --- Prediction Button and Output ---
if st.button('Predict Rain Tomorrow'):
    # Prepare the input array in the exact order required by the model
    # Convert dictionary values to a list in the order of features_list
    model_input_values = [input_data[feature] for feature in features_list]

    # Convert to a NumPy array and reshape for single sample prediction
    final_model_input = np.array(model_input_values).reshape(1, -1)

    # Make prediction
    with st.spinner("Making prediction..."):
        try:
            prediction = model.predict(final_model_input)
            st.success("Prediction Complete!")

            # Display result based on model output (assuming 'No' or 'Yes')
            if prediction[0] == 'No':
                st.balloons()  # Add a small celebration for no rain!
                st.metric(label="Will it rain tomorrow?", value="No ☀️", delta="Clear skies expected!")
                st.markdown("Enjoy your day!")
            else:
                st.snow()  # Add a snow effect for rain, might be visually surprising but fun!
                st.metric(label="Will it rain tomorrow?", value="Yes 🌧️",
                          delta="Rain is likely! Don't forget your umbrella!")
                st.markdown("Be prepared for some wet weather.")

        except Exception as e:
            st.error(f"An error occurred during prediction: {e}")
            st.warning("Please check your input values and ensure they are within a reasonable range for the model.")

st.markdown("---")
st.caption(
    "This application uses a pre-trained machine learning model (`rain_model.pkl`) to predict rainfall in Australia based on the provided weather parameters.")
