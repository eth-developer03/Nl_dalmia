import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Page Title
st.title("📦 Pallet Route Adherence Analysis")

# Load dataset with error handling
file_path = "filtered_ongoing_trip_data.csv"

@st.cache_data
def load_data():
    if not os.path.exists(file_path):
        st.error("❌ Error: The dataset file is missing! Please upload 'filtered_ongoing_trip_data.csv'.")
        return None
    df = pd.read_csv(file_path)
    return df

df = load_data()

if df is not None and not df.empty:  # Proceed only if the file is loaded successfully
    # Convert Pallet_ID to string to avoid sorting issues
    df["Pallet_ID"] = df["Pallet_ID"].astype(str)

    # Sidebar - User-defined threshold
    st.sidebar.header("⚙️ Settings")
    max_threshold = round(df["min_distance_km"].max(), 1) if not df.empty else 10.0
    threshold = st.sidebar.slider("Set Route Adherence Threshold (km)", min_value=0.0, max_value=max_threshold, value=2.0, step=0.1)

    # ✅ Update adherence classification BEFORE showing preview
    df["route_adherence"] = df["min_distance_km"] <= threshold

    # ✅ Dataset Preview (Show after updating adherence column)
    st.subheader("📋 Dataset Preview")
    st.dataframe(df[["Pallet_ID", "latitude", "longitude", "min_distance_km", "route_adherence"]].head(10))  # 🔥 Display as interactive table

    # Visualization: Pallet ID vs Minimum Distance
    st.subheader("📊 Pallet Distance to Route (Adherence)")

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.scatterplot(
        data=df,
        x="Pallet_ID",
        y="min_distance_km",
        hue="route_adherence",
        palette="coolwarm",  # Dynamic color scaling
        alpha=0.7,
        ax=ax
    )

    # Fix X-axis ticks
    ax.axhline(threshold, color='blue', linestyle='--', label=f'Threshold: {threshold} km')
    ax.set_xlabel("Pallet ID")
    ax.set_ylabel("Minimum Distance to Route (km)")
    ax.set_title("📍 Route Adherence Based on Distance")

    # 🔥 Rotate X-axis labels
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")

    # 🔥 Show only every N-th label (avoid clutter)
    total_pallets = len(df["Pallet_ID"].unique())
    step = max(total_pallets // 20, 1)  # Show 1 label per 20 Pallet IDs (adjustable)
    ax.set_xticks(ax.get_xticks()[::step])

    ax.legend()
    st.pyplot(fig)

    # Adherence Statistics
    st.subheader("📈 Adherence Statistics")

    adherence_counts = df["route_adherence"].value_counts()
    adherence_percentages = adherence_counts / adherence_counts.sum() * 100

    stats_df = pd.DataFrame({
        "Adherence": ["Within Threshold", "Outside Threshold"],
        "Count": adherence_counts.values,
        "Percentage": adherence_percentages.values.round(2)
    })

    st.write(stats_df)

    # Allow users to download the filtered dataset
    st.subheader("💾 Download Filtered Data")
    st.download_button(
        label="📥 Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_ongoing_trip_data.csv",
        mime="text/csv"
    )

############
###

# import streamlit as st
# import pandas as pd
# import matplotlib.pyplot as plt
# import seaborn as sns
# import os

# # Page Title
# st.title("📦 Pallet Route Adherence Analysis")

# # Load dataset with error handling
# file_path = "filtered_ongoing_trip_data.csv"

# @st.cache_data
# def load_data():
#     if not os.path.exists(file_path):
#         st.error("❌ Error: The dataset file is missing! Please upload 'filtered_ongoing_trip_data.csv'.")
#         return None
#     df = pd.read_csv(file_path)
#     return df

# df = load_data()

# if df is not None:  # Proceed only if the file is loaded successfully

#     # Convert Pallet_ID to string to avoid sorting issues
#     df["Pallet_ID"] = df["Pallet_ID"].astype(str)

#     # Sidebar - User-defined threshold
#     st.sidebar.header("⚙️ Settings")
#     max_threshold = round(df["min_distance_km"].max(), 1) if not df.empty else 10.0
#     threshold = st.sidebar.slider("Set Route Adherence Threshold (km)", min_value=0.0, max_value=max_threshold, value=2.0, step=0.1)

#     # Compute adherence based on the chosen threshold
#     df["route_adherence"] = df["min_distance_km"] <= threshold

#     # Dataset Preview
#     st.subheader("📋 Dataset Preview")
#     st.write(df.head())

#     # Visualization: Pallet ID vs Minimum Distance
#     st.subheader("📊 Pallet Distance to Route (Adherence)")

#     fig, ax = plt.subplots(figsize=(12, 6))
#     sns.scatterplot(
#         data=df,
#         x="Pallet_ID",
#         y="min_distance_km",
#         hue="route_adherence",
#         palette="coolwarm",  # Dynamic color scaling
#         alpha=0.7,
#         ax=ax
#     )

#     # Fix X-axis ticks
#     ax.axhline(threshold, color='blue', linestyle='--', label=f'Threshold: {threshold} km')
#     ax.set_xlabel("Pallet ID")
#     ax.set_ylabel("Minimum Distance to Route (km)")
#     ax.set_title("📍 Route Adherence Based on Distance")

#     # 🔥 Rotate X-axis labels
#     ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")

#     # 🔥 Show only every N-th label (avoid clutter)
#     total_pallets = len(df["Pallet_ID"].unique())
#     step = max(total_pallets // 20, 1)  # Show 1 label per 20 Pallet IDs (adjustable)
#     ax.set_xticks(ax.get_xticks()[::step])

#     ax.legend()
#     st.pyplot(fig)

#     # Adherence Statistics
#     st.subheader("📈 Adherence Statistics")

#     adherence_counts = df["route_adherence"].value_counts()
#     adherence_percentages = adherence_counts / adherence_counts.sum() * 100

#     stats_df = pd.DataFrame({
#         "Adherence": ["Within Threshold", "Outside Threshold"],
#         "Count": adherence_counts.values,
#         "Percentage": adherence_percentages.values.round(2)
#     })

#     st.write(stats_df)

#     # Allow users to download the filtered dataset
#     st.subheader("💾 Download Filtered Data")
#     st.download_button(
#         label="📥 Download CSV",
#         data=df.to_csv(index=False).encode("utf-8"),
#         file_name="filtered_ongoing_trip_data.csv",
#         mime="text/csv"
#     )
