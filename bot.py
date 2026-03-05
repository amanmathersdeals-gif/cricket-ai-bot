import requests
import time
import telegram
import asyncio
from openai import OpenAI

# -----------------------------
# CONFIGURATION
# -----------------------------

BOT_TOKEN = "8534858024:AAH0BbyR8jnS66geUaE8HXpcwJTP6-P69o0"
CHAT_ID = "8796376997"
CRIC_API_KEY = "d4c0cebd-1ee3-405a-b91b-4a36ece300ce"
DEEPSEEK_API_KEY = "sk-aefd1387ceb44364a218037f79a215be"

# -----------------------------
# INITIALIZE SERVICES
# -----------------------------

bot = telegram.Bot(token=BOT_TOKEN)

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

last_score = ""

# -----------------------------
# GET MATCH SCORE
# -----------------------------

def get_score():

    url = f"https://api.cricapi.com/v1/currentMatches?apikey={CRIC_API_KEY}&offset=0"

    r = requests.get(url)
    data = r.json()

    for match in data["data"]:

        if "India" in match["name"] and "England" in match["name"]:

            score = match["score"]

            return str(score)

    return None


# -----------------------------
# AI ANALYSIS
# -----------------------------

def ai_insight(score):

    try:

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    Analyze this cricket match situation.

                    Score:
                    {score}

                    Provide short insights:

                    - Which team has momentum
                    - Predicted final score
                    - Key tactical insight
                    """
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:

        print("Error generating AI insight:", e)

        return "AI insight unavailable."


# -----------------------------
# TELEGRAM MESSAGE
# -----------------------------

import asyncio

def send_update(score):

    insight = ai_insight(score)

    message = f"""
🏏 Live Match Update

{score}

🧠 AI Insight

{insight}
"""

    async def send_message_async():
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message
        )

    asyncio.run(send_message_async())


# -----------------------------
# MAIN LOOP
# -----------------------------

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
