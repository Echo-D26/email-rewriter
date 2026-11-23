import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)

MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = (
    "You are an expert email editor. Rewrite the email the user gives you. "
    "Keep the original meaning and facts. Fix grammar and clarity. "
    "Return only the rewritten email, with no explanations."
)

def rewrite_email(email_text, tone="professional"):
    if not email_text.strip():
        return "Please enter an email first."
    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=1000,
            temperature=0.5,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",
                 "content": f"Tone: {tone}\n\nEmail to rewrite:\n{email_text}"},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    email = input("Paste your email: ")
    tone = input("Tone (professional / friendly / short / firm): ")
    print("\n--- Rewritten email ---\n")
    print(rewrite_email(email, tone))