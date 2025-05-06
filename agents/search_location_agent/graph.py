# src/orchestration/graph.py
 
import os
from typing import Dict, Any, List, Annotated, TypedDict, Literal
from dotenv import load_dotenv
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
import json
import logging
 
# Configure logging
logger = logging.getLogger(__name__)
 
# Load environment variables
load_dotenv()
 
# Type definitions for our state
class LocationAgentState(TypedDict):
    """Type definition for the agent state."""
    query: str
    chronic_condition: str
    location_details: Dict[str, Any]
    search_results: Dict[str, Any]
    messages: List[Dict[str, str]]
    next_step: str
 
# Define node functions (each will be a step in our graph)
def extract_location_information(state: LocationAgentState) -> LocationAgentState:
    """Extract location information from the user query."""
    query = state["query"]
    chronic_condition = state.get("chronic_condition", "")
   
    logger.info(f"Extracting location info from query: {query}")
   
    # Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )
   
    # Create a prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a healthcare facility location assistant.
        Extract location details from the user's query about healthcare facilities.
       
        Extract the following information:
        - city: The name of the city mentioned
        - zipcode: The zipcode/postal code if mentioned (IMPORTANT: extract this if present)
        - facility_type: Type of healthcare facility (hospital, clinic, pharmacy, mental_health_group)
        - chronic_condition: Any chronic condition mentioned
       
        If a piece of information is not mentioned, leave it as an empty string.
        The zipcode is a critical piece of information for precise location search.
        """),
        ("user", "{query}")
    ])
   
    # Define the output structure
    function_def = {
        "name": "extract_location_info",
        "description": "Extract location information from the user query",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
                "zipcode": {"type": "string", "description": "ZIP code/postal code"},
                "facility_type": {"type": "string", "description": "Type of healthcare facility"},
                "chronic_condition": {"type": "string", "description": "Chronic condition mentioned"}
            },
            "required": ["city", "facility_type"]
        }
    }
   
    # Create the chain
    chain = prompt | llm.bind_functions(functions=[function_def]) | JsonOutputFunctionsParser()
   
    try:
        # Run the chain
        result = chain.invoke({"query": query})
       
        # Use chronic condition from state if not found in query
        if not result.get("chronic_condition") and chronic_condition:
            result["chronic_condition"] = chronic_condition
       
        # Ensure all fields exist
        result.setdefault("city", "")
        result.setdefault("zipcode", "")
        result.setdefault("facility_type", "hospital")
        result.setdefault("chronic_condition", "")
       
        # Create a message about the extracted information
        if result["zipcode"]:
            location_summary = f"{result['city']} {result['zipcode']}"
        else:
            location_summary = result['city']
           
        summary = f"Extracted location details: {location_summary}, " \
                f"Facility type: {result['facility_type']}, Condition: {result['chronic_condition']}"
       
        logger.info(f"Extracted location information: {result}")
       
        # Update the state
        new_messages = state["messages"] + [{"role": "assistant", "content": summary}]
       
        return {
            **state,
            "location_details": result,
            "messages": new_messages,
            "next_step": "search_facilities"
        }
   
    except Exception as e:
        logger.error(f"Error extracting location information: {str(e)}")
        error_message = "I couldn't extract the location information from your query. Please provide a city name and facility type."
        new_messages = state["messages"] + [{"role": "assistant", "content": error_message}]
       
        return {
            **state,
            "location_details": {
                "city": "",
                "zipcode": "",
                "facility_type": "hospital",
                "chronic_condition": state.get("chronic_condition", "")
            },
            "messages": new_messages,
            "next_step": END
        }
 
def search_healthcare_facilities(state: LocationAgentState) -> LocationAgentState:
    """
    Search for healthcare facilities based on the extracted information.

    - For 'pharmacy', the chronic condition is ignored (general results are returned).
    """
    try:
        from agents.search_location_agent.google_oracle import GoogleOracle

        location_details = state["location_details"]
        city = location_details.get("city", "")
        zipcode = location_details.get("zipcode", "")
        facility_type = location_details.get("facility_type", "hospital")
        chronic_condition = location_details.get("chronic_condition", "")

        if not city:
            error_message = "I need a city name to search for healthcare facilities. Please specify a city."
            new_messages = state["messages"] + [{"role": "assistant", "content": error_message}]
            return {
                **state,
                "search_results": {
                    "success": False,
                    "message": "City name is required",
                    "facilities": []
                },
                "messages": new_messages,
                "next_step": END
            }

        if not zipcode:
            error_message = "I need a zipcode to search for healthcare facilities. Please specify a zipcode."
            new_messages = state["messages"] + [{"role": "assistant", "content": error_message}]
            return {
                **state,
                "search_results": {
                    "success": False,
                    "message": "Zipcode is required",
                    "facilities": []
                },
                "messages": new_messages,
                "next_step": END
            }

        logger.info(f"Searching facilities in {city} {zipcode}, type: {facility_type}, condition: {chronic_condition}")

        # Initialize the oracle
        oracle = GoogleOracle()

        # Omit chronic condition for pharmacy searches
        condition_to_use = "" if facility_type in ["pharmacy", "mental_health_group"] else chronic_condition

        search_results = oracle.consult({
            "city": city,
            "zipcode": zipcode,
            "facility_type": facility_type,
            "chronic_condition": condition_to_use
        })

        if search_results.get("success"):
            facilities = search_results.get("facilities", [])
            message = f"Found {len(facilities)} healthcare facilities in {city} {zipcode}."
        else:
            message = f"Sorry, {search_results.get('message', 'no facilities found')}."

        logger.info(f"Search results: {message}")
        new_messages = state["messages"] + [{"role": "assistant", "content": message}]

        return {
            **state,
            "search_results": search_results,
            "messages": new_messages,
            "next_step": "format_results"
        }

    except Exception as e:
        logger.error(f"Error searching healthcare facilities: {str(e)}")
        error_message = f"I encountered an error while searching for healthcare facilities: {str(e)}"
        new_messages = state["messages"] + [{"role": "assistant", "content": error_message}]
        return {
            **state,
            "search_results": {
                "success": False,
                "message": f"Error: {str(e)}",
                "facilities": []
            },
            "messages": new_messages,
            "next_step": END
        }

 
def format_search_results(state: LocationAgentState) -> LocationAgentState:
    """Format the search results for presentation based on facility type."""
    try:
        search_results = state["search_results"]
        location_details = state["location_details"]
        facility_type = location_details.get("facility_type", "hospital").lower()
        chronic_condition = location_details.get("chronic_condition", "")
       
        # Check if we have results to format
        if search_results.get("success"):
            facilities = search_results.get("facilities", [])
           
            # Use different approaches for different facility types
            if facility_type == "hospital":
                # Format hospital results without using LLM
                content = format_hospital_results(facilities, chronic_condition, location_details.get("city", ""))
            elif facility_type == "clinic":
                # Format clinic results without using LLM
                content = format_clinic_results(facilities, chronic_condition, location_details.get("city", ""))
            elif facility_type == "pharmacy":
                # Format pharmacy results without using LLM
                content = format_pharmacy_results(facilities, chronic_condition, location_details.get("city", ""))
            elif facility_type == "mental_health_group" or facility_type == "community_center":
                # Format support group and community center results the same way
                content = format_support_group_results(facilities, chronic_condition, location_details.get("city", ""))
            else:
                # Generic format for other types
                content = format_generic_results(facilities, facility_type, chronic_condition, location_details.get("city", ""))
           
            # Update the state with the formatted content
            new_messages = state["messages"] + [{"role": "assistant", "content": content}]
           
        else:
            # No results found message
            no_results_content = format_no_results(facility_type, chronic_condition, location_details.get("city", ""))
            new_messages = state["messages"] + [{"role": "assistant", "content": no_results_content}]
       
        return {
            **state,
            "messages": new_messages,
            "next_step": END
        }
   
    except Exception as e:
        logger.error(f"Error formatting search results: {str(e)}")
       
        # Provide a more detailed error message for debugging
        error_detail = f": {str(e)}" if str(e) else ""
        error_message = f"I encountered an error while formatting the search results{error_detail}."
       
        new_messages = state["messages"] + [{"role": "assistant", "content": error_message}]
       
        return {
            **state,
            "messages": new_messages,
            "next_step": END
        }
 
def format_hospital_results(facilities, chronic_condition, city):
    """Format hospital results with a clinical, professional style."""
    condition_text = chronic_condition if chronic_condition else "general healthcare needs"
   
    # Create the content with a medical/clinical tone
    content = f"# MEDICAL CENTER EVALUATION REPORT\n\n"
    content += f"## HOSPITAL RESOURCES FOR {condition_text.upper()}\n\n"
    content += f"### CLINICAL ASSESSMENT\n\n"
    content += f"The following medical centers in {city} may provide appropriate care for patients with {condition_text}. "
    content += f"These facilities typically offer comprehensive medical services including emergency care, specialist consultations, diagnostic capabilities, and inpatient treatment options when necessary.\n\n"
   
    content += f"### FACILITY ANALYSIS\n\n"
   
    for i, facility in enumerate(facilities, 1):
        name = facility.get("name", "Unnamed Facility")
        address = facility.get("address", "No address available")
        rating = facility.get("rating", "Not rated")
        maps_link = facility.get("maps_link", "#")
       
        content += f"#### {i}. {name}\n"
        content += f"**LOCATION:** {address}\n\n"
       
        if rating != "Not rated":
            content += f"**PATIENT SATISFACTION METRICS:** {rating}/5 ({facility.get('total_ratings', 0)} assessments)\n\n"
        else:
            content += f"**PATIENT SATISFACTION METRICS:** Insufficient data available\n\n"
       
        content += f"**POTENTIAL CLINICAL SERVICES:** May include specialized care for {condition_text}, diagnostic evaluation, treatment planning, and ongoing management.\n\n"
        content += f"**FACILITY ACCESS:** [View location on medical referral map]({maps_link})\n\n"
   
    content += f"### CLINICAL RECOMMENDATIONS\n\n"
    content += f"* Consult with primary care physician for appropriate referrals to specialists at these facilities\n"
    content += f"* Verify insurance acceptance and network status prior to scheduling appointments\n"
    content += f"* Request complete medical records transfer to ensure continuity of care\n"
    content += f"* Inquire about clinical trials or specialized treatment protocols for {condition_text} if applicable\n\n"
   
    content += f"*This assessment is based on facility data and does not constitute a complete evaluation of medical services.*"
   
    return content
 
def format_clinic_results(facilities, chronic_condition, city):
    """Format clinic results with a warm, conversational style."""
    condition_text = chronic_condition if chronic_condition else "general healthcare needs"
   
    # Create the content with a warm, conversational tone
    content = f"# Your Neighborhood Clinic Guide\n\n"
    content += f"## Finding Care Partners for {condition_text}\n\n"
    content += f"### Hello Friend!\n\n"
    content += f"We've found some wonderful clinics in {city} that can help you manage {condition_text}. "
    content += f"These welcoming care centers focus on building ongoing relationships with patients through regular check-ups, personalized treatment plans, and supportive care from dedicated healthcare teams.\n\n"
   
    content += f"### Your Local Care Options\n\n"
   
    for i, facility in enumerate(facilities, 1):
        name = facility.get("name", "Unnamed Facility")
        address = facility.get("address", "No address available")
        rating = facility.get("rating", "Not rated")
        maps_link = facility.get("maps_link", "#")
       
        content += f"#### {i}. {name} - Your Potential Medical Home\n"
        content += f"**Where to Find Them:** {address}\n\n"
       
        if rating != "Not rated":
            content += f"**What Patients Say:** {rating}/5 stars from {facility.get('total_ratings', 0)} patients\n\n"
        else:
            content += f"**What Patients Say:** No ratings available yet\n\n"
       
        content += f"**How They Can Help:** Your care team here can offer regular check-ins, monitoring, and personalized care plans for managing {condition_text} with a focus on your overall wellbeing.\n\n"
        content += f"**Getting Started:** [Get directions to begin your care journey]({maps_link})\n\n"
   
    content += f"### Helpful Tips From Our Care Team\n\n"
    content += f"* Call ahead to schedule your first appointment and ask about wait times\n"
    content += f"* Bring a list of your current medications and questions to discuss\n"
    content += f"* Consider what you hope to achieve with your healthcare partner\n"
    content += f"* Remember, finding the right care team might take a couple of visits\n\n"
   
    content += f"*We're here to partner with you on your healthcare journey!*"
   
    return content
 
def format_pharmacy_results(facilities, chronic_condition, city):
    """Format pharmacy results with a practical, informative style."""
    condition_text = chronic_condition if chronic_condition else "general healthcare needs"
   
    # Create the content with a practical, informative tone
    content = f"# Medication & Pharmacy Services Guide\n\n"
    content += f"## Local Prescription Resources for {condition_text}\n\n"
    content += f"### Pharmacy Services Overview\n\n"
    content += f"The following pharmacies in {city} can support your medication needs for {condition_text}. "
    content += f"Beyond simply filling prescriptions, these locations may offer medication therapy management, consultation with pharmacists, automated refill programs, and health screenings.\n\n"
   
    content += f"### Available Pharmacy Resources\n\n"
   
    for i, facility in enumerate(facilities, 1):
        name = facility.get("name", "Unnamed Facility")
        address = facility.get("address", "No address available")
        rating = facility.get("rating", "Not rated")
        maps_link = facility.get("maps_link", "#")
       
        content += f"#### {i}. {name}\n"
        content += f"**Location:** {address}\n\n"
       
        if rating != "Not rated":
            content += f"**Customer Feedback:** {rating}/5 ({facility.get('total_ratings', 0)} reviews)\n\n"
        else:
            content += f"**Customer Feedback:** No ratings available\n\n"
       
        content += f"**Potential Services:** Prescription filling, refill management, medication counseling, and possible medication therapy management for {condition_text}.\n\n"
        content += f"**Access Information:** [View pharmacy location]({maps_link})\n\n"
   
    content += f"### Effective Medication Management\n\n"
    content += f"* Bring a complete list of all medications when consulting with your pharmacist\n"
    content += f"* Ask about medication therapy management programs specific to {condition_text}\n"
    content += f"* Inquire about automatic refill programs to ensure consistent medication availability\n"
    content += f"* Consider using a single pharmacy for all prescriptions to better monitor potential interactions\n\n"
   
    content += f"*Remember to bring your current medication list to every pharmacy visit.*"
   
    return content
 
def format_support_group_results(facilities, chronic_condition, city):
    """Format support group results with a completely different style from hospitals."""
    condition_text = chronic_condition if chronic_condition else "general healthcare needs"
   
    # Create the content with a completely different format and style from hospital
    content = f"#  Support Community Directory\n\n"
    content += f"## Peer Support Resources for {condition_text}\n\n"
   
    # Add colorful emoji section headers
    content += f"###  The Healing Power of Connection\n\n"
    content += f"Living with {condition_text} is a journey that's easier when you don't walk it alone. "
    content += f"The support communities below in {city} offer spaces where you can connect with others who truly understand what you're experiencing. "
    content += f"These groups provide emotional support, practical wisdom, and the comfort of knowing you're not alone.\n\n"
   
    # Add visually distinct section
    content += f"### Support Communities Near You\n\n"
   
    for i, facility in enumerate(facilities, 1):
        name = facility.get("name", "Unnamed Facility")
        address = facility.get("address", "No address available")
        rating = facility.get("rating", "Not rated")
        maps_link = facility.get("maps_link", "#")
       
        # Use emojis and casual formatting
        content += f"#### {i}. {name} ✨\n"
        content += f"**Where We Meet:** {address}\n\n"
       
        if rating != "Not rated":
            content += f"**Group Vibe:** {rating}/5 stars (from {facility.get('total_ratings', 0)} members)\n\n"
        else:
            content += f"**Group Vibe:** No ratings yet - be the first to share your experience!\n\n"
       
        content += f"**What to Expect:** A welcoming circle of people who understand the daily realities of {condition_text}. "
        content += f"You'll likely find both emotional support and practical tips from those who have walked a similar path.\n\n"
       
        # Friendly call-to-action
        content += f"**Find Your Way There:** [Get directions to join this community]({maps_link})\n\n"
   
    # Add testimonials - completely different from hospital format
    content += f"### 💭 Voices from the Community\n\n"
    content += f"> \"After my diagnosis, I felt so alone until I found my support group. Now I have friends who truly get it.\"\n\n"
    content += f"> \"The practical tips I've learned from others have made such a difference in my day-to-day life with this condition.\"\n\n"
    content += f"> \"Sometimes I go just to listen, other times to share. Both have been healing in different ways.\"\n\n"
   
    # Add friendly tips section
    content += f"### 🌟 Your First Visit\n\n"
    content += f"* It's totally normal to feel nervous about joining a new group - everyone felt that way at first!\n"
    content += f"* You're always welcome to just listen until you feel comfortable sharing\n"
    content += f"* Consider reaching out to the group coordinator before attending if you have questions\n"
    content += f"* Remember that everyone in these spaces is there for the same reason: connection and support\n\n"
   
    # Add warm closing
    content += f"*Remember: Sharing your story isn't just therapeutic for you - it can be a lifeline for someone else who's struggling. These communities welcome you just as you are!* 💕"
   
    return content
 
def format_generic_results(facilities, facility_type, chronic_condition, city):
    """Format generic results for any other facility type."""
    condition_text = chronic_condition if chronic_condition else "general healthcare needs"
    facility_type_display = facility_type.replace("_", " ").capitalize()
   
    # Create generic content
    content = f"# {facility_type_display} Resources\n\n"
    content += f"## Services for {condition_text} in {city}\n\n"
    content += f"### Available Facilities\n\n"
    content += f"Here are the {facility_type_display.lower()} facilities in {city} that may provide services related to {condition_text}.\n\n"
   
    for i, facility in enumerate(facilities, 1):
        name = facility.get("name", "Unnamed Facility")
        address = facility.get("address", "No address available")
        rating = facility.get("rating", "Not rated")
        maps_link = facility.get("maps_link", "#")
       
        content += f"#### {i}. {name}\n"
        content += f"**Address:** {address}\n\n"
       
        if rating != "Not rated":
            content += f"**Rating:** {rating}/5 ({facility.get('total_ratings', 0)} ratings)\n\n"
        else:
            content += f"**Rating:** Not rated\n\n"
       
        content += f"**Directions:** [View on Google Maps]({maps_link})\n\n"
   
    content += f"### Helpful Information\n\n"
    content += f"* Call facilities directly to inquire about specific services for {condition_text}\n"
    content += f"* Check each facility's website for more detailed information\n"
    content += f"* Consider visiting in person to better understand available resources\n\n"
   
    return content
 
def format_no_results(facility_type, chronic_condition, city):
    """Format no results message based on facility type."""
    condition_text = chronic_condition if chronic_condition else "your healthcare needs"
    facility_type_display = facility_type.replace("_", " ").capitalize()
   
    # Create no results message
    content = f"# No {facility_type_display} Facilities Found\n\n"
   
    # Hospital specific message
    if facility_type == "hospital":
        content += f"We couldn't locate any hospitals in {city} for {condition_text} in our database. This could be due to:\n\n"
        content += f"* Limited hospital data in this specific area\n"
        content += f"* Specialized hospitals might be located in nearby metropolitan areas\n"
        content += f"* The search parameters may need adjustment\n\n"
        content += f"**Medical Recommendations:**\n"
        content += f"* Try searching in neighboring larger cities\n"
        content += f"* Consider looking for medical centers or healthcare systems instead\n"
        content += f"* Consult with a primary care provider for appropriate referrals\n"
   
    # Clinic specific message
    elif facility_type == "clinic":
        content += f"We couldn't find any clinics in {city} for {condition_text} in our database. Some possibilities:\n\n"
        content += f"* The clinics might be listed under different categories\n"
        content += f"* Specialized care may require searching for specific practice types\n"
        content += f"* Your search area might need to be expanded\n\n"
        content += f"**Friendly Suggestions:**\n"
        content += f"* Try searching for 'medical offices' or 'doctor's offices' instead\n"
        content += f"* Check with your insurance provider for in-network options\n"
        content += f"* Consider telehealth options that might be available regardless of location\n"
   
    # Pharmacy specific message
    elif facility_type == "pharmacy":
        content += f"We couldn't locate any pharmacies in {city} for {condition_text} in our database. This might be because:\n\n"
        content += f"* The search area may need to be expanded\n"
        content += f"* Pharmacies might be located inside grocery stores or other retailers\n"
        content += f"* The search terms might need adjustment\n\n"
        content += f"**Practical Next Steps:**\n"
        content += f"* Try searching for drugstores or specific pharmacy chains by name\n"
        content += f"* Explore mail-order pharmacy options for medication needs\n"
        content += f"* Check with your healthcare provider for pharmacy recommendations\n"
   
    # Support group specific message - completely different from hospital
    elif facility_type == "mental_health_group" or facility_type == "community_center":
        content = f"#No Support Communities Found\n\n"
        content += f"We couldn't find any support groups or community centers in {city} for {condition_text} in our database. This often happens because:\n\n"
        content += f"* Many community support groups don't appear in standard business listings\n"
        content += f"* Groups often meet in spaces like churches, libraries, or community centers\n"
        content += f"* Some communities have more online than in-person support options\n\n"
        content += f"###  Finding Your Community\n\n"
        content += f"* Reach out to local hospitals and clinics - many host or know of support groups\n"
        content += f"* Contact national organizations for {condition_text} to find local chapters\n"
        content += f"* Check community bulletin boards at libraries, grocery stores, and community centers\n"
        content += f"* Explore online communities which can provide support regardless of location\n"
        content += f"* Consider social media platforms where condition-specific groups often form\n\n"
        content += f"*Remember that finding the right support community might take time, but connection is worth the search.* 💕"
   
    # Generic message for other types
    else:
        content += f"We couldn't find any {facility_type_display.lower()} facilities in {city} for {condition_text} in our database. Please try:\n\n"
        content += f"* Expanding your search to nearby areas\n"
        content += f"* Trying different facility types\n"
        content += f"* Checking if the city name is spelled correctly\n"
        content += f"* Using more general search terms\n"
   
    return content
 
# Define the decision function for routing
def decide_next_step(state: LocationAgentState) -> Literal["extract_location", "search_facilities", "format_results", "END"]:
    """Decide the next step in the workflow based on the current state."""
    return state["next_step"]
 
# Create and configure the graph
def create_location_agent_graph() -> StateGraph:
    """Create the location agent graph workflow."""
    # Initialize the graph
    workflow = StateGraph(LocationAgentState)
   
    # Add nodes to the graph
    workflow.add_node("extract_location", extract_location_information)
    workflow.add_node("search_facilities", search_healthcare_facilities)
    workflow.add_node("format_results", format_search_results)
   
    # Add conditional edges
    workflow.add_conditional_edges(
        "extract_location",
        decide_next_step,
        {
            "search_facilities": "search_facilities",
            "format_results": "format_results",
            END: END
        }
    )
   
    workflow.add_conditional_edges(
        "search_facilities",
        decide_next_step,
        {
            "format_results": "format_results",
            END: END
        }
    )
   
    workflow.add_conditional_edges(
        "format_results",
        decide_next_step,
        {
            END: END
        }
    )
   
    # Set the entry point
    workflow.set_entry_point("extract_location")
   
    return workflow
 
# Function to run the graph
def run_location_agent(query: str, chronic_condition: str = "") -> Dict[str, Any]:
    """Run the location agent with the given query."""
    try:
        # Create the graph
        graph = create_location_agent_graph()
       
        # Create a compiled graph for execution
        app = graph.compile()
       
        # Initialize the state
        initial_state = {
            "query": query,
            "chronic_condition": chronic_condition,
            "location_details": {},
            "search_results": {},
            "messages": [{"role": "user", "content": query}],
            "next_step": "extract_location"
        }
       
        logger.info(f"Running location agent with query: {query}, condition: {chronic_condition}")
       
        # Run the graph
        result = app.invoke(initial_state)
       
        # Extract the final results
        return {
            "success": result["search_results"].get("success", False),
            "facilities": result["search_results"].get("facilities", []),
            "messages": result["messages"],
            "location_details": result["location_details"]
        }
   
    except Exception as e:
        logger.error(f"Error running location agent: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "facilities": [],
            "messages": [
                {"role": "user", "content": query},
                {"role": "assistant", "content": f"Sorry, I encountered an error: {str(e)}"}
            ]
        }