<p align="center">
  <h1 align="center">🎓 EduAgent</h1>
  <p align="center"><em>AI-Powered Student Assistant — built with FastAPI + Qwen + MCP</em></p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/fastapi-0.115-teal" alt="FastAPI">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://github.com/XobierWang/EduAgent/actions/workflows/ci.yml/badge.svg" alt="CI">
</p>

---

EduAgent is an intelligent education assistant designed for students and teachers. It provides natural language Q&A for academic records, course materials, and learning progress — powered by LLM tool-calling with a structured memory system.

## ✨ Features

- **Natural Language Q&A** — Ask about grades, assignments, course schedules in plain language
- **Multi-modal Input** — Upload images of problem sets or exam papers for analysis
- **Text-to-Speech** — Voice synthesis for reading answers aloud
- **Identity Verification** — Secure student identity checks before accessing private data
- **Short-term Memory** — Conversation context across multi-turn dialogues
- **Long-term Memory** — Persistent student profiles and key learning events via FAISS vector search
- **MCP Tool Calling** — Extensible agent toolchain for querying student data

## 🚀 Quick Start

```bash
# Clone and enter project
git clone https://github.com/XobierWang/EduAgent.git
cd EduAgent/Agent

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Qwen API key

# Run the server
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/query` in your browser.

## 🧱 Architecture

```
app/
├── api/          FastAPI routes
├── db/           SQLAlchemy models & session
├── llm/          Qwen client, MCP agent, speech synthesis
├── schemas/      Pydantic request/response models
├── services/     Business logic layer
├── static/       Frontend (HTML/CSS/JS)
└── middleware.py Request logging & error handling
```

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| LLM | Qwen (via DashScope) |
| Agent | MCP (Model Context Protocol) |
| Database | SQLite + SQLAlchemy + Alembic |
| Vector Search | FAISS |
| Speech | DashScope TTS |
| Config | pydantic-settings |
| CI | GitHub Actions |

## 📄 License

MIT © XobierWang
