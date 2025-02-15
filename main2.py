import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
from geopy.distance import geodesic
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest

# Load Data Without Caching
def load_data():
    known_routes = pd.read_csv(r"final_known_route_repo.csv")
    ongoing_trips = pd.read_csv(r"filtered_ongoing_trip_data.csv")

    # Convert date and time to timestamps
    known_routes['Timestamp'] = pd.to_datetime(known_routes['Date'] + ' ' + known_routes['Time'])
    ongoing_trips['Timestamp'] = pd.to_datetime(ongoing_trips['Date'] + ' ' + ongoing_trips['Time'])
    
    # Drop unnecessary columns
    known_routes.drop(columns=['Date', 'Time'], errors='ignore', inplace=True)
    ongoing_trips.drop(columns=['Date', 'Time'], errors='ignore', inplace=True)
    
    return known_routes, ongoing_trips

# Load data
known_routes, ongoing_trips = load_data()

# Sidebar Configurations
st.sidebar.title("PalletSense Monitoring Dashboard")
stationary_threshold = st.sidebar.slider('Stationary Threshold (Hours)', min_value=12, max_value=168, value=48)

# Function to Calculate Distance Between GPS Coordinates
def haversine(coord1, coord2):
    return geodesic(coord1, coord2).meters

# Detect Stationary Pallets
def detect_stationary_pallets(data):
    stationary_pallets = []
    alerts = []
    
    # Group by pallet ID
    for pallet_id, group in data.groupby('Pallet_ID'):
        group = group.sort_values(by='Timestamp')
        first_entry = group.iloc[0]
        last_entry = group.iloc[-1]
        
        # Check if the pallet has moved significantly
        distance_travelled = haversine((first_entry['latitude'], first_entry['longitude']), 
                                       (last_entry['latitude'], last_entry['longitude']))
        time_spent = (last_entry['Timestamp'] - first_entry['Timestamp']).total_seconds() / 3600
        
        if distance_travelled < 500 and time_spent >= stationary_threshold:
            stationary_pallets.append((pallet_id, last_entry['Timestamp'], time_spent))
            
            # Alert System
            if time_spent >= (0.8 * stationary_threshold):
                alerts.append((pallet_id, "🚨 Initial Warning: Exceeded 80% dwell time"))
            if time_spent >= (stationary_threshold + 2 * np.std(data['Timestamp'].diff().dt.total_seconds() / 3600)):
                alerts.append((pallet_id, "🔴 Critical Alert: 2σ Deviation"))
            if time_spent >= (stationary_threshold + 3 * np.std(data['Timestamp'].diff().dt.total_seconds() / 3600)):
                alerts.append((pallet_id, "⚠️ Escalation: 3σ Deviation"))
    
    return pd.DataFrame(stationary_pallets, columns=['Pallet_ID', 'Last_Timestamp', 'Hours_Stationary']), alerts

# Identify Stationary Pallets
stationary_df, alerts = detect_stationary_pallets(ongoing_trips)

# Display Stationary Pallets
st.subheader("📌 Stationary Pallets")
st.write(stationary_df)

# Display Alerts
st.subheader("🚨 Alerts")
alert_df = pd.DataFrame(alerts, columns=['Pallet_ID', 'Alert Type'])
st.write(alert_df)

# Map Visualization
st.subheader("📍 Pallet Locations")
map_center = [ongoing_trips['latitude'].mean(), ongoing_trips['longitude'].mean()]
pallet_map = folium.Map(location=map_center, zoom_start=6)

for _, row in stationary_df.iterrows():
    folium.Marker(
        location=[row['Last_Timestamp'], row['Hours_Stationary']],
        popup=f"Pallet ID: {row['Pallet_ID']}\nHours Stationary: {row['Hours_Stationary']}",
        icon=folium.Icon(color='red')
    ).add_to(pallet_map)

folium_static(pallet_map)

st.success("✅ Dashboard Loaded Successfully")
