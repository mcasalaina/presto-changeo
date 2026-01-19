# Presto-Change-O

An AI-powered multi-industry simulation dashboard. Say "Presto-Change-O, you're a bank" and watch the entire interface transform — colors, charts, data, and behavior — to simulate that industry.

## Features

- **Chat Interface**: Left-panel chat with streaming AI responses
- **Industry Modes**: Banking, Insurance, Healthcare (more coming)
- **Dynamic Theming**: Colors and UI adapt to each industry
- **Voice Integration**: Toggle-mode voice interaction (planned)
- **LLM-Driven**: All interactions powered by Azure AI

## Tech Stack

- **Frontend**: React 19 + TypeScript + Vite
- **Backend**: Python + FastAPI + WebSocket
- **AI**: Azure AI Foundry (gpt-5-mini)
- **Auth**: Azure CLI / Interactive Browser

## Prerequisites

- Node.js 18+
- Python 3.11+
- Azure CLI (`az login` for authentication)
- Access to Azure AI Foundry project

## Setup

### Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env`:
```
AZURE_PROJECT_ENDPOINT=https://your-project.services.ai.azure.com/models
AZURE_MODEL_DEPLOYMENT=gpt-5-mini
```

### Frontend

```bash
cd frontend
npm install
```

## Running

### 1. Login to Azure (once per session)

```bash
az login
```

### 2. Start Backend

```bash
cd backend
python -m uvicorn main:app --reload
```

Server runs at http://localhost:8000

### 3. Start Frontend

```bash
cd frontend
npm run dev
```

App runs at http://localhost:5173

## Project Structure

```
presto-changeo/
├── backend/
│   ├── main.py          # FastAPI app + WebSocket endpoint
│   ├── chat.py          # LLM chat handler with streaming
│   ├── auth.py          # Azure authentication
│   └── .env             # Configuration (not committed)
├── frontend/
│   ├── src/
│   │   ├── App.tsx      # Main app component
│   │   ├── hooks/       # React hooks (useWebSocket)
│   │   ├── lib/         # WebSocket utilities
│   │   └── components/  # UI components
│   └── package.json
└── .planning/           # Project planning docs
```

## Development

### Build Frontend
```bash
cd frontend && npm run build
```

### Lint Frontend
```bash
cd frontend && npm run lint
```

## License

Private - All rights reserved
