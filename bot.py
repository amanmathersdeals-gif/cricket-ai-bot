import os
import time
import requests
from openai import OpenAI
import telegram  # ensure this matches your installed package!

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CRIC_API_KEY = os.getenv("CRIC_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

missing = [k for k, v in {
    "BOT_TOKEN": BOT_TOKEN,
    "CHAT_ID": CHAT_ID,
    "CRIC_API_KEY": CRIC_API_KEY,
    "OPENROUTER_API_KEY": OPENROUTER_API_KEY
}.items() if not v]

if missing:
    raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

bot = telegram.Bot(token=BOT_TOKEN)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

last_score = None


def format_score(score_obj):
    """Turn score object into readable text."""
    if score_obj is None:
        return "Score unavailable"

    # If API returns list of innings dicts
    if isinstance(score_obj, list):
        parts = []
        for inn in score_obj:
            team = inn.get("inning", "Innings")
            r = inn.get("r", "?")
            w = inn.get("w", "?")
            o = inn.get("o", "?")
            parts.append(f"{team}: {r}/{w} ({o} ov)")
        return "\n".join(parts) if parts else str(score_obj)

    return str(score_obj)


def get_score():
    url = f"https://api.cricapi.com/v1/currentMatches?apikey={CRIC_API_KEY}&offset=0"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()

    matches = data.get("data") or []
    for match in matches:
        name = match.get("name", "")
        if "India" in name and "England" in name:
            return format_score(match.get("score"))

    return None


def ai_insight(score_text):
    try:
        resp = client.chat.completions.create(
            model="arcee-ai/trinity-large-preview:free",
            messages=[{
                "role": "user",
                "content": (
                    "Analyze this cricket match situation.\n\n"
                    f"Score:\n{score_text}\n\n"
                    "Provide short insights:\n"
                    "- Which team has momentum\n"
                    "- Predicted final score\n"
                    "- Key tactical insight"
                )
            }],
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print("AI Error:", e)
        return "AI insight unavailable."


def send_update(score_text):
    insight = ai_insight(score_text)
    message = (
        "🏏 Live Match Update\n\n"
        f"{score_text}\n\n"
        "🧠 AI Insight\n\n"
        f"{insight}"
    )
    # sync send (common in some telegram libs)
    bot.send_message(chat_id=CHAT_ID, text=message)


while True:
    try:
        score = get_score()
        if score and score != last_score:
            send_update(score)
            last_score = score
        time.sleep(300)
    except Exception as e:
        print("Error:", e)
        time.sleep(60)