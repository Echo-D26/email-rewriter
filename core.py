import os
import re
import json
import html
import difflib

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)

MODEL = "openai/gpt-oss-120b"

TONES = ["professional", "friendly", "short", "firm"]

REWRITE_PROMPT = (
    "You are an expert email editor. Rewrite the email the user gives you. "
    "Keep the original meaning and facts. Fix grammar and clarity. "
    "Do not invent names, dates or details. Keep any [placeholders] as they are. "
    "Return only the rewritten email, with no explanations."
)

REFINE_PROMPT = (
    "You edit emails. Apply the instruction to the email. "
    "Keep the facts and the main request. Return only the full edited email."
)

ANALYZE_PROMPT = (
    "You review emails. Return ONLY a JSON object, no other text, in this shape:\n"
    '{"original": {"formality": 0-100, "warmth": 0-100, "directness": 0-100},'
    ' "rewritten": {"formality": 0-100, "warmth": 0-100, "directness": 0-100},'
    ' "pitfalls": [{"type": "blunt" | "buried_ask" | "vague_ask", "message": "short advice"}]}\n'
    "Scores: formality (0 very casual, 100 very formal), warmth (0 cold, 100 very warm), "
    "directness (0 very indirect, 100 very direct). "
    "Pitfalls apply to the REWRITTEN email only: 'blunt' if it may sound rude or harsh, "
    "'buried_ask' if the main request is not clear in the first two sentences, "
    "'vague_ask' if it asks for something without saying what or by when. "
    "Use an empty list if there are no problems."
)

# One-click edits shown as chips under the result
CHIPS = {
    "✂️ 30% shorter": "Make it about 30% shorter. Remove filler but keep the main request.",
    "🤝 Soften the ask": "Soften the request so it sounds polite and less demanding.",
    "📣 Add a call-to-action": "End with one clear call-to-action saying exactly what the reader should do next.",
    "👔 More formal": "Make the tone more formal and business-like.",
    "☀️ Warmer": "Make the tone warmer and friendlier without becoming unprofessional.",
}


def _chat(system, user, temperature=0.5, json_mode=False):
    """Send one request to Groq and return the reply text."""
    extra = {"response_format": {"type": "json_object"}} if json_mode else {}
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=1000,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        **extra,
    )
    return response.choices[0].message.content.strip()


def rewrite_email(email_text, tone="professional"):
    if not email_text.strip():
        raise ValueError("Please enter an email first.")
    return _chat(REWRITE_PROMPT, f"Tone: {tone}\n\nEmail to rewrite:\n{email_text}")


def refine_email(current_text, instruction):
    return _chat(REFINE_PROMPT, f"Instruction: {instruction}\n\nEmail:\n{current_text}")


# ---------- Pitfall checks ----------

PLACEHOLDER_PATTERNS = [
    r"\[[^\]\n]{1,40}\]",        # [Name]
    r"\{\{?[^}\n]{1,40}\}?\}",   # {name} or {{name}}
    r"<[^>\n]{2,40}>",           # <insert date>
    r"\bX{3,}\b",                # XXX
    r"\bTBD\b",
    r"_{3,}",                    # ____
]


def find_placeholders(text):
    found = []
    for pattern in PLACEHOLDER_PATTERNS:
        for match in re.findall(pattern, text):
            if match not in found:
                found.append(match)
    return found


def _clamp(value):
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return 50


def analyze_email(original, rewritten):
    """Return tone scores for both versions plus a list of pitfalls."""
    scores = {
        "original": {"formality": 50, "warmth": 50, "directness": 50},
        "rewritten": {"formality": 50, "warmth": 50, "directness": 50},
    }
    pitfalls = []

    try:
        raw = _chat(
            ANALYZE_PROMPT,
            f"ORIGINAL:\n{original}\n\nREWRITTEN:\n{rewritten}",
            temperature=0.1,
            json_mode=True,
        )
        data = json.loads(raw)
        for version in ("original", "rewritten"):
            for key in ("formality", "warmth", "directness"):
                scores[version][key] = _clamp(data.get(version, {}).get(key))
        pitfalls = [p for p in data.get("pitfalls", []) if isinstance(p, dict)]
    except Exception:
        pitfalls = [{"type": "info", "message": "Tone analysis was unavailable for this version."}]

    # Placeholder check is done with plain code, so it is always reliable
    for item in find_placeholders(rewritten):
        pitfalls.insert(0, {"type": "placeholder", "message": f"Unfilled placeholder: {item}"})

    return {"scores": scores, "pitfalls": pitfalls}


# ---------- Word-level diff ----------

def _tokens(text):
    return re.findall(r"\s+|\w+|[^\w\s]", text)


def _clean(tokens):
    return html.escape("".join(tokens)).replace("\n", "<br>")


def diff_html(old, new):
    """Return (left_html, right_html). Removed words are red on the left, added words green on the right."""
    a, b = _tokens(old), _tokens(new)
    matcher = difflib.SequenceMatcher(
        None, [t.lower() for t in a], [t.lower() for t in b], autojunk=False
    )
    left, right = [], []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        old_part, new_part = _clean(a[i1:i2]), _clean(b[j1:j2])
        if tag == "equal":
            left.append(old_part)
            right.append(new_part)
            continue
        if old_part.strip():
            left.append(f'<span class="del">{old_part}</span>')
        else:
            left.append(old_part)
        if new_part.strip():
            right.append(f'<span class="ins">{new_part}</span>')
        else:
            right.append(new_part)
    return "".join(left), "".join(right)


if __name__ == "__main__":
    sample = "hey can u send me the report asap, need it for [Client]"
    result = rewrite_email(sample, "professional")
    print(result)
    print(analyze_email(sample, result))