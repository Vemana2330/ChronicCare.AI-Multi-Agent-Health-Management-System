# src/agents/location_agent.py

import os
import sys
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class LocationAgent:
    """Agent for finding healthcare facilities based on location and chronic condition."""

    def __init__(self):
        """Initialize the location agent."""
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable not set")
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        logger.info("Location agent initialized successfully")

    def process_query(self, query: str, zipcode: str = "", chronic_condition: str = "",
                     facility_type: str = "hospital", additional_params: Dict = None) -> Dict[str, Any]:
        """
        Process a query to find healthcare facilities.

        Args:
            query: User query about healthcare facilities.
            zipcode: Zipcode to search in (now required).
            chronic_condition: Optional chronic condition to filter facilities.
                              (Note: ignored for pharmacy searches)
            facility_type: Type of facility to search for.
            additional_params: Optional additional parameters specific to facility type.

        Returns:
            Dict with search results.
        """
        try:
            from agents.search_location_agent.graph import run_location_agent

            if additional_params is None:
                additional_params = {}

            if not zipcode:
                return {
                    "success": False,
                    "message": "Zipcode is required for the search",
                    "facilities": [],
                    "messages": [
                        {"role": "user", "content": query},
                        {"role": "assistant", "content": "Please provide a zipcode for your search."}
                    ]
                }

            if zipcode and zipcode not in query:
                query = f"{query} in zipcode {zipcode}"

            if facility_type == "community_center":
                facility_type = "mental_health_group"

            # For pharmacy, skip chronic condition context
            if facility_type in ["pharmacy", "mental_health_group"]:
                chronic_condition = ""

            enhanced_query = self._enhance_query_with_params(query, facility_type, additional_params)

            logger.info(f"Processing query: {enhanced_query}, condition: {chronic_condition}")

            result = run_location_agent(enhanced_query, chronic_condition)

            facilities = result.get('facilities', [])
            for facility in facilities:
                facility["facility_type"] = facility_type

            if facilities:
                logger.info(f"Found {len(facilities)} facilities")
                return {
                    "success": True,
                    "message": f"Found {len(facilities)} healthcare facilities",
                    "facilities": facilities,
                    "location_details": result.get("location_details", {}),
                    "messages": result.get("messages", [])
                }
            else:
                logger.warning("No facilities found")
                return {
                    "success": False,
                    "message": "No healthcare facilities found matching your criteria",
                    "facilities": [],
                    "location_details": result.get("location_details", {}),
                    "messages": result.get("messages", [])
                }

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "success": False,
                "message": f"An error occurred: {str(e)}",
                "facilities": [],
                "messages": [
                    {"role": "user", "content": query},
                    {"role": "assistant", "content": f"Sorry, I encountered an error: {str(e)}"}
                ]
            }

    def _enhance_query_with_params(self, query: str, facility_type: str, additional_params: Dict) -> str:
        """
        Enhance the query with additional parameters based on facility type.

        Args:
            query: Original user query.
            facility_type: Type of facility being searched for.
            additional_params: Additional search parameters.

        Returns:
            Enhanced query string.
        """
        enhanced_query = query

        if not additional_params:
            return enhanced_query

        if facility_type == "hospital":
            if additional_params.get("emergency_services", False):
                enhanced_query += " with emergency services"

            specialties = additional_params.get("specialties", [])
            if specialties:
                enhanced_query += f" specializing in {', '.join(specialties)}"

            hospital_type = additional_params.get("hospital_type")
            if hospital_type and hospital_type != "Any":
                enhanced_query += f" {hospital_type.lower()} hospital"

        elif facility_type == "clinic":
            clinic_type = additional_params.get("clinic_type")
            if clinic_type and clinic_type != "Any":
                enhanced_query += f" {clinic_type.lower()}"

            if additional_params.get("telehealth", False):
                enhanced_query += " with telehealth services"

            wait_time = additional_params.get("wait_time")
            if wait_time and wait_time != "Any":
                enhanced_query += f" with {wait_time.lower()} wait times"

        elif facility_type == "pharmacy":
            hours = additional_params.get("hours")
            if hours and hours != "Any":
                if hours == "Open Now":
                    enhanced_query += " open now"
                else:
                    enhanced_query += f" with {hours.lower()}"

            services = additional_params.get("services", [])
            if services:
                enhanced_query += f" offering {', '.join(services)}"

            pharmacy_type = additional_params.get("pharmacy_type")
            if pharmacy_type and pharmacy_type != "Any":
                enhanced_query += f" {pharmacy_type.lower()} pharmacy"

        elif facility_type == "mental_health_group":
            format_type = additional_params.get("format")
            if format_type and format_type != "Any":
                enhanced_query += f" {format_type.lower()} format"

            facilitation = additional_params.get("facilitation")
            if facilitation and facilitation != "Any":
                enhanced_query += f" {facilitation.lower()} facilitation"

            meeting_frequency = additional_params.get("meeting_frequency")
            if meeting_frequency and meeting_frequency != "Any":
                enhanced_query += f" meeting {meeting_frequency.lower()}"

            focus_areas = additional_params.get("focus", [])
            if focus_areas:
                enhanced_query += f" focused on {', '.join(focus_areas)}"

        logger.info(f"Enhanced query: {enhanced_query}")
        return enhanced_query


def run_location_agent(query: str, zipcode: str = "", chronic_condition: str = "",
                      facility_type: str = "hospital", additional_params: Dict = None) -> Dict[str, Any]:
    """
    Run the location agent with the given query.

    Args:
        query: User query about healthcare facilities.
        zipcode: Zipcode to search in (now required).
        chronic_condition: Optional chronic condition to filter facilities.
        facility_type: Type of facility to search for.
        additional_params: Optional additional parameters specific to facility type.

    Returns:
        Dict with search results.
    """
    agent = LocationAgent()
    return agent.process_query(query, zipcode, chronic_condition, facility_type, additional_params)
