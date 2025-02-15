import streamlit as st
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from geopy.distance import geodesic
import folium
from streamlit_folium import folium_static
from datetime import datetime, timedelta

# Load data with necessary preprocessing
@st.cache_data
def load_data():
    # Load datasets
    known_routes = pd.read_csv(r"final_known_route_repo.csv")
    ongoing_trips = pd.read_csv(r"final_on_going_trip_data.csv")

    # Combine Date and Time into a Timestamp column for known routes
    known_routes['Timestamp'] = pd.to_datetime(known_routes['Date'] + ' ' + known_routes['Time'])

    # Combine Date and Time into a Timestamp column for ongoing trips
    ongoing_trips['Timestamp'] = pd.to_datetime(ongoing_trips['Date'] + ' ' + ongoing_trips['Time'])

    # Drop old Date and Time columns
    known_routes.drop(columns=['Date', 'Time', 'Unnamed: 0'], errors='ignore', inplace=True)
    ongoing_trips.drop(columns=['Date', 'Time', 'Unnamed: 0'], errors='ignore', inplace=True)

    return known_routes, ongoing_trips

# Load the processed data
known_routes, ongoing_trips = load_data()

# Sidebar for user inputs
st.sidebar.title("PalletSense Dashboard")
st.sidebar.markdown("Configure the parameters below:")

# Clustering parameters
num_clusters = st.sidebar.slider('Number of clusters for KMeans', min_value=1, max_value=20, value=5)

# Deviation detection parameters
route_adherence_threshold = st.sidebar.slider('Route adherence threshold (meters)', min_value=500, max_value=5000, value=2000)
deviation_time_threshold = st.sidebar.slider('Deviation time threshold (hours)', min_value=1, max_value=24, value=6)

# Stationary detection parameters
stationary_distance_threshold = st.sidebar.slider('Stationary distance threshold (meters)', min_value=100, max_value=1000, value=500)
stationary_time_threshold = st.sidebar.slider('Stationary time threshold (hours)', min_value=24, max_value=168, value=48)

# Main title
st.title('PalletSense Tracking Dashboard')

# Function to calculate distance between two GPS coordinates
def haversine(coord1, coord2):
    return geodesic(coord1, coord2).meters

# A. Detecting Pallets Traveling Together
st.header('A. Detecting Pallets Traveling Together')

# Prepare data for clustering
coords = ongoing_trips[['latitude', 'longitude']].to_numpy()

# Perform KMeans clustering
kmeans = KMeans(n_clusters=num_clusters, random_state=42).fit(coords)
ongoing_trips['Cluster'] = kmeans.labels_

# Display clustering results
st.subheader('Clustering Results')
clustered_map = folium.Map(location=[ongoing_trips['latitude'].mean(), ongoing_trips['longitude'].mean()], zoom_start=5)
colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']

for cluster_id in ongoing_trips['Cluster'].unique():
    cluster_data = ongoing_trips[ongoing_trips['Cluster'] == cluster_id]
    for _, row in cluster_data.iterrows():
        folium.CircleMarker(
            location=(row['latitude'], row['longitude']),
            radius=5,
            color=colors[cluster_id % len(colors)] if cluster_id != -1 else 'black',
            fill=True,
            fill_color=colors[cluster_id % len(colors)] if cluster_id != -1 else 'black',
            fill_opacity=0.6,
            popup=f"Pallet ID: {row['Pallet_ID']}\nCluster: {cluster_id}"
        ).add_to(clustered_map)

folium_static(clustered_map)

# B. Route Adherence & Deviation Detection
st.header('B. Route Adherence & Deviation Detection')

# Function to find the nearest route point
def find_nearest_route_point(pallet_coord):
    distances = known_routes.apply(lambda row: haversine(pallet_coord, (row['latitude'], row['longitude'])), axis=1)
    min_distance = distances.min()
    nearest_route_point = known_routes.loc[distances.idxmin()]
    return min_distance, nearest_route_point

# Check route adherence and detect deviations
def check_route_adherence(trip_data):
    trip_data['Deviation'] = False
    trip_data['Deviation_Start'] = pd.NaT

    for idx, row in trip_data.iterrows():
        pallet_coord = (row['latitude'], row['longitude'])
        min_distance, _ = find_nearest_route_point(pallet_coord)

        if min_distance > route_adherence_threshold:
            if pd.isna(row['Deviation_Start']):
                trip_data.at[idx, 'Deviation_Start'] = row['Timestamp']
            else:
                deviation_duration = (row['Timestamp'] - row['Deviation_Start']).total_seconds() / 3600
                if deviation_duration >= deviation_time_threshold:
                    trip_data.at[idx, 'Deviation'] = True
        else:
            trip_data.at[idx, 'Deviation_Start'] = pd.NaT

    return trip_data

# Apply route adherence check
ongoing_trips = ongoing_trips.groupby('Pallet_ID').apply(check_route_adherence)

# Display deviations
st.subheader('Deviation Alerts')
deviations = ongoing_trips[ongoing_trips['Deviation'] == True]
if not deviations.empty:
    st.write(deviations[['Pallet_ID', 'Timestamp', 'latitude', 'longitude']])
else:
    st.write("No deviations detected.")

# C. Identifying Stationary Pallets
st.header('C. Identifying Stationary Pallets')

# Function to detect stationary pallets
def detect_stationary_pallets(trip_data):
    trip_data = trip_data.sort_values(by='Timestamp')
    trip_data['Stationary'] = False
    trip_data['Stationary_Start'] = pd.NaT

    for idx, row in trip_data.iterrows():
        if idx == 0:
            continue
        prev_row = trip_data.iloc[idx - 1]
        distance = haversine((row['latitude'], row['longitude']), (prev_row['latitude'], prev_row['longitude']))
        time_diff = (row['Timestamp'] - prev_row['Timestamp']).total_seconds() / 3600

        if distance <= stationary_distance_threshold and time_diff >= stationary_time_threshold:
            trip_data.at[idx, 'Stationary'] = True
            trip_data.at[idx, 'Stationary_Start'] = prev_row['Timestamp']
        else:
            trip_data.at[idx, 'Stationary_Start'] = pd.NaT

    return trip_data

# Apply stationary detection
ongoing_trips = ongoing_trips.groupby('Pallet_ID').apply(detect_stationary_pallets)

# Display stationary pallets
st.subheader('Stationary Pallet Alerts')
stationary_pallets = ongoing_trips[ongoing_trips['Stationary'] == True]
st.write(stationary_pallets[['Pallet_ID', 'Timestamp', 'latitude', 'longitude']])
