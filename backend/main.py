from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import logging
import traceback
 
# ========== LangGraph Agent Imports ==========
from langchain_core.messages import HumanMessage, AIMessage
from agents.orchestrator import run_agents
from agents.nutrition_agent.nutrition_orchestrator import run_nutrition_agents
 
 
# ========== Auth & DB Setup ==========
import postgres_db.models as models
from postgres_db.database import engine
import users

# Location Agent
from agents.search_location_agent.location_agent import run_location_agent
from typing import Optional, Dict, Any
 
from agents.news_agent.news_controller import run_news_agent
 
 
# ========== Configure Logging ==========
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
 
# ========== Create Tables ==========
models.Base.metadata.create_all(bind=engine)
 
# ========== FastAPI Initialization ==========
app = FastAPI(title="Chronic Disease Management API")
 
 
 
# ========== CORS Setup ==========
origins = [
    "http://localhost",
    "http://localhost:8501",
    "http://127.0.0.1:8501",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# ========== Global Exception Handler ==========
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": f"An error occurred: {str(exc)}"}
    )
 
# ========== Routers ==========
app.include_router(users.router)
 
# ========== Health Check ==========
@app.get("/")
async def root():
    return {"message": "Welcome to the Chronic Disease Management API"}
 
# ========== Request & Response Schemas ==========
class Message(BaseModel):
    type: str  # "human" or "ai"
    content: str
 
class AgentRequest(BaseModel):
    input: str
    condition: str
    chat_history: List[Message]
 
class AgentResponse(BaseModel):
    response: str
 
class NutritionRequest(BaseModel):
    username: str
    cuisine_types: List[str]
    meal_types: List[str]
 
class NutritionResponse(BaseModel):
    response: str
 
class LocationSearchRequest(BaseModel):
    query: str
    zipcode: str  # Now required
    chronic_condition: Optional[str] = ""
    facility_type: Optional[str] = "hospital"
    additional_params: Optional[Dict[str, Any]] = {}
 
class NewsRequest(BaseModel):
    condition: str
 
class NewsResponse(BaseModel):
    condition: str
    news: Dict[str, Any]  
 
 
# ========== Endpoint: Knowledge Assistant ==========
@app.post("/agent", response_model=AgentResponse)
def agent_endpoint(req: AgentRequest):
    print("\n===================== 🚨 /agent called =====================")
    print(f"📥 Input: {req.input}")
    print(f"🩺 Condition: {req.condition}")
    print("📚 Chat History:")
    for msg in req.chat_history:
        print(f"  [{msg.type.upper()}] {msg.content}")
 
    # Format chat history for LangGraph
    formatted_history = []
    for msg in req.chat_history:
        if msg.type == "human":
            formatted_history.append(HumanMessage(content=msg.content))
        elif msg.type == "ai":
            formatted_history.append(AIMessage(content=msg.content))
 
    try:
        response = run_agents(
            input_text=req.input,
            chat_history=formatted_history,
            condition=req.condition
        )
        print(f"✅ Final Agent Response: {response[:300]}...\n")
        return AgentResponse(response=response)
 
    except Exception as e:
        logger.error(f"❌ Error in LangGraph agent execution: {str(e)}", exc_info=True)
        return AgentResponse(response="Sorry, something went wrong while processing your request.")
 
# ========== Endpoint: Nutrition Assistant ==========
@app.post("/nutrition", response_model=NutritionResponse)
def nutrition_endpoint(req: NutritionRequest):
    print("\n===================== 🥗 /nutrition called =====================")
    print(f"👤 Username: {req.username}")
    print(f"🍛 Cuisines: {req.cuisine_types}")
    print(f"🕒 Meals: {req.meal_types}")
 
    try:
        result = run_nutrition_agents(
            username=req.username,
            cuisine_types=req.cuisine_types,
            meal_types=req.meal_types,
            input_text="",       # Optional for now; may be used in future chat prompts
            chat_history=[]      # Expand to full conversation if needed
        )
        print(f"✅ Nutrition Agent Output: {result[:300]}...\n")
        return NutritionResponse(response=result)
 
    except Exception as e:
        logger.error(f"❌ Error in /nutrition agent: {str(e)}", exc_info=True)
        return NutritionResponse(response="Sorry, something went wrong while generating your nutrition plan.")
    
 
@app.post("/search-facilities")
async def search_facilities(request: LocationSearchRequest):
    """
    Search for healthcare facilities based on location and condition
    """
    try:
        if not request.zipcode:
            raise HTTPException(status_code=400, detail="Zipcode is required")
 
        if request.facility_type and request.facility_type not in request.query:
            query = f"Find {request.facility_type} for {request.chronic_condition} in {request.query}"
        else:
            query = request.query
 
        result = run_location_agent(
            query=query,
            zipcode=request.zipcode,
            chronic_condition=request.chronic_condition,
            facility_type=request.facility_type,
            additional_params=request.additional_params
        )
 
        return result
 
    except Exception as e:
        logger.error(f"Error in search_facilities endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
 
 
@app.get("/chronic-conditions")
async def get_chronic_conditions():
    """
    Retrieve list of supported chronic conditions
    """
    return [
        "Diabetes",
        "Cholesterol",
        "Hypertension",
        "Chronic Kidney Disease",
        "Gluten Intolerance",
        "Polycystic",
        "Obesity"
    ]

 
@app.get("/facility-types")
async def get_facility_types():
    """
    Retrieve list of supported facility types
    """
    return [
        {"id": "hospital", "name": "Hospital"},
        {"id": "clinic", "name": "Clinic"},
        {"id": "pharmacy", "name": "Pharmacy"},
        {"id": "support_group", "name": "Support Group/Community Center"}
    ]
 
@app.post("/news", response_model=NewsResponse)
def fetch_news(req: NewsRequest):
    """
    Fetch latest news for a chronic condition using the news LangGraph agent
    """
    try:
        result = run_news_agent(req.condition)
        return NewsResponse(condition=req.condition, news=result)
 
    except Exception as e:
        logger.error(f"Error in /news endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unable to fetch news at this time.")
    


# 🔔 ALERT JOBS
from apscheduler.schedulers.background import BackgroundScheduler
from utils_backend.alert_jobs import (
    send_daily_summary,
    send_low_logging_alert,
    send_weekly_digest,
    send_critical_calorie_warning
)

scheduler = BackgroundScheduler()

# Final Cron Schedule
scheduler.add_job(send_daily_summary, 'cron', hour=21, minute=0)
scheduler.add_job(send_low_logging_alert, 'cron', hour=10, minute=0)
scheduler.add_job(send_weekly_digest, 'cron', day_of_week='sun', hour=20, minute=0)
scheduler.add_job(send_critical_calorie_warning, 'cron', hour=23, minute=30)

scheduler.start()



@app.get("/alerts/test")
def run_alerts_now():
    send_daily_summary()
    send_low_logging_alert()
    send_weekly_digest()
    send_critical_calorie_warning()
    return {"status": "✅ All alert jobs executed manually"}
