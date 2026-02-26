# AI Fact Checker

## Overview
AI-powered fact-checking system using:
- FastAPI
- LangChain
- LangGraph
- Groq LLM
- Tavily Search API
- Docker + Nginx
- AWS-ready architecture

## Run Locally

### 1. Install dependencies
pip install -r requirements.txt

### 2. Set environment variables
Create .env file with API keys

### 3. Run server
uvicorn app.main:app --reload

Server runs at:
http://localhost:8000

## Docker Run

docker build -t ai-fact-checker .
docker run -p 8000:8000 --env-file .env ai-fact-checker