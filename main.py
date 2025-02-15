# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import timedelta
from sqlalchemy.orm import Session

import auth
from models import Base, User, Chat
import database
import llm  # Import our LLM module

# Create tables (for development only; consider using Alembic for production)
#Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Enable CORS (adjust allowed origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication endpoint (as before)
@app.post("/token")
async def login_for_access_token(
    db: Session = Depends(database.get_db),
    form_data: auth.OAuth2PasswordBearer = Depends()
):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Protected endpoint to get current user details
@app.get("/users/me")
async def read_users_me(current_user: User = Depends(auth.get_current_user)):
    return current_user

# Define a Pydantic model for chat requests
from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    session_type: str = "general"  # can be "diagnosis", "topic", or "general"
    topic: Optional[str] = None    # Allows topic to be None

# Chat endpoint that stores chat data in PostgreSQL
@app.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Generate emotion analysis (optional)
    emotion_result = llm.get_emotion_analysis(request.message)
    
    # Generate a response using LLM logic
    response_text = llm.get_response(request.message, request.session_type, request.topic)
    
    # Create a new Chat record using the SQLAlchemy model
    new_chat = Chat(
        user_id=current_user.id,
        message=request.message,
        response=response_text
    )
    
    # Save the chat record to the database
    db.add(new_chat)
    await db.commit()  # Commit changes asynchronously
    await db.refresh(new_chat)  # Refresh to get the new_chat.id, etc.
    
    return {
        "reply": response_text,
        "emotion": emotion_result,
        "chat_id": new_chat.id
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
