# Procfile for Koyeb, Heroku, or other PaaS
# This command runs the main sales automation loop
worker: python main.py --audit --niche "Plumber" --location "San Francisco" --limit 10
# If you want to run the FastAPI server instead:
web: uvicorn main:app --host 0.0.0.0 --port $PORT
