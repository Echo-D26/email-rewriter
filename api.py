from fastapi import FastAPI
from pydantic import BaseModel
from core import rewrite_email

app = FastAPI(title="Email Rewriter API")

class EmailRequest(BaseModel):
    email: str
    tone: str = "professional"

@app.get("/")
def home():
    return {"status": "running"}

@app.post("/rewrite")
def rewrite(req: EmailRequest):
    return {"rewritten": rewrite_email(req.email, req.tone)}