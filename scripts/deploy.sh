#!/bin/bash

# Start backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Start frontend
cd ../frontend
npm start
