#  Architecture Diagram

```mermaid
flowchart TD
  %% USER INPUT
  User([ User])
  User -->|Selects Condition + Location| StreamlitUI

  subgraph Frontend [Frontend - Streamlit]
      StreamlitUI([ Streamlit UI])
      StreamlitUI --> NutritionTab([ Nutrition Tracker])
      StreamlitUI --> DrugTab([ Medication Tracker])
      StreamlitUI --> InfoTab([ Condition KB])
      StreamlitUI --> NearbyTab([ Clinics & Support])
      StreamlitUI --> SummaryTab([ Health Summary])
  end

  subgraph Backend [FastAPI + LangGraph]
      FastAPI([ FastAPI Backend])
      subgraph LangGraphController [LangGraph Agent Controller]
          NutritionAgent([ Nutrition Agent])
          DrugAgent([ Drug Agent])
          ConditionAgent([ Condition QA Agent])
          LocationAgent([ Nearby Search Agent])
          SummaryAgent([ Summary & Alert Agent])
      end
      FastAPI --> NutritionAgent
      FastAPI --> DrugAgent
      FastAPI --> ConditionAgent
      FastAPI --> LocationAgent
      FastAPI --> SummaryAgent
  end

  Airflow([ Airflow Pipeline Orchestrator])

  subgraph ExternalAPIs [ External APIs]
      Spoonacular([ Spoonacular])
      OpenFDA([ OpenFDA])
      WebSearch([ Real-Time Web Search])
  end

  S3([ AWS S3 - PDFs & Markdown])
  Mistral([ Mistral AI - PDF to Markdown])
  Chunking([ Document Chunking])
  OpenAIEmbed([ OpenAI Embeddings])
  Pinecone([Pinecone Vector DB])
  Snowflake([ Snowflake Structured Data])
  Email([ Email Alerts])

  PDFUpload([ Chronic Condition PDFs])
  PDFUpload -->|Upload| S3
  S3 -->|Convert| Mistral
  Mistral -->|.md| Chunking
  Chunking --> OpenAIEmbed
  OpenAIEmbed --> Pinecone

  NutritionAgent --> Snowflake
  DrugAgent --> Snowflake
  ConditionAgent --> Pinecone
  ConditionAgent --> S3
  LocationAgent --> WebSearch

  Spoonacular --> Airflow
  OpenFDA --> Airflow
  Airflow --> Snowflake

  SummaryAgent --> Snowflake
  SummaryAgent --> Pinecone
  SummaryAgent --> S3
  SummaryAgent --> Email
  SummaryAgent -->|Summarized Output| StreamlitUI
