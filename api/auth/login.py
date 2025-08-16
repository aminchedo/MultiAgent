from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import json
import os
import jwt
from datetime import datetime, timedelta
import hashlib

app = FastAPI()

# Simple user database (replace with real database)
USERS = {
    "admin": {
        "id": "1",
        "email": "admin",
        "password_hash": hashlib.sha256("admin".encode()).hexdigest(),
        "name": "Admin User"
    }
}

def create_jwt_token(user_data):
    payload = {
        'user_id': user_data['id'],
        'email': user_data['email'],
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, os.getenv('JWT_SECRET_KEY', 'secret'), algorithm='HS256')

async def handler(request: Request):
    if request.method == "POST":
        try:
            body = await request.json()
            email = body.get('email')
            password = body.get('password')
            
            if not email or not password:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Email and password required"}
                )
            
            # Check user credentials
            user = USERS.get(email)
            if not user:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid credentials"}
                )
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if user['password_hash'] != password_hash:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid credentials"}
                )
            
            # Create JWT token
            token = create_jwt_token(user)
            
            return JSONResponse(content={
                "success": True,
                "user": {
                    "id": user['id'],
                    "email": user['email'],
                    "name": user['name']
                },
                "token": token
            })
            
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": str(e)}
            )
    
    return JSONResponse(
        status_code=405,
        content={"error": "Method not allowed"}
    )