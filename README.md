# Agentic Scraper - Backend

This is the backend for the **Agentic Web Scraper**, an autonomous AI-powered tool designed to navigate websites and extract specific information based on high-level goals.

## 🚀 Features

- **Autonomous Agent**: Powered by Google Gemini to reason about webpage structures and determine next actions.
- **FastAPI Core**: High-performance asynchronous API for job management.
- **Background Processing**: Handles long-running scraping tasks without blocking the API.
- **Browser Automation**: Integration with Playwright for reliable web interaction.
- **Real-time Status**: Track agent thoughts, actions, and results step-by-step.

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **AI Model**: Google Gemini (via LangChain or Direct API)
- **Automation**: Playwright
- **Language**: Python 3.9+

## ⚙️ Setup & Installation

1. **Clone the repository**
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment Variables**:
   Create a `.env` file in the root directory (refer to `.env.example`):
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```
5. **Run the server**:
   ```bash
   python main.py
   ```

## 📡 API Endpoints

- `POST /scrape`: Launch a new scraping job.
- `GET /status/{job_id}`: Get detailed progress of a specific job.
- `GET /jobs`: List all active/completed jobs.
- `DELETE /jobs`: Clear job history.

## 📄 License

MIT
