# ChronicCare.AI-Multi-Agent-Health-Management-System

## Live Application Links
[![codelab](https://img.shields.io/badge/codelabs-4285F4?style=for-the-badge&logo=codelabs&logoColor=white)](https://codelabs-preview.appspot.com/?file_id=1vRDlDe1wL3BszPOn75w2uF0WKvaB9SjdFROvnrNpknE#0)
* Streamlit App(not live): http://157.245.251.74:8501
* FastAPI Docs(not live): http://157.245.251.74:8000/docs
* Airflow(not live): http://157.245.251.74:8082

## Technologies Used
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/fastapi-109989?style=for-the-badge&logo=FASTAPI&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-000000?style=for-the-badge&logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Snowflake](https://img.shields.io/badge/Snowflake-56B9EB?style=for-the-badge&logo=snowflake&logoColor=white)](https://www.snowflake.com/)
[![dbt](https://img.shields.io/badge/dbt-FF694B?style=for-the-badge&logo=dbt&logoColor=white)](https://docs.getdbt.com/)
[![Apache Airflow](https://img.shields.io/badge/Apache_Airflow-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white)](https://airflow.apache.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-C71A36?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![LangChain](https://img.shields.io/badge/LangChain-000000?style=for-the-badge&logo=langchain&logoColor=white)](https://www.langchain.com/)
[![Amazon AWS](https://img.shields.io/badge/Amazon_AWS-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](https://aws.amazon.com/)
[![Pinecone](https://img.shields.io/badge/Pinecone-6A4CBB?style=for-the-badge&logo=pinecone&logoColor=white)](https://www.pinecone.io/)
[![MistralAI](https://img.shields.io/badge/MistralAI-4C75A3?style=for-the-badge&logo=mistralai&logoColor=white)](https://www.mistral.ai/)
[![Tavily](https://img.shields.io/badge/Tavily-007ACC?style=for-the-badge&logo=internetexplorer&logoColor=white)](https://www.tavily.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)
[![Google Maps API](https://img.shields.io/badge/Google_Maps_API-4285F4?style=for-the-badge&logo=googlemaps&logoColor=white)](https://developers.google.com/maps/documentation)
[![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![DigitalOcean](https://img.shields.io/badge/DigitalOcean-0080FF?style=for-the-badge&logo=digitalocean&logoColor=white)](https://www.digitalocean.com/)
[![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-000000?style=for-the-badge&logo=matplotlib&logoColor=white)](https://matplotlib.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-008000?style=for-the-badge&logo=python&logoColor=white)](https://docs.pydantic.dev/)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/)
[![Python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://www.python.org/)
[![Seaborn](https://img.shields.io/badge/Seaborn-005571?style=for-the-badge&logo=python&logoColor=white)](https://seaborn.pydata.org/)

## Overview

ChronicCare.AI is a multi-agent health management system that supports individuals with chronic conditions like diabetes, hypertension, and heart disease by offering a unified dashboard for personalized nutrition, calorie tracking, medication guidance, live news about latest discovery and access to nearby healthcare facilities—including hospitals, pharmacies, and mental health support groups. By integrating structured nutrition data, unstructured medical documents, and real-time web sources, the system generates actionable health summaries and alerts, enhancing daily decision-making and proactive care.

## Problem Statement

Managing chronic health conditions demands daily attention to nutrition, medication, and lifestyle decisions—yet patients often lack a centralized, intelligent system that adapts to their evolving health needs. Existing tools fall short in integrating medical literature, dietary tracking, and real-time support, leading to fragmented care, missed alerts, and reduced adherence to treatment plans.

## Project Goals

- Build a multi-agent assistant combining structured data, medical PDFs, and live web content for chronic care.
- Design a Nutrition Agent to provide calorie needs and food suggestions based on medical benchmarks.
- Develop a Knowledge Base Agent to answer queries from research papers.
- Implement a Location Agent to find nearby clinics, pharmacies, and support groups.
- Create a Live Summary Agent to summarize real-time news and discoveries for specific chronic conditions.
- Enable email alerts for under/over calorie intake, remaining daily calories, and meal planning based on weekly consumption trends.
- Build an ETL pipeline with Airflow to ingest nutrition data from Edamam API into Snowflake.
- Containerize and deploy all components with Docker on DigitalOcean for public access.

## Architecture Diagram

### Data Pipeline
<img width="827" alt="Final_Project" src="https://github.com/user-attachments/assets/9f27e7dd-f3c1-4cf0-8291-1c37c49d0748" />

### Overall Architecture
<img width="986" alt="Overall_Architecture" src="https://github.com/user-attachments/assets/cd2de6be-b420-4be4-8ffe-1e60a7ae0ae6" />

## Directory Structure
```
ChronicCare.AI-Multi-Agent-Health-Management-System/
├── .gitignore
├── .env
├── agents/
│   ├── __init__.py
│   ├── knowledgbase_agent/
│   │   ├── __init__.py
│   │   ├── chunking.py
│   │   ├── knowledgebase_tool.py
│   │   ├── mistral_ai.py
│   │   ├── pdf_to_s3.py
│   │   └── pinecone_utils.py
│   ├── news_agent/
│   │   ├── __init__.py
│   │   ├── news_controller.py
│   │   └── news_tool.py
│   ├── nutrition_agent/
│   │   ├── get_user_condition_tool.py
│   │   ├── nutrition_constraints.py
│   │   ├── nutrition_orchestrator.py
│   │   ├── recommend_recipes_tool.py
│   │   └── snowflake_connector.py
│   ├── orchestrator.py
│   └── search_location_agent/
│       ├── __init__.py
│       ├── google_oracle.py
│       ├── graph.py
│       └── location_agent.py
├── airflow/
│   ├── dags/
│   │   └── dag_extract_load_transform.py
│   ├── dbt_recipe/
│   │   ├── .dbt/
│   │   │   ├── .user.yml
│   │   │   └── profiles.yml
│   │   ├── .gitignore
│   │   ├── analyses/
│   │   │   └── .gitkeep
│   │   ├── dbt_project.yml
│   │   ├── macros/
│   │   │   └── .gitkeep
│   │   ├── models/
│   │   │   ├── sources.yml
│   │   │   └── staging/
│   │   │       ├── schema.yml
│   │   │       └── stg_recipes.sql
│   │   ├── packages.yml
│   │   ├── README.md
│   │   ├── seeds/
│   │   │   └── .gitkeep
│   │   ├── snapshots/
│   │   │   └── .gitkeep
│   │   └── tests/
│   │       └── .gitkeep
│   ├── docker-compose.yaml
│   ├── Dockerfile
│   ├── recipe/
│   │   ├── __init__.py
│   │   ├── extract_recipe.py
│   │   └── uploaded_recipes.txt
│   └── requirements.txt
│   └── .env
├── backend/
│   ├── __init__.py
│   ├── .env
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
│   ├── users.py
│   └── utils_backend/
│       ├── alert_jobs.py
│       ├── email_utils.py
│       └── Nutrition_Agent2.png
├── docker-compose.yaml
├── frontend/
│   ├── .streamlit/
│   │   └── config.toml
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env
│   └── utils/
│       ├── __init__.py
│       ├── home.py
│       ├── knowledge_base.py
│       ├── live_news.py
│       ├── location_search_streamlit.py
│       ├── login.py
│       ├── nutrition_agent_streamlit.py
│       ├── nutrition_dashboard.py
│       └── signup.py
├── postgres_db/
│   ├── auth.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── setup_db.py
├── prototypes/
│   ├── drug_fda.ipynb
│   ├── nutrition_test.py
│   ├── recipe_test.ipynb
│   └── uploaded_recipes.txt
├── README.md
├── requirements.txt
└── test_workflow/
    └── flowchart.md
```

## Application Workflow

1. Sign Up & Login
  - The user starts by signing up with their basic details: name, chronic condition, height, weight, and activity level. After submitting, the system calculates their BMI and daily calorie needs. The user can then log in to access all features.
2. Knowledge Assistant
  - After logging in, the user can visit the Knowledge Assistant page to ask questions like:
    - “What is name_of_the_disease(eg. Cholesterol)”
    - “What are the risk factors”
    - "What medications are prescribed for name_of_the_disease(eg. Cholesterol)"
  - The user can also click "Generate Summary" to instantly get key information like symptoms, stages, treatments, remedies, medications and general doctor’s advice for their condition.
3. Nutrition Planner
  - The user will be suggested recipes based on Cuisine Type selected by the user and add them to their meal plan by selecting a meal type (Breakfast, Lunch, Snacks, or Dinner). The planner ensures meals align with their health condition and calorie needs.
4. Nutrition Dashboard
  - The dashboard displays daily and weekly calorie intake and remaining calories. Users can track recipe logs and visualize their intake. If the user exceed or miss targets, the user receives automatic email alerts.
5. Location Assistance
  - The user can enter their condition, city, and pincode to find nearby healthcare services. The user can choose to view Hospitals, Pharmacies, or Mental Health Support Groups in their area.
6. Live News
  - On the Live News page, the user gets short summaries of the latest discoveries and updates related to their chronic condition—fetched in real-time from trusted sources.
7. Profile Management
  - The user can visit their profile to update password or review personal and health information at any time.

## Prerequisites
- Python: Ensure Python is installed on your system. Python 3.8+ is recommended.
- Docker: Ensure Docker Desktop is installed and running.
- Docker Resources: Allocate at least 4 CPUs and 8 GB RAM for smooth execution of Streamlit, FastAPI, and other containers.
- API Keys: Add your OpenAI, Pinecone, Tavily, and Google Maps API, Mistral AI keys to the appropriate .env files (e.g., backend/.env, frontend/.env, airflow/.env).
- Streamlit Knowledge: Familiarity with Streamlit will help in understanding and customizing the financial assistant UI.
- FastAPI Knowledge: Understanding FastAPI will assist in debugging backend agent routes and API validation logic.
- LangGraph Orchestration: Basic understanding of how LangGraph handles multi-agent workflows will help in extending the system.
- Vector Database Concepts: Knowledge of semantic search, embeddings, and metadata filtering will be useful when working with Pinecone.
- Snowflake Basics: Knowing how to query structured data from Snowflake will help in modifying or scaling the pipeline.
- Airflow + DBT: Familiarity with DAGs, tasks, and DBT transformations helps monitor and manage the nutrition ingestion pipeline.
- PostgreSQL & SQLAlchemy: Understanding database schemas, ORM, and authentication logic helps in managing user credentials and profile data.
- Git: Required for cloning, committing, and version-controlling the codebase.
- Open Ports:
  - 8501 – Streamlit UI
  - 8000 – FastAPI Backend
  - 8082 – Airflow Webserver
  - 5432 – PostgreSQL Database (if accessed locally)

## How to run this Application Locally

1. Clone the Repository
```
git clone https://github.com/your-username/ChronicCare.AI-Multi-Agent-Health-Management-System.git
cd ChronicCare.AI-Multi-Agent-Health-Management-System
```

2. Set Up Environment Configuration:
- Create .env files in backend/, frontend/, and airflow/ directories with the following variables as needed:
```
[EDAMAM]
APP_ID = 
APP_KEY = 

[AWS]
AWS_BUCKET_NAME = 
AWS_ACCESS_KEY_ID = 
AWS_SECRET_ACCESS_KEY = 
AWS_REGION = 

[SNOWFLAKE]
SNOWFLAKE_USER = 
SNOWFLAKE_PASSWORD = 
SNOWFLAKE_ACCOUNT = 
SNOWFLAKE_DBT_ROLE = 
SNOWFLAKE_WAREHOUSE = 
SNOWFLAKE_DATABASE = 
SNOWFLAKE_SCHEMA_DBT = 

[OPENAI]
OPENAI_API_KEY = 

[PINECONE]
PINECONE_API_KEY = 
INDEX_NAME = 

[MISTRAL]
MISTRAL_API_KEY = 

[TAVILY]
TAVILY_API_KEY = 

[GOOGLE_MAPS]
GOOGLE_API_KEY = 

[POSTGRES]
DATABASE_URL = 
POSTGRES_HOST = 
POSTGRES_PORT = 
POSTGRES_USER = 
POSTGRES_PASSWORD = 
POSTGRES_DB = 

[AUTH]
SECRET_KEY = 
ALGORITHM = 
ACCESS_TOKEN_EXPIRE_MINUTES = 

```
3. Create and Activate a Virtual Environment
```
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```
4. Install Required Packages
```
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
pip install -r airflow/requirements.txt
```
5. Build and Start All Services: Make sure Docker is running, then execute:
```
docker-compose up --build
```
This starts:
  - Streamlit Frontend → http://localhost:8501
  - FastAPI Backend → http://localhost:8000/docs
  - Airflow Webserver → http://localhost:8082

6. Use the Application
- Open the Streamlit UI at http://localhost:8501
- Sign up with your chronic condition and personal details
- Explore the app: Ask health questions, plan meals, monitor intake, find nearby support, and read chronic-specific news
- Track your health journey through visual dashboards and personalized AI insights


## REFERENCES

- https://langchain-ai.github.io/langgraph/
- https://colab.research.google.com/github/pinecone-io/examples/blob/master/learn/generation/langchain/langgraph/01-gpt-4o-research-agent.ipynb
- https://docs.langchain.com
- https://docs.pinecone.io/  
- https://docs.pinecone.io/docs/metadata-filtering
- https://airflow.apache.org/docs/
- https://airflow.apache.org/docs/apache-airflow-providers-snowflake/
- https://docs.snowflake.com/  
- https://docs.snowflake.com/en/user-guide/python-connector
- https://docs.getdbt.com/
- https://quickstarts.snowflake.com/
- https://tavily.com/
- https://platform.openai.com/docs
- https://developers.google.com/maps/documentation
- https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/
- https://fastapi.tiangolo.com/tutorial/sql-databases/](https://fastapi.tiangolo.com/tutorial/sql-databases/
- https://docs.streamlit.io/](https://docs.streamlit.io/
- https://docs.docker.com
- https://docs.github.com/en](https://docs.github.com/en
