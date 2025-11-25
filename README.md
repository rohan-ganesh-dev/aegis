# Aegis - Multi-Agent Enterprise AI Concierge

🛡️ **Aegis** is a multi-agent enterprise AI concierge built on Google ADK (Agent Development Kit). It provides intelligent, automated assistance for customer onboarding, integrations, operations, and growth.

> ⚠️ **BOILERPLATE REPOSITORY**: This is a hackathon MVP scaffold with stub implementations and mock data. No production logic, API keys, or real integrations are included. All external calls return deterministic mock responses.

## 🏗️ Architecture

Aegis uses a supervisor-specialist agent pattern:

- **Supervisor Agent (Agent0)**: Central orchestrator that classifies intents and routes tasks to specialist agents
- **Onboarding Agent (Agent1)**: RAG-powered documentation retrieval, migration planning, sandbox provisioning
- **Integration Agent (Agent2)**: Integration marketplace, gateway configuration, code generation
- **Proactive Agent (Agent3)**: Billing monitoring, platform status tracking, support analytics
- **Growth Agent (Agent4)**: Churn prediction, retention perks (with HIL approval), upsell identification

### Agent Communication

Agents communicate via a message transport layer (in-memory for development, Redis adapter for production). Each agent can:
- Receive messages from the supervisor or other agents
- Process tasks asynchronously
- Return structured responses with actions and attachments

### Human-in-Loop (HIL)

High-value actions (e.g., applying discounts, issuing credits) require human approval via:
- **Streamlit Dashboard**: Visual interface for reviewing and approving requests
- **FastAPI HIL API**: REST endpoints for programmatic approval workflows

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip or poetry

### Installation

```bash
# Clone the repository
cd aegis

# Install dependencies
pip install -r requirements.txt

# Or use poetry
poetry install
```

### Running Locally

#### 1. Run Supervisor Demo

```bash
python -m aegis.cli.run_supervisor
```

This will:
- Start the supervisor and all specialist agents
- Send sample tasks through the system
- Log routing decisions and agent responses

#### 2. Run HIL Dashboard

```bash
streamlit run aegis/hil/dashboard.py
```

Open http://localhost:8501 to see the approval interface.

#### 3. Run HIL API

```bash
python aegis/hil/api.py
```

API will be available at http://localhost:8001. View docs at http://localhost:8001/docs.

### Using Docker

```bash
# Build the image
docker build -t aegis:latest .

# Run with docker-compose
docker-compose up
```

Services:
- Supervisor: Runs agent demo
- HIL Dashboard: http://localhost:8501
- HIL API: http://localhost:8001

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_imports.py -v

# Run with coverage
pytest --cov=aegis tests/
```

## 🛠️ Development

### Code Quality

```bash
# Format code
black aegis/ tests/
isort aegis/ tests/

# Type checking
mypy aegis/

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

### Project Structure

```
aegis/
├── agents/           # Agent implementations (supervisor + specialists)
├── tools/            # Mock tools and API clients
├── transports/       # Message transport layer
├── hil/              # Human-in-loop dashboard and API
├── cli/              # CLI runners
└── config.py         # Configuration management

tests/                # Test suite
docs/                 # Documentation
```

## 📋 TODO: Production Implementation

This repository contains **boilerplate only**. For production deployment, implement:

### Core Infrastructure
- [ ] Replace in-memory transport with Redis for multi-process communication
- [ ] Integrate real vector database (Qdrant, Pinecone) for RAG
- [ ] Set up persistent storage for customer contexts (PostgreSQL, Redis)
- [ ] Configure Google ADK with Gemini API credentials

### Agent Logic
- [ ] Implement real intent classification using Gemini 2.5 Pro
- [ ] Build RAG pipeline with document embeddings
- [ ] Integrate with actual billing system (Chargebee, Stripe)
- [ ] Connect to support ticketing (Zendesk, Intercom)
- [ ] Implement ML-based churn prediction model
- [ ] Build sandbox provisioning with real infrastructure API

### HIL & Monitoring
- [ ] Persist HIL approval requests to database
- [ ] Implement agent callback system for approved actions
- [ ] Add authentication and authorization to HIL dashboard
- [ ] Set up monitoring and alerting (Datadog, Prometheus)
- [ ] Implement audit logging for all agent actions

### Security
- [ ] Replace all placeholder API keys with secrets management (Google Secret Manager)
- [ ] Add input validation and sanitization
- [ ] Implement rate limiting and abuse prevention
- [ ] Set up RBAC for HIL approvals
- [ ] Enable encryption for sensitive data

## 📖 Documentation

- [Message Schema Examples](docs/messages.md) - Example agent-to-agent messages
- [HIL API Schema](docs/hil_api_schema.yaml) - OpenAPI spec for HIL endpoints

## 🎯 Hackathon Next Steps

1. **Pick a vertical**: Choose one specialist agent to flesh out (e.g., onboarding)
2. **Add real LLM calls**: Integrate Gemini API for intent classification or RAG
3. **Build a demo flow**: Create an end-to-end workflow from user query to HIL approval
4. **Add UI**: Enhance the Streamlit dashboard with customer-facing chat interface
5. **Implement one integration**: Connect to a real API (e.g., Slack notifications)

## 🤝 Contributing

This is a boilerplate project. Fork and extend as needed for your use case.

## 📄 License

MIT License - see LICENSE file for details

---

**Made with ❤️ for Enterprise AI**
