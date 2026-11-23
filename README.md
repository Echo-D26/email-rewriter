# Email Rewriter

A small app that rewrites rough emails in a chosen tone using the Groq API.
It has a web dashboard (Streamlit) and an API (FastAPI).

# Features
- Choose a tone: professional, friendly, short or firm
- Web dashboard
- REST API with an automatic test page

# Setup
1. Install Python 3.11
2. Install the packages: `pip install -r requirements.txt`
3. Get a free API key at console.groq.com
4. Create a file named `.env` containing: `GROQ_API_KEY=your_key_here`

# Run
- Dashboard: `streamlit run dashboard.py`
- API: `uvicorn api:app --reload` then open http://127.0.0.1:8000/docs

# Files
- `core.py`: the function that calls the AI
- `dashboard.py`: the web page
- `api.py`: the API