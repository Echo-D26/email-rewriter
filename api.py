from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core import rewrite_email, refine_email, analyze_email, diff_html, CHIPS

app = FastAPI(title="Email Rewriter API")


class EmailRequest(BaseModel):
    email: str
    tone: str = "professional"


class RefineRequest(BaseModel):
    email: str
    instruction: str


class AnalyzeRequest(BaseModel):
    original: str
    rewritten: str


def run(function, *args):
    """Call a core function and turn errors into proper HTTP errors."""
    try:
        return function(*args)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")


@app.get("/")
def home():
    return {"status": "running"}


@app.get("/chips")
def chips():
    return CHIPS


@app.post("/rewrite")
def rewrite(req: EmailRequest):
    return {"rewritten": run(rewrite_email, req.email, req.tone)}


@app.post("/refine")
def refine(req: RefineRequest):
    return {"refined": run(refine_email, req.email, req.instruction)}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    result = run(analyze_email, req.original, req.rewritten)
    old_html, new_html = diff_html(req.original, req.rewritten)
    return {**result, "diff": {"original_html": old_html, "rewritten_html": new_html}}