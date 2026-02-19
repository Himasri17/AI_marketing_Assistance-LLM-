# AI Tribal Marketplace

A marketplace for tribal products with AI-powered features including image recognition, text generation, and translation.

## Features

- Backend API with FastAPI
- SQLite database
- AI services: VIT model for image processing, text generator, translator
- Simple HTML/CSS/JS frontend

## Setup

1. Install dependencies: `pip install -r backend/requirements.txt`
2. Run the backend: `uvicorn backend.app.main:app --reload`
3. Open frontend/index.html in browser

## Docker

Run with Docker Compose: `docker-compose up`