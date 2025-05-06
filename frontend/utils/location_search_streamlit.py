# frontend/utils/location_assistance_streamlit.py

import streamlit as st
import requests
import re
from streamlit_folium import folium_static
import folium
from dotenv import load_dotenv
import os

# Load environment
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://fastapi_service:8000")

FACILITY_TYPES = [
    {"id": "hospital", "name": "Hospital"},
    {"id": "pharmacy", "name": "Pharmacy"},
    {"id": "mental_health_group", "name": "Mental Health Support Groups"}
]

def validate_zipcode(zipcode):
    return bool(re.match(r'^\d{5}(-\d{4})?$', zipcode))

def fetch_chronic_conditions():
    try:
        response = requests.get(f"{BACKEND_URL}/chronic-conditions")
        if response.status_code == 200:
            return ["Any"] + response.json()
        return ["Any"]
    except:
        return ["Any"]

def create_folium_map(facilities):
    if not facilities:
        return None

    center_lat, center_lng = 42.3601, -71.0589  # Default: Boston

    for f in facilities:
        if f.get("latitude") and f.get("longitude"):
            center_lat, center_lng = f["latitude"], f["longitude"]
            break

    m = folium.Map(location=[center_lat, center_lng], zoom_start=12, tiles="CartoDB positron")

    icon_map = {
        "hospital": ("plus-square", "fa", "red"),
        "pharmacy": ("pills", "fa", "green"),
        "mental_health_group": ("users", "fa", "purple"),
    }

    for idx, f in enumerate(facilities, 1):
        lat, lng = f.get("latitude"), f.get("longitude")
        if not lat or not lng:
            continue

        name = f.get("name", "Unnamed")
        address = f.get("address", "No address")
        rating = f.get("rating", "Not rated")
        maps_link = f.get("maps_link", "#")
        ftype = f.get("facility_type", "hospital").lower()

        icon, prefix, color = icon_map.get(ftype, icon_map["hospital"])
        tooltip = f"{idx}. {ftype.capitalize()}: {name}"

        popup_html = f"""
        <div style="width: 250px;">
            <h4>{name}</h4>
            <p><b>Address:</b> {address}</p>
            <p><b>Rating:</b> {rating}</p>
            <a href="{maps_link}" target="_blank">View on Google Maps</a>
        </div>
        """

        marker = folium.Marker(
            location=[lat, lng],
            tooltip=tooltip,
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(icon=icon, prefix=prefix, color=color)
        )
        marker.add_to(m)

    if len(facilities) > 1:
        coords = [[f["latitude"], f["longitude"]] for f in facilities if f.get("latitude") and f.get("longitude")]
        m.fit_bounds(coords)

    return m

def location_assistance_page():
    st.title("📍 Location-Based Healthcare Assistance")
    st.markdown("Find facilities near you for chronic condition support.")

    chronic_conditions = fetch_chronic_conditions()

    col1, col2 = st.columns(2)

    with col1:
        chronic_condition = st.selectbox("Select Chronic Condition", chronic_conditions)
        city = st.text_input("City (Required)")
    
    with col2:
        facility_type_name = st.selectbox("Facility Type", [ft["name"] for ft in FACILITY_TYPES])
        zipcode = st.text_input("Zipcode (Required)")

    facility_type_id = next((ft["id"] for ft in FACILITY_TYPES if ft["name"] == facility_type_name), "hospital")

    st.caption("* Required fields")

    if zipcode and not validate_zipcode(zipcode):
        st.error("❌ Invalid Zipcode Format")

    if st.button("🔍 Find Facilities"):
        if not city:
            st.error("Please enter a city name.")
        elif not zipcode:
            st.error("Please enter a zipcode.")
        elif not validate_zipcode(zipcode):
            st.error("Please enter a valid zipcode.")
        else:
            st.info("Searching for facilities...")

            query = f"Find {facility_type_name} facilities"
            if chronic_condition != "Any":
                query += f" for {chronic_condition}"
            query += f" in {city}"

            payload = {
                "query": query,
                "zipcode": zipcode,
                "chronic_condition": chronic_condition if chronic_condition != "Any" else "",
                "facility_type": facility_type_id,
                "additional_params": {}
            }

            try:
                response = requests.post(f"{BACKEND_URL}/search-facilities", json=payload)

                if response.status_code == 200:
                    data = response.json()
                    facilities = data.get("facilities", [])
                    messages = data.get("messages", [])

                    if facilities:
                        st.success(f"Found {len(facilities)} {facility_type_name.lower()} facilities in {city}")
                        tab1, tab2 = st.tabs(["🗺️ Map View", "📋 List View"])

                        with tab1:
                            fmap = create_folium_map(facilities)
                            if fmap:
                                folium_static(fmap, width=1200, height=500)
                            else:
                                st.warning("No coordinates found for map.")

                        with tab2:
                            for i, f in enumerate(facilities, 1):
                                st.markdown(f"### {i}. {f.get('name', 'Unnamed Facility')}")
                                st.markdown(f"**Address:** {f.get('address', 'N/A')}")
                                st.markdown(f"**Rating:** {f.get('rating', 'Not rated')}")
                                if f.get("maps_link"):
                                    st.markdown(f"[View on Google Maps]({f['maps_link']})")
                                st.markdown("---")

                    else:
                        st.warning("No matching facilities found.")
                        for msg in messages:
                            if msg.get("role") == "assistant":
                                st.info(msg.get("content"))

                else:
                    error = response.json().get("detail", "Server error")
                    st.error(f"API Error: {error}")
            except Exception as e:
                st.error(f"Connection error: {str(e)}")