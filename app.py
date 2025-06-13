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

import matplotlib.dates as mdates
import time

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
    m = folium.Map(location=[-33.5, 151.0], zoom_start=6)
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

    image_path = "Keeling_curve_2023.PNG"
    st.image(image_path, caption="Keeling curve 2023", use_container_width=True)

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
            if "Stockton" in os.path.basename(f):
                df = pd.read_csv(f, usecols=["Date Time"], dayfirst=True)
                df["datetime"] = pd.to_datetime(df["Date Time"], dayfirst=True, errors='coerce')
                df.rename(columns={
                    'CH4_Pic_0': 'CH4',
                    'CO2_Pic_0': 'CO2',
                    'N2O_Pic_0': 'N2O',
                    'NH3_Pic_0': 'NH3',
                    'H2O_Pic_0': 'H2O',
                    'WSP_0': 'Wind_Speed',
                    'WDR_0': 'Wind_Direction'
                }, inplace=True)
            else:
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


    df = pd.read_csv(monthly_file, dayfirst=True)
    #st.write("Original columns:", df.columns.tolist())  # Debug output

    # Detect and harmonize file format BEFORE column cleaning
    if "Date Time" in df.columns:
        # Stockton format
        df.rename(columns={
            'CH4_Pic_0': 'CH4',
            'CO2_Pic_0': 'CO2',
            'N2O_Pic_0': 'N2O',
            'NH3_Pic_0': 'NH3',
            'H2O_Pic_0': 'H2O',
            'WSP_0': 'Wind_Speed',
            'WDR_0': 'Wind_Direction'
        }, inplace=True)

        df["datetime"] = pd.to_datetime(df["Date Time"], dayfirst=True, errors='coerce')
        if df["datetime"].isnull().any():
            st.warning("Some datetime parsing errors detected in Stockton data.")

        # Set datetime index and resample to hourly mean
        df = df.dropna(subset=["datetime"])
        #df = df.set_index("datetime")
        #df = df.set_index("datetime", inplace=True)
        #df = df.resample('H').mean().reset_index()

    elif "DATE" in df.columns and "TIME" in df.columns:
        # Lidcombe format
        df["datetime"] = pd.to_datetime(df["DATE"] + " " + df["TIME"], dayfirst=True, errors='coerce')

    else:
        st.error("Unknown file format. Required columns not found.")
        st.stop()

    # Now clean column names
    df.columns = df.columns.str.replace(r"\s*\(.*\)", "", regex=True).str.strip()
    #st.write("Cleaned columns:", df.columns.tolist())  # Debug output

    # Set index and resample
    df.set_index("datetime", inplace=True)
    #df = df.resample("H").mean().reset_index()

    # Separate numeric and non-numeric columns
    numeric_df = df.select_dtypes(include=["number"])

    # Resample numeric columns only
    numeric_df = numeric_df.resample("H").mean()

    # Reset index to bring datetime back as a column
    numeric_df = numeric_df.reset_index()
    df = numeric_df

    # Process selected gas
    if selected_gas in df.columns:
        df[selected_gas] = pd.to_numeric(df[selected_gas], errors="coerce")
    else:
        st.error(f"Selected gas column '{selected_gas}' not found in file.")
        st.stop()

    # Filter by single day if required
    if view_mode == "Single Day":
        df = df[df["datetime"].dt.date == selected_date]

    # Rename columns to remove units and match expected gas names
    # Clean column names: remove units (if any)
    df.columns = df.columns.str.replace(r"\s*\(.*\)", "", regex=True).str.strip()

   
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
 
    # Check if selected gas exists
    if selected_gas not in df.columns:
        st.warning(f"{selected_gas} not found in the data.")
        st.stop()

    # Drop NA datetime or selected_gas
    df = df.dropna(subset=["datetime", selected_gas])
    df = df.sort_values("datetime")

    # Plotting
    st.title("GHG Analysis dashboard")

    if view_mode == "Single Day":
        st.subheader(f"{selected_gas} at {selected_site} on {selected_date.strftime('%Y-%m-%d')}")
    else:
        st.subheader(f"{selected_gas} at {selected_site} for {selected_date.strftime('%B %Y')}")

    import matplotlib.dates as mdates
    from windrose import WindroseAxes

    if selected_gas not in df.columns:
        st.warning(f"{selected_gas} not found in the data.")
        st.stop()

    #st.write("Available columns:", df.columns.tolist())
    st.write("Selected site value:", selected_site)

    st.sidebar.write(f"🔍 selected_site = {repr(selected_site)}")

    # --- Wind Rose ---
    #if selected_site == "Stockton"  and "Wind_Speed" in df.columns and "Wind_Direction" in df.columns:
    #    st.sidebar.title("Options")
    #    if st.sidebar.checkbox("Show Wind Rose"):
    #       st.markdown("### Wind Rose")
    #       wind_df = df.dropna(subset=["Wind_Speed", "Wind_Direction"])
    #       if not wind_df.empty:
    #           fig = plt.figure(figsize=(6, 6))
    #           ax = WindroseAxes.from_ax(fig=fig)
    #           ax.bar(
    #               wind_df["Wind_Direction"],
    #               wind_df["Wind_Speed"],
    #               normed=True,
    #               opening=0.8,
    #               edgecolor='white'
    #           )
    #           ax.set_legend()
    #           st.pyplot(fig)
    #    else:
    #        st.info("Wind data available to generate wind rose. Choose opion on the left sidebar")

    # --- Wind & Pollution Rose ---
    if selected_site == "Stockton" and "Wind_Speed" in df.columns and "Wind_Direction" in df.columns:
        st.info("Wind data available to generate wind and pollution rose. Choose options on the left sidebar")
        st.sidebar.title("Options")

        show_windrose = st.sidebar.checkbox("Show Wind Rose")
        show_pollution_rose = st.sidebar.checkbox("Show Pollution Rose")

        # Prepare wind data
        wind_df = df.dropna(subset=["Wind_Speed", "Wind_Direction"])

        if show_windrose:
            st.markdown("### Wind Rose")
            if not wind_df.empty and len(wind_df["Wind_Speed"]) > 0:
                fig = plt.figure(figsize=(6, 6))
                ax = WindroseAxes.from_ax(fig=fig)
                ax.bar(
                    wind_df["Wind_Direction"],
                    wind_df["Wind_Speed"],
                    normed=True,
                    opening=0.8,
                    edgecolor='white'
                    )
                ax.set_legend()
                st.pyplot(fig)
            else:
                st.warning("Not enough data for wind rose.")

        if show_pollution_rose:
            st.sidebar.markdown("### Pollution Rose Options")
    
            # 1. Pollutant selection
            available_pollutants = [col for col in ['CH4', 'CO2', 'N2O', 'NH3', 'H2O'] if col in df.columns]
            if not available_pollutants:
                st.warning("No pollutants available for plotting.")
            else:
                selected_pollutant = st.sidebar.selectbox("Select Pollutant", available_pollutants)
                agg_choice = st.sidebar.radio("Aggregate Data", ["Raw", "Daily Mean", "Monthly Mean"])

                # 2. Date and aggregation
                df["datetime"] = pd.to_datetime(df["datetime"])
                if agg_choice == "Daily Mean":
                    df = df.set_index("datetime").resample("D").mean().reset_index()
                elif agg_choice == "Monthly Mean":
                    df = df.set_index("datetime").resample("M").mean().reset_index()

                # 3. Filter out missing data

                pollution_df = df.dropna(subset=["Wind_Speed", "Wind_Direction", selected_pollutant])

                if pollution_df.empty:
                    st.warning("Not enough data for pollution rose.")
                else:
                    st.markdown(f"### Pollution Rose – {selected_pollutant} ({agg_choice})")

                    # Use filtered_df consistently
                    filtered_df = pollution_df.copy()

                    pollutant_values = filtered_df[selected_pollutant].values
                    min_val = np.nanmin(pollutant_values)
                    max_val = np.nanmax(pollutant_values)

                    # Compute bins safely
                    if min_val == max_val:
                        bins = [min_val - 0.1, min_val + 0.1]
                    else:
                        bins = np.linspace(min_val, max_val, 6)

                    #print("### Bin edges:", bins)
                    #print(filtered_df[selected_pollutant].describe())

                    # Check bin validity
                    if np.isnan(bins).any():
                        st.error("Bin computation failed due to NaNs.")
                    else:
                        # Create new bin labels **each time**
                        bin_labels = [
                            f"{round(bins[i], 1)}–{round(bins[i + 1], 1)}"
                            for i in range(len(bins) - 1)
                        ]
                        # Label pollutant bins
                        filtered_df["pollutant_bin_label"] = pd.cut(
                            filtered_df[selected_pollutant],
                            bins=bins,
                            labels=bin_labels,
                            include_lowest=True,
                            ordered=False  # Essential if there's any risk of duplicates
                        )

                        # Drop rows that failed to bin
                        filtered_df = filtered_df.dropna(subset=["pollutant_bin_label"])

                        import plotly.express as px

                        # Drop rows without valid bin labels
                        filtered_df = filtered_df.dropna(subset=["pollutant_bin_label"])

                        if filtered_df.empty:
                            st.warning("No data falls within pollutant bins.")
                        else:
                            # Bin wind direction to nearest 30 degrees
                            filtered_df["Wind_Direction_Binned"] = (filtered_df["Wind_Direction"] // 30) * 30

                            # Group data
                            grouped = (
                                filtered_df.groupby(["Wind_Direction_Binned", "pollutant_bin_label"])
                                .size()
                                .reset_index(name="Count")
                            )

                            # Create polar bar plot
                            fig = px.bar_polar(
                                grouped,
                                r="Count",
                                theta="Wind_Direction_Binned",
                                color="pollutant_bin_label",
                                color_discrete_sequence=px.colors.sequential.Plasma_r,
                                #title=f"Pollution Rose – {selected_pollutant} ({agg_choice})",
                                template="plotly_white",
                                height=600
                            )

                            fig.update_layout(
                                polar=dict(
                                    angularaxis=dict(
                                        direction="clockwise",
                                        tickmode="array",
                                        tickvals=list(range(0, 360, 30)),
                                        rotation=90,
                                        showline=True,
                                        linewidth=2,
                                        linecolor="black",
                                        gridcolor="gray"
                                    ),
                                    radialaxis=dict(
                                        showticklabels=True,
                                        ticks="outside",
                                        tickfont=dict(size=12),
                                        showline=True,
                                        linewidth=2,
                                        linecolor="black",
                                        gridcolor="gray",
                                        gridwidth=1.5
                                    )
                                ),
                                legend_title=selected_pollutant,
                                template="plotly_white"
                            )

                            st.plotly_chart(fig)

    # Plotting setup
    fig, ax = plt.subplots(figsize=(10, 4))

    if view_mode == "Full Month":
        df["date"] = df["datetime"].dt.date
        daily_avg = df.groupby("date")[selected_gas].mean().reset_index()

        if plot_mode in ["Line Only", "Combined"]:
            ax.plot(df["datetime"], df[selected_gas], marker="o", linestyle="-", label="Hourly")

        if plot_mode in ["Bar Only", "Combined"]:
            ax.bar(daily_avg["date"], daily_avg[selected_gas], width=0.6, alpha=0.3, label="Daily Avg")

        ax.set_title(f"{selected_gas} for {selected_date.strftime('%B %Y')}")

        ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))  # spacing ticks every 3 days
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))

    else:  # Single Day
        # Filter data to selected date only
        day_data = df[df["datetime"].dt.date == selected_date]
        if day_data.empty:
            st.warning("No data available for the selected day.")
            st.stop()

        if plot_mode in ["Line Only", "Combined"]:
            ax.plot(day_data["datetime"], day_data[selected_gas], marker="o", linestyle="-", label="Hourly")

        if plot_mode == "Bar Only":
            avg_val = day_data[selected_gas].mean()
            bar_time = datetime.combine(selected_date, datetime.min.time())
            ax.bar([bar_time], [avg_val], width=0.03, alpha=0.5, label="Daily Avg")

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

    # ------------------------
    # Sidebar: Parameter & Date Selection
    # ------------------------
    st.sidebar.markdown("### API Aquisnet Parameter & Date Selection")

    # Parameter and date selection
    parameter = st.sidebar.selectbox("Select Parameter", ["CH4", "CO2", "NH3", "N2O", "NO2", "NO"])
    start_date = st.sidebar.date_input("Start Date", datetime(2025, 1, 1))
    end_date = st.sidebar.date_input("End Date", datetime(2025, 1, 7))

    if start_date > end_date:
        st.sidebar.error("End Date must be after Start Date")
        st.stop()

    # API configuration
    API_URL = "https://data.airquality.nsw.gov.au/api/Data/get_Observations"
    HEADERS = {'Content-Type': 'application/json', 'accept': 'application/json'}

    # Helper function to check data existence
    def parameter_exists_api(site_id, parameter_id, start_date, end_date):
        payload = {
            #"Sites": [site_id],
            #"Parameters": [parameter_id],
            "Sites": site_id,    # should be inside [] but deliberately make it wrong to get default resutls
            "Parameters": parameter_id,    # should be inside [] but deliberately make it wrong to get default resutls
            "StartDate": start_date.strftime("%Y-%m-%d"),
            "EndDate": end_date.strftime("%Y-%m-%d"),
            "Categories": ["Averages"],
            "SubCategories": ["Hourly"],
            "Frequency": ["Hourly average"]
        }
        try:
            with st.spinner("Please wait, fetching sites... Once finished. site is available to select"):
                # Simulate a slow API call
                #time.sleep(5)  # Replace this with your real API request

                response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=20)
                if response.status_code == 200:
                    data = response.json()
                    return len(data) > 0
            st.success("Data loaded successfully!")

        except Exception as e:
            st.warning(f"API error for site ID {site_id}: {e}")
        return False

    # Load available sites and parameter IDs
    def load_sites_and_params():
        sites_url = "https://data.airquality.nsw.gov.au/api/Data/get_SiteDetails"
        params_url = "https://data.airquality.nsw.gov.au/api/Data/get_ParameterDetails"

        sites = requests.get(sites_url, headers=HEADERS).json()
        params = requests.get(params_url, headers=HEADERS).json()

        # Map: Site name -> Site ID
        site_map = {site["SiteName"]: site["Site_Id"] for site in sites}

        # Map: ParameterCode -> first valid ParameterId (prefer hourly average)
        param_map = {}
        for param in params:
            code = param.get("ParameterCode")
            freq = param.get("Frequency", "").lower()
            if code and code not in param_map:
                if "hour" in freq:  # prefer hourly
                    param_map[code] = param.get("ParameterCode")

        return site_map, param_map


    site_map, param_map = load_sites_and_params()

    # Get the parameter ID from name
    parameter_id = param_map.get(parameter)
    if parameter_id is None:
        st.error(f"Parameter '{parameter}' not found in API.")
        st.stop()

    # Check which sites have the parameter data
    available_sites = [
        site_name for site_name, site_id in site_map.items()
        if parameter_exists_api(site_id, parameter_id, start_date, end_date)
    ]

    if not available_sites:
        st.warning(f"No data found for {parameter} between {start_date} and {end_date} at any site.")
        st.stop()

    # Let user select from available sites
    selected_site = st.sidebar.selectbox("Select Site", available_sites)

    # Get the selected site ID
    selected_site_id = site_map[selected_site]

    #st.write(f"Sending Site_Id (type {type(selected_site_id)}): {selected_site_id}")

    # Prepare the API request payload with correct fields
    payload = {
        "Sites": [selected_site_id],
        "Parameters": [parameter_id],
        "StartDate": start_date.strftime("%Y-%m-%d"),
        "EndDate": end_date.strftime("%Y-%m-%d"),
        "Categories": ["Averages"],
        "SubCategories": ["Hourly"],
        "Frequency": ["Hourly average"]
    }

    #st.write(f"Selected site ID: {selected_site_id}, Parameter ID: {parameter_id}")
    #st.subheader("Payload sent to API:")
    #st.json(payload)

    # Fetch data from the API
    try:
        with st.spinner("Please wait, fetching data..."):
            # Simulate a slow API call
            #time.sleep(5)  # Replace this with your real API request

            response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
        st.success("Data loaded successfully!")
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        st.stop()

    records = []
    units = None  # store the units

    for rec in data:
        # Convert everything to correct type before comparison
        rec_site_id = int(rec.get("Site_Id", -1))
        rec_param_code = str(rec.get("Parameter", {}).get("ParameterCode", "")).upper()

        if rec_site_id == selected_site_id and rec_param_code == parameter_id.upper():
            date_str = rec["Date"]
            hour = rec["Hour"]
            dt = datetime.strptime(date_str, "%Y-%m-%d") + timedelta(hours=hour)
            value = rec["Value"]

            if value is not None:
                if units is None:
                    units = rec["Parameter"].get("Units", "")
                records.append({"datetime": dt, "value": value})

    #st.write(f"Total records returned by API: {len(data)}")
    st.write(f"selected_site_id: {selected_site_id} ({type(selected_site_id)})")
    st.write(f"parameter_id: {parameter_id} ({type(parameter_id)})")

    df = pd.DataFrame(records)

    #st.write("Preview of retrieved data:")
    #st.dataframe(df.head())

    # Assuming df contains 'datetime' and 'value' columns
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(df["datetime"], df["value"], marker="o", linestyle="-", label=parameter)

    # Set axis titles
    ax.set_title(f"{parameter} Time Series at {selected_site}", fontsize=14)
    ax.set_xlabel("Datetime")
    ax.set_ylabel(f"{parameter} ({units})")
    #ax.set_ylabel(f"{parameter} ({rec['Parameter']['Units']})")
    ax.grid(True)
    ax.legend()

    # Format x-axis to show hourly ticks or auto-adjust
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d\n%H:%M'))

    # Rotate x-tick labels for readability
    plt.xticks(rotation=45)

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Show in Streamlit
    st.pyplot(fig)


