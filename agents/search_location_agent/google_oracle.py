# src/apis/google_oracle.py

import os
import requests
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

class GoogleOracle:
    """
    Oracle for retrieving healthcare facility information using Google Places API,
    including hospitals, clinics, pharmacies, and mental health support groups.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Google Oracle

        Args:
            api_key (Optional[str]): Google API key. Defaults to environment variable.
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API Key is required")

        self.text_search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        self.nearby_search_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        self.geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.place_details_url = "https://maps.googleapis.com/maps/api/place/details/json"

    def validate_location(self, city: str, zipcode: str) -> Dict[str, Any]:
        """
        Validate if the location exists and get detailed information
        """
        try:
            if not city:
                return {"valid": False, "message": "City name is required for location validation"}
            if not zipcode:
                return {"valid": False, "message": "Zipcode is required for location validation"}

            address = f"{city} {zipcode}, USA"
            params = {"address": address, "key": self.api_key}
            response = requests.get(self.geocode_url, params=params)
            data = response.json()

            logger.info(f"Geocode API response status: {data.get('status')}")

            if data.get("status") == "OK" and data.get("results"):
                result = data["results"][0]
                address_components = result.get("address_components", [])
                geometry = result.get("geometry", {})
                location = geometry.get("location", {})

                address_components_text = " ".join([comp.get("long_name", "") for comp in address_components]).lower()
                if city.lower() not in address_components_text or zipcode not in address_components_text:
                    return {
                        "valid": False,
                        "message": f"The provided city and zipcode do not match. Please check again.",
                        "status": "MISMATCH"
                    }

                return {
                    "valid": True,
                    "city": city,
                    "zipcode": zipcode,
                    "latitude": location.get("lat"),
                    "longitude": location.get("lng"),
                    "formatted_address": result.get("formatted_address", address)
                }
            else:
                return {
                    "valid": False,
                    "message": f"Invalid location. {data.get('error_message', 'Please check city and zipcode.')}",
                    "status": data.get("status")
                }

        except Exception as e:
            logger.error(f"Location validation error: {str(e)}")
            return {"valid": False, "message": f"Error validating location: {str(e)}"}

    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a place using its ID
        """
        try:
            params = {
                "place_id": place_id,
                "fields": "name,formatted_address,geometry,rating,user_ratings_total,website,formatted_phone_number,opening_hours",
                "key": self.api_key
            }
            response = requests.get(self.place_details_url, params=params)
            data = response.json()

            if data.get("status") == "OK" and data.get("result"):
                result = data["result"]
                location = result.get("geometry", {}).get("location", {})
                return {
                    "success": True,
                    "name": result.get("name", ""),
                    "address": result.get("formatted_address", ""),
                    "latitude": location.get("lat"),
                    "longitude": location.get("lng"),
                    "rating": result.get("rating"),
                    "total_ratings": result.get("user_ratings_total"),
                    "website": result.get("website", ""),
                    "phone": result.get("formatted_phone_number", ""),
                    "opening_hours": result.get("opening_hours", {}).get("weekday_text", [])
                }
            else:
                return {"success": False, "message": f"Failed to get place details: {data.get('status')}"}
        except Exception as e:
            logger.error(f"Error getting place details: {str(e)}")
            return {"success": False, "message": f"Error getting place details: {str(e)}"}

    def search_facilities(
        self,
        city: str,
        zipcode: str = "",
        facility_type: str = "hospital",
        chronic_condition: str = ""
    ) -> Dict[str, Any]:
        """
        Search for healthcare facilities in a specific location

        Args:
            city (str): City name (required)
            zipcode (str): Zip code (required)
            facility_type (str): Type of facility to search for.
                                 Supported: "hospital", "clinic", "pharmacy", "mental_health_group"
            chronic_condition (str): Chronic condition to enhance search (ignored for pharmacy)

        Returns:
            Dict with search results
        """
        try:
            if not city:
                return {"success": False, "message": "City name is required for the search", "facilities": []}
            if not zipcode:
                return {"success": False, "message": "Zipcode is required for the search", "facilities": []}

            location_validation = self.validate_location(city, zipcode)
            if not location_validation.get("valid"):
                return {"success": False, "message": location_validation.get("message", "Invalid location"), "facilities": []}

            latitude = location_validation.get("latitude")
            longitude = location_validation.get("longitude")
            facilities = []

            query_terms = {
                "hospital": ["hospitals", "medical centers"],
                "clinic": ["medical clinics", "healthcare clinics"],
                "pharmacy": ["pharmacies", "drugstores"],
                "mental_health_group": [
                    "mental health support groups", "mental health peer support",
                    "depression support groups", "anxiety support groups", "mental health community centers"
                ]
            }

            query_options = query_terms.get(facility_type, ["healthcare facilities"])
            location_str = location_validation.get("formatted_address") or f"{city} {zipcode}"

            for query_term in query_options:
                base_query = f"{query_term} in {location_str}"
                query = base_query

                # Do NOT append chronic condition for pharmacies
                if chronic_condition and facility_type not in ["pharmacy", "mental_health_group"]:
                    query = f"{chronic_condition} {base_query}"

                logger.info(f"Text search query: {query}")
                params = {"query": query, "key": self.api_key}
                response = requests.get(self.text_search_url, params=params)
                data = response.json()

                if data.get("status") == "OK" and data.get("results"):
                    for place in data.get("results", []):
                        place_location = place.get("geometry", {}).get("location", {})
                        facility = {
                            "name": place.get("name", "Unnamed Facility"),
                            "address": place.get("formatted_address", "No address"),
                            "rating": place.get("rating", "Not rated"),
                            "total_ratings": place.get("user_ratings_total", 0),
                            "place_id": place.get("place_id", ""),
                            "maps_link": f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id', '')}",
                            "latitude": place_location.get("lat"),
                            "longitude": place_location.get("lng")
                        }
                        if not any(f.get("place_id") == facility.get("place_id") for f in facilities):
                            facilities.append(facility)
                    if len(facilities) >= 3:
                        break

            if not facilities and latitude and longitude:
                logger.info(f"Text search found no results, trying nearby search at coordinates: {latitude}, {longitude}")
                type_mappings = {
                    "hospital": "hospital",
                    "clinic": "doctor",
                    "pharmacy": "pharmacy",
                    "mental_health_group": "health"
                }
                place_type = type_mappings.get(facility_type, "hospital")
                params = {
                    "location": f"{latitude},{longitude}",
                    "radius": "10000",
                    "type": place_type,
                    "key": self.api_key
                }
                response = requests.get(self.nearby_search_url, params=params)
                data = response.json()

                if data.get("status") == "OK":
                    for place in data.get("results", [])[:5]:
                        place_location = place.get("geometry", {}).get("location", {})
                        facility = {
                            "name": place.get("name", "Unnamed Facility"),
                            "address": place.get("vicinity", "No address"),
                            "rating": place.get("rating", "Not rated"),
                            "total_ratings": place.get("user_ratings_total", 0),
                            "place_id": place.get("place_id", ""),
                            "maps_link": f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id', '')}",
                            "latitude": place_location.get("lat"),
                            "longitude": place_location.get("lng")
                        }
                        facilities.append(facility)

            if facilities:
                return {
                    "success": True,
                    "facilities": facilities[:5],
                    "message": f"Found {len(facilities[:5])} healthcare facilities in {location_str}",
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"No healthcare facilities found in {location_str}",
                    "facilities": []
                }

        except Exception as e:
            logger.error(f"Facility search error: {str(e)}")
            return {"success": False, "message": f"Error searching facilities: {str(e)}", "facilities": []}

    def consult(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main consultation method for the Google Oracle.

        Args:
            query (Dict[str, Any]): Dictionary containing:
                - city: City name
                - zipcode: Zip code
                - facility_type: Facility category ("hospital", "clinic", "pharmacy", or "mental_health_group")
                - chronic_condition: Optional medical condition to improve relevance (ignored for pharmacies)

        Returns:
            Dict with consultation results and list of relevant healthcare facilities.
        """
        city = query.get("city", "")
        zipcode = query.get("zipcode", "")
        facility_type = query.get("facility_type", "hospital")
        chronic_condition = query.get("chronic_condition", "")

        logger.info(f"Oracle consultation: city={city}, zipcode={zipcode}, type={facility_type}, condition={chronic_condition}")

        if not city:
            return {"success": False, "message": "City name is required for the search", "facilities": []}
        if not zipcode:
            return {"success": False, "message": "Zipcode is required for the search", "facilities": []}

        return self.search_facilities(
            city=city,
            zipcode=zipcode,
            facility_type=facility_type,
            chronic_condition=chronic_condition
        )
