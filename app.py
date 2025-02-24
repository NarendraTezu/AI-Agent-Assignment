"""
AI Agent Application
--------------------
This Quart-based AI agent performs two core functions:
1. Fetches cryptocurrency prices using the CoinGecko API.
2. Handles language translation requests while maintaining English as the response language.

Key Features:
-------------
- Utilizes Together AI's LLaMA 3.1 8B model for natural language processing.
- Implements conversation context maintenance using Redis.
- Provides rate limiting per user to prevent abuse.
- Caches API responses to improve efficiency.
- Ensures system responses are always in English, even if the input is in another language.

Dependencies:
-------------
- quart
- aiocache
- aioredis
- aiohttp
- python-dotenv
- together

Run Instructions:
-----------------
1. Install dependencies: `pip install -r requirements.txt`
2. Set `TOGETHER_API_KEY` in your `.env` file.
3. Start Redis server on `localhost`.
4. Run the application: `python app.py`
5. Access via POST requests to `/agent`.

"""

import os
import asyncio
import aiocache
import aioredis
import aiohttp
import logging
import time
from dotenv import load_dotenv
from quart import Quart, request, jsonify, send_from_directory
from together import Together

# -------------------------------
# Environment and API Setup
# -------------------------------

# Load API key from environment
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
if not TOGETHER_API_KEY:
    raise ValueError("TOGETHER_API_KEY is not set in the environment")

# Initialize Together AI client
client = Together(api_key=TOGETHER_API_KEY)

# Initialize Quart app
app = Quart(__name__)

# -------------------------------
# Redis Initialization
# -------------------------------
redis = None

async def init_redis():
    """Initializes Redis connection for caching, rate limiting, and chat history."""
    global redis
    redis = await aioredis.from_url("redis://localhost", decode_responses=True)

# -------------------------------
# Rate Limiting
# -------------------------------
REQUEST_LIMIT = 5  # Max requests per user
TIME_FRAME = 60    # Time frame in seconds

async def rate_limited(user_id: str) -> bool:
    """Enforces per-user rate limiting."""
    current_time = time.time()
    key = f"rate_limit:{user_id}"

    try:
        async with redis.pipeline() as pipe:
            pipe.lrange(key, 0, -1)
            requests = await pipe.execute()
            requests = [float(t) for t in requests[0] if current_time - float(t) < TIME_FRAME]

            if len(requests) >= REQUEST_LIMIT:
                return False

            pipe.rpush(key, current_time)
            pipe.ltrim(key, -REQUEST_LIMIT, -1)
            pipe.expire(key, TIME_FRAME)
            await pipe.execute()

        return True
    except Exception as e:
        logging.error(f"Rate limiting error: {e}")
        return False

# -------------------------------
# Chat History Management
# -------------------------------

async def update_chat_history(user_id: str, user_message: str, assistant_response: str):
    """Stores the last 10 messages for a user."""
    key = f"history:{user_id}"
    await redis.rpush(key, f"User: {user_message}", f"AI: {assistant_response}")
    await redis.ltrim(key, -10, -1)

async def get_chat_history(user_id: str):
    """Retrieves the last 10 messages from Redis."""
    return await redis.lrange(f"history:{user_id}", 0, -1) or []

# -------------------------------
# Cryptocurrency Price Fetching
# -------------------------------

@aiocache.cached(ttl=30, cache=aiocache.SimpleMemoryCache)
async def fetch_crypto_price(crypto_name: str) -> str:
    """Fetches the current price of a cryptocurrency from CoinGecko."""
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_name.lower()}&vs_currencies=usd"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                if response.status != 200:
                    return f"Failed to fetch {crypto_name} price."
                
                data = await response.json()
                price = data.get(crypto_name.lower(), {}).get("usd")
                return f"The current price of {crypto_name.capitalize()} is ${price}" if price else f"Price for {crypto_name} not found."

    except Exception as e:
        logging.error(f"Error fetching {crypto_name} price: {e}")
        return "Error fetching price."

# -------------------------------
# English-Only AI Responses
# -------------------------------

async def enforce_english_response(user_id: str, user_input: str) -> str:
    """Ensures responses are always in English with conversation context."""
    history = await get_chat_history(user_id)
    messages = [{"role": "system", "content": "Respond in English and retain conversation context."}]

    for message in history:
        role, content = message.split(": ", 1)
        messages.append({"role": "user" if role == "User" else "assistant", "content": content})

    messages.append({"role": "user", "content": user_input})

    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo-128K",
            messages=messages
        )
        assistant_response = response.choices[0].message.content
        await update_chat_history(user_id, user_input, assistant_response)
        return assistant_response
    except Exception as e:
        logging.error(f"AI response error: {e}")
        return "I encountered an issue. Please try again."

# -------------------------------
# Main AI Agent Route
# -------------------------------

@app.route("/agent", methods=["POST"])
async def ai_agent():
    """Main endpoint to handle user queries."""
    data = await request.get_json()
    user_id = data.get("user_id")
    action = data.get("action", "").lower()
    user_message = data.get("text", "")

    if not user_id:
        return jsonify({"response": "Missing user_id."}), 400

    if not await rate_limited(user_id):
        return jsonify({"response": "Rate limit exceeded."}), 429

    if "price" in action:
        crypto_name = action.replace("price of", "").strip()
        return jsonify({"response": await fetch_crypto_price(crypto_name)})

    if action == "translate":
        return jsonify({"response": await enforce_english_response(user_id, user_message)})

    return jsonify({"response": await enforce_english_response(user_id, user_message)})

# -------------------------------
# Server Initialization
# -------------------------------

if __name__ == "__main__":
    asyncio.run(init_redis())
    app.run(debug=True)
