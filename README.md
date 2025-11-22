# AI Research Suite

A modern, full-stack application designed to transform dense research papers into engaging audiobooks using AI. This tool serves as the foundation for a broader suite of AI-powered research utilities.

## Features

*   **Research to Audiobook:** Upload any research paper (PDF), and the system intelligently summarizes it and converts it into a high-quality MP3 audiobook.
*   **Async Processing:** Built with Celery and Redis to handle multiple long-running conversions simultaneously without blocking the UI.
*   **Real-time Queue System:**
    *   **Active Queue:** Monitor conversions in real-time with status updates.
    *   **Audiobook Library:** Persistent history of your converted files with options to download or manage them.
*   **Modern UI/UX:** A clean, responsive interface with a split-screen login page and a central services dashboard.
*   **Robust Error Handling:** Graceful handling of uploads, cancellations, and file cleanup.

## Tech Stack

*   **Frontend:** HTML5, CSS3 (Modern/Clean), Vanilla JavaScript (ES6+)
*   **Backend:** Python, Flask
*   **Task Queue:** Celery, Redis
*   **AI Engine:** OpenAI API
    *   `gpt-5-mini` (or similar) for summarization
    *   `tts-1` (Shimmer voice) for text-to-speech
*   **Containerization:** Docker, Docker Compose

## Prerequisites

*   [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running.
*   An [OpenAI API Key](https://platform.openai.com/) with access to GPT-4 and TTS models.

## Quick Start

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/research-paper-to-audiobook.git
    cd research-paper-to-audiobook
    ```

2.  **Configure Environment:**
    Create a `.env` file in the root directory:
    ```env
    OPENAI_API_KEY=sk-your-openai-api-key-here
    password=your_login_password
    ```

3.  **Build and Run:**
    ```bash
    docker-compose up --build
    ```

4.  **Access the App:**
    Open your browser and navigate to:
    `http://localhost:5000`

    *   **Login:** Use `rob.roskowski@gmail.com` (default in `config.py`) and the password you set in `.env`.

## Project Structure

```
├── app/
│   ├── agent/          # AI Logic (OpenAI wrapper)
│   ├── static/         # CSS & JS files
│   ├── templates/      # HTML templates (Login, Dashboard, Tools)
│   ├── __init__.py     # Flask App Factory & Celery Config
│   ├── routes.py       # API Routes & Views
│   └── tasks.py        # Celery Background Tasks
├── uploads/            # Temp storage for papers & MP3s (cleared on startup)
├── docker-compose.yml  # Orchestration for Web, Worker, and Redis
├── Dockerfile          # App environment definition
├── main.py             # Entry point
└── requirements.txt    # Python dependencies
```

## Roadmap

*   [x] **Research to Audiobook** (Live)
*   [ ] **Research to YouTube Video** (Coming Soon) - Generate video scripts and visuals from papers.
*   [ ] **YouTube to Summary** (Coming Soon) - Summarize long technical videos.
*   [ ] **Data Extractor** (Coming Soon) - Extract tables and charts into Excel.
*   [ ] **User Accounts** - Database integration for multi-user support.
*   [ ] **Payments** - Stripe integration for premium features.

## License

MIT License. Feel free to use and modify for your own projects.

