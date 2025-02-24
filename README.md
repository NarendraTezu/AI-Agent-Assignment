# AI Agent with Quart, Together AI, and Redis

This AI agent is a Flask-compatible asynchronous web service built using Quart. It provides two main functionalities:

- Fetching the current Bitcoin price from CoinGecko.
- Translating text while ensuring the response remains in English.

The project integrates Together AI's language model, Redis for rate limiting and conversation context storage, and aiocache for caching Bitcoin prices.

## Features

- **Asynchronous API Handling**: Uses `Quart` for handling asynchronous API requests.
- **Rate Limiting**: Prevents excessive API requests using Redis.
- **Caching**: Caches Bitcoin prices for 30 seconds to reduce API calls.
- **Translation**: Uses Together AI to translate text while ensuring responses remain in English.
- **Error Handling**: Implements robust exception handling for API failures.

## Prerequisites

Ensure you have the following installed:

- Python 3.8+
- Redis (Running on `localhost`)
- `pip` for dependency management

## Installation

1. **Clone the repository:**
   ```sh
   git clone <repository-url>
   cd <repository-folder>
   ```
2. **Create a virtual environment (optional but recommended):**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Set up environment variables:**
   Create a `.env` file in the project root and add:
   ```sh
   TOGETHER_API_KEY=your_together_ai_api_key
   ```
   Replace `your_together_ai_api_key` with your actual Together AI API key.

## Running the Application

1. **Ensure Redis is running:**
   ```sh
   redis-server
   ```
2. **Start the AI Agent:**
   ```sh
   python app.py
   ```
3. **Make API Requests:**
   Use a tool like `curl` or Postman to send requests.

   - **Fetch Bitcoin price:**
     ```sh
     curl -X POST http://127.0.0.1:5000/agent -H "Content-Type: application/json" -d '{"user_id": "123", "action": "price"}'
     ```
   - **Translate text:**
     ```sh
     curl -X POST http://127.0.0.1:5000/agent -H "Content-Type: application/json" -d '{"user_id": "123", "action": "translate", "text": "Hola, cómo estás?", "target_language": "English"}'
     ```

## Notes

- The AI agent enforces English-only responses.
- Rate limiting restricts users to **5 requests per minute**.
- Cached Bitcoin price updates every **30 seconds**.

## Troubleshooting

- **Redis not found?** Ensure Redis is installed and running (`redis-server`).
- **API key errors?** Double-check your `.env` file setup.
- **Async issues?** Try running the server in a Python virtual environment.