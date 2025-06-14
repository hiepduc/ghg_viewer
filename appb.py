import streamlit as st
import os
from datetime import datetime, timedelta
from PIL import Image
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components

from streamlit_folium import folium_static
import io
import tempfile
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import requests
import urllib.parse

# Define available sites and coordinates
sites = {
    "Lidcombe": [-33.865, 151.045],
    "Stockton": [-32.909, 151.784]
}


# Layout: create 2 columns (left narrow for map)
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("### NSW Piccarro Site Locations")

    # Create the Folium map
    m = folium.Map(location=[-33.5, 147.0], zoom_start=6)
    for name, coords in sites.items():
        folium.Marker(location=coords, popup=name).add_to(m)

    # Save to a temporary HTML file
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html') as f:
        m.save(f.name)
        map_html_path = f.name

    # Read and display map
    with open(map_html_path, 'r', encoding='utf-8') as f:
        map_html = f.read()

    components.html(map_html, height=400, width=250)

with col2:

    # -----------------------------
    # Configuration
    # -----------------------------
    DATA_DIR = "ghg_csv"  # folder with files like Lidcombe_YYYYMMDD.csv
    GASES = ["CH4", "CO2", "H2O", "N2O", "NH3"]
    SITES = ["Lidcombe", "Stockton"]

    # -----------------------------
    # Sidebar: Site & Gas Selection
    # -----------------------------
    st.sidebar.title("Greenhouse Gas Viewer")
    selected_site = st.sidebar.selectbox("Select Site", SITES)
    selected_gas = st.sidebar.selectbox("Select Gas", GASES)
    view_mode = st.sidebar.radio("View Mode", ["Single Day", "Full Month"])
    plot_mode = st.sidebar.radio("Plot Type", ["Line Only", "Bar Only", "Combined"])

    # -----------------------------
    # Find Available Dates
    # -----------------------------
    file_pattern = os.path.join(DATA_DIR, f"{selected_site}_*.csv")
    available_files = sorted(glob.glob(file_pattern))

    if not available_files:
        st.warning(f"No files found for site {selected_site} in {DATA_DIR}")
        st.stop()

    # Extract dates from filenames
    # available_dates = [datetime.strptime(os.path.basename(f).split("_")[1].split(".")[0], "%Y%m%d").date() for f in available_files]

    # Extract all available dates from the contents of all files
    available_dates = set()
    for f in available_files:
        try:
            df = pd.read_csv(f, usecols=["DATE", "TIME"])
            df["datetime"] = pd.to_datetime(df["DATE"] + " " + df["TIME"], dayfirst=True, errors='coerce')
            available_dates.update(df["datetime"].dt.date.dropna().unique())
        except Exception as e:
            st.warning(f"Failed to parse dates in {f}: {e}")

    available_dates = sorted(available_dates)

    # Sidebar: Date selector
    selected_date = st.sidebar.date_input(
        "Select Date",
        value=available_dates[-1],
        min_value=min(available_dates),
        max_value=max(available_dates),
    )

    # -----------------------------
    # Load and Display Data
    # -----------------------------
    date_str = selected_date.strftime("%Y%m%d")
    # Find the file that contains the month of selected_date
    selected_month = selected_date.strftime("%Y%m")
    monthly_file = None
    for f in available_files:
        if selected_month in os.path.basename(f):
            monthly_file = f
            break

    if not monthly_file:
        st.warning(f"No data found for {selected_date.strftime('%B %Y')}")
        st.stop()

    df = pd.read_csv(monthly_file)
    # Rename columns to remove units and match expected gas names
    df.columns = df.columns.str.replace(r"\s*\(.*\)", "", regex=True).str.strip()

    try:
        df["datetime"] = pd.to_datetime(df["DATE"] + " " + df["TIME"], dayfirst=True)
        df[selected_gas] = pd.to_numeric(df[selected_gas], errors="coerce")
    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.stop()

    if view_mode == "Single Day":
        df = df[df["datetime"].dt.date == selected_date]
   
    # Summary statistics
    if not df[selected_gas].isnull().all():
        mean_val = df[selected_gas].mean()
        min_val = df[selected_gas].min()
        max_val = df[selected_gas].max()

        st.markdown("### Summary Statistics")
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        col_stats1.metric("Mean", f"{mean_val:.2f}")
        col_stats2.metric("Min", f"{min_val:.2f}")
        col_stats3.metric("Max", f"{max_val:.2f}")
    else:
        st.info("No valid data to calculate statistics.")
 
    # Plotting
    st.title("GHG Time Series Viewer")

    if view_mode == "Single Day":
        st.subheader(f"{selected_gas} at {selected_site} on {selected_date.strftime('%Y-%m-%d')}")
    else:
        st.subheader(f"{selected_gas} at {selected_site} for {selected_date.strftime('%B %Y')}")

    import matplotlib.dates as mdates

    if selected_gas not in df.columns:
        st.warning(f"{selected_gas} not found in the data.")
        st.stop()
    # Plot configuration
    fig, ax = plt.subplots(figsize=(10, 4))

    # Prepare daily average if needed
    if view_mode == "Full Month":
        df["date"] = df["datetime"].dt.date
        daily_avg = df.groupby("date")[selected_gas].mean().reset_index()

        if plot_mode in ["Line Only", "Combined"]:
            ax.plot(df["datetime"], df[selected_gas], marker="o", linestyle="-", label="Hourly")

        if plot_mode in ["Bar Only", "Combined"]:
            ax.bar(daily_avg["date"], daily_avg[selected_gas], width=0.6, alpha=0.3, label="Daily Avg")

        ax.set_title(f"{selected_gas} for {selected_date.strftime('%B %Y')}")
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))

    else:  # Single Day
        if plot_mode in ["Line Only", "Combined"]:
            ax.plot(df["datetime"], df[selected_gas], marker="o", linestyle="-", label="Hourly")

        if plot_mode == "Bar Only":
            day_avg = df[selected_gas].mean()
            bar_time = datetime.combine(selected_date, datetime.min.time())  # Convert date to datetime
            ax.bar([bar_time], [day_avg], width=0.03, alpha=0.5, label="Daily Avg")

        ax.set_title(f"{selected_gas} on {selected_date.strftime('%Y-%m-%d')}")
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    # Labels and formatting
    ax.set_xlabel("Time")
    #ax.set_ylabel(f"{selected_gas} concentration")
    # Define gas units
    GAS_UNITS = {
        "CH4": "ppm",
        "CO2": "ppm",
        "N2O": "ppm",
        "NH3": "ppb",
        "H2O": "%",
    }

    unit = GAS_UNITS.get(selected_gas, "")
    ax.set_ylabel(f"{selected_gas} ({unit})")

    ax.grid(True)
    ax.legend()
    fig.autofmt_xdate(rotation=30)
    fig.autofmt_xdate()

    # Show plot
    st.pyplot(fig)

    # Export plot
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight')
    st.download_button("Download Plot as PNG", buf.getvalue(), file_name=f"{selected_site}_{selected_gas}_{selected_date.strftime('%Y%m%d')}.png", mime="image/png")

    # CSV downloads
    st.download_button("Download Full CSV", data=df.to_csv(index=False), file_name=os.path.basename(monthly_file))

    if view_mode == "Full Month":
        daily_avg_csv = daily_avg.rename(columns={selected_gas: f"{selected_gas}_daily_avg"})
        st.download_button("Download Daily Averages", data=daily_avg_csv.to_csv(index=False), file_name=f"{selected_site}_{selected_gas}_daily_avg_{selected_month}.csv")

    # Sidebar additions
    st.sidebar.markdown("### Parameter & Date Selection")

    parameter = st.sidebar.selectbox("Select Parameter", ["CH4", "CO2", "NH3", "N2O", "NO2"])
    start_date = st.sidebar.date_input("Start Date", datetime(2025, 1, 1))
    end_date = st.sidebar.date_input("End Date", datetime(2025, 3, 31))

    # Ensure valid date range
    if start_date > end_date:
        st.sidebar.error("End Date must be after Start Date")

    API_URL = "https://data.airquality.nsw.gov.au/api/Data/get_ConcentrationData"
    HEADERS = {'Content-Type': 'application/json', 'accept': 'application/json'}

    def parameter_exists_api(site_id, parameter_id, start_date, end_date):
        payload = {
            "SiteId": site_id,
            "ParameterId": parameter_id,
            "FromDate": start_date.strftime("%Y-%m-%d"),
            "ToDate": end_date.strftime("%Y-%m-%d")
        }
        try:
            response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return len(data) > 0  # Data exists
        except Exception as e:
            st.warning(f"API error for site {site_id}: {e}")
        return False

    def load_sites_and_params():
        sites_url = "https://data.airquality.nsw.gov.au/api/Data/get_SiteDetails"
        params_url = "https://data.airquality.nsw.gov.au/api/Data/get_ParameterDetails"

        sites = requests.get(sites_url, headers=HEADERS).json()
        params = requests.get(params_url, headers=HEADERS).json()

        site_map = {site["SiteName"]: site["Site_Id"] for site in sites}
        param_map = {param["ParameterName"]: param["ParameterId"] for param in params}
        return site_map, param_map

    site_map, param_map = load_sites_and_params()

    st.sidebar.markdown("### Parameter & Date Selection")

    parameter = st.sidebar.selectbox("Select Parameter", ["CH4", "CO2", "NH3", "N2O"])
    start_date = st.sidebar.date_input("Start Date", datetime(2025, 1, 1))
    end_date = st.sidebar.date_input("End Date", datetime(2025, 3, 31))

    if start_date > end_date:
        st.sidebar.error("End Date must be after Start Date")

    parameter_id = param_map.get(parameter)
    if parameter_id is None:
        st.error(f"Parameter '{parameter}' not found in API")
        st.stop()

    available_sites = []
    for site_name, site_id in site_map.items():
        if parameter_exists_api(site_id, parameter_id, start_date, end_date):
            available_sites.append(site_name)

    if not available_sites:
        st.warning("No available sites with data for the selected parameter and date range.")
        st.stop()

    selected_site = st.sidebar.selectbox("Select Site", available_sites)

