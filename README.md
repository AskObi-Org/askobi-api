# AskObi Backend API

<p align="center">
  <strong>AI-driven health intelligence platform</strong><br>
  Democratizing access to accurate medical symptom analysis
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#api-documentation">API Docs</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## Overview

AskObi is an intelligent health platform that leverages AI to provide accurate medical symptom analysis, making healthcare information accessible to everyone.

## Features

- 🩺 **Symptom Analysis** - AI-powered symptom evaluation and insights
- 🔒 **Secure & Private** - HIPAA-compliant data handling
- ⚡ **Fast Response** - Real-time analysis with minimal latency
- 🌍 **Accessible** - Democratizing health information globally

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework for building APIs
- **Language**: Python 3.11+
- **Documentation**: OpenAPI (Swagger UI & ReDoc)

## Getting Started

### Prerequisites

- Python 3.11 or higher
- pip or uv package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AskObi-Org/askobi-api.git
   cd askobi-api
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the development server**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Project Structure

```
askobi-api/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application entry point
│   ├── api/              # API routes
│   ├── core/             # Core configurations
│   ├── models/           # Pydantic models
│   ├── services/         # Business logic
│   └── utils/            # Utility functions
├── tests/                # Test suite
├── requirements.txt
├── .env.example
└── README.md
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
# Format code
black .
ruff check --fix .
```

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting a pull request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary software. All rights reserved.

---

<p align="center">
  Made with ❤️ by the AskObi Team
</p>

