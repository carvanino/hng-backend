# Budget Tracker AI Agent (A2A Protocol)

An intelligent budget tracking agent that monitors Gmail for transaction notifications, categorizes expenses automatically using Gemini AI, and maintains a monthly budget spreadsheet in Google Drive. Fully compliant with the A2A (Agent-to-Agent) protocol for integration with Telex.im.

## Features

- 📧 **Gmail Integration**: Monitors inbox for bank transaction alerts
- 🤖 **Smart Categorization**: Uses Google Gemini to intelligently categorize expenses
- 📊 **Google Drive Storage**: Maintains Excel budget tracker in user's Drive
- 💬 **Telex.im Integration**: A2A protocol compliant conversational interface
- 🔐 **Secure OAuth**: Users grant access to their own Gmail and Drive

## Architecture (A2A Protocol)

```
Telex.im → A2A JSON-RPC Request → Budget Agent
                                        ↓
                          Process with Gmail/Drive/Gemini
                                        ↓
Budget Agent → A2A JSON-RPC Response → Telex.im
```

## Tech Stack

- **Backend**: Python 3.10+, FastAPI
- **Protocol**: A2A (JSON-RPC 2.0)
- **Storage**: Google Drive (Excel), Firebase/Firestore (user data)
- **APIs**: Gmail API, Drive API, Gemini API
- **OAuth**: Google OAuth 2.0

## Setup

### Prerequisites

1. **Google Cloud Project** with Gmail API and Drive API enabled
2. **OAuth 2.0 Web Application credentials**
3. **Firebase project** with Firestore enabled
4. **Gemini API key** (free tier available)
5. **Telex.im AI Coworker** created

### Installation

1. Navigate to project:
```bash
cd stage-3
source bin/activate
```

2. Install dependencies (already done):
```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env`:
```bash
# Copy from .env.example and fill in:
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/callback
FIREBASE_CREDENTIALS_PATH=config/firebase-credentials.json
GEMINI_API_KEY=your_gemini_api_key
```

4. Add credentials:
- Place Firebase service account JSON in `config/firebase-credentials.json`

### Running the Agent

1. Start FastAPI server:
```bash
python main.py
```

2. Expose with ngrok (for Telex integration):
```bash
ngrok http 8000
```

3. Configure Telex Workflow:
   - Copy your ngrok URL (e.g., `https://abc123.ngrok.io`)
   - Edit `telex_workflow.json`
   - Replace `YOUR_NGROK_URL` with your actual ngrok URL
   - Paste the JSON into your Telex AI Coworker workflow configuration

## Telex Integration

### Workflow JSON Configuration

In your Telex AI Coworker dashboard:

1. Go to Workflow configuration
2. Paste this JSON (update the URL):

```json
{
  "nodes": [
    {
      "id": "budget_tracker_agent",
      "name": "Budget Tracker Agent",
      "type": "a2a/generic-a2a-node",
      "typeVersion": 1,
      "url": "https://YOUR_NGROK_URL/a2a/agent",
      "parameters": {},
      "position": [400, 300]
    }
  ],
  "settings": {
    "executionOrder": "v1"
  }
}
```

3. Save and test

### Agent Discovery

The agent exposes an Agent Card at:
```
https://YOUR_NGROK_URL/.well-known/agent.json
```

This allows Telex to discover the agent's capabilities automatically.

## Usage

### User Flow on Telex

1. **User**: "connect"
   - **Agent**: Provides OAuth link to authorize Gmail & Drive

2. **User clicks link** → Authorizes access
   - **Agent**: Creates budget tracker in user's Drive, starts monitoring

3. **User receives bank alert** in Gmail
   - **Agent**: Automatically parses, categorizes, and logs in budget

4. **User**: "status"
   - **Agent**: Shows connection status and budget link

5. **User**: "sync"
   - **Agent**: Manually processes recent transactions

### Available Commands

- `connect` - Link Gmail and Google Drive
- `status` - Check connection and budget status  
- `sync` - Manually process transactions
- `help` - Show available commands

## A2A Protocol Endpoints

### Core Endpoints

- `POST /a2a/agent` - Main A2A JSON-RPC endpoint
- `GET /.well-known/agent.json` - Agent Card (discovery)
- `GET /` - Health check

### OAuth Endpoints

- `GET /oauth/authorize?user_id={user_id}` - Start OAuth flow
- `GET /oauth/callback` - OAuth callback handler

### Debug Endpoints

- `GET /user/{user_id}/status` - Check user connection status

## A2A Protocol Structure

### Request Example (from Telex):
```json
{
  "jsonrpc": "2.0",
  "id": "req-123",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{"kind": "text", "text": "connect"}]
    }
  }
}
```

### Response Example:
```json
{
  "jsonrpc": "2.0",
  "id": "req-123",
  "result": {
    "id": "task-456",
    "status": {
      "state": "completed"
    },
    "message": {
      "role": "agent",
      "parts": [{"kind": "text", "text": "Click here to connect..."}]
    }
  }
}
```

## Project Structure

```
stage-3/
├── budget_agent/
│   ├── a2a/
│   │   ├── agent_card.py      # Agent Card definition
│   │   ├── protocol.py         # JSON-RPC handler
│   │   └── schemas.py          # A2A data models
│   ├── core/
│   │   ├── gmail_monitor.py
│   │   ├── transaction_parser.py
│   │   ├── category_classifier.py
│   │   ├── excel_manager.py
│   │   └── user_store.py
│   └── agent.py                # Main orchestrator
├── config/
│   ├── settings.py
│   └── firebase-credentials.json
├── data/
├── main.py
├── telex_workflow.json
├── requirements.txt
└── README.md
```

## Testing

### Local Testing

1. **Health check:**
```bash
curl http://localhost:8000/
```

2. **Agent Card:**
```bash
curl http://localhost:8000/.well-known/agent.json
```

3. **A2A Request (simulate Telex):**
```bash
curl -X POST http://localhost:8000/a2a/agent \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-1",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "help"}]
      }
    }
  }'
```

### With Telex

1. Ensure ngrok is running
2. Update workflow JSON with ngrok URL
3. Message your AI Coworker on Telex
4. Check logs at: `https://api.telex.im/agent-logs/{channel-id}.txt`

## Troubleshooting

**Agent not responding on Telex:**
- Check ngrok is running and URL is correct in workflow
- Verify Agent Card is accessible: `curl https://your-ngrok-url/.well-known/agent.json`
- Check Telex agent logs

**OAuth failing:**
- Verify Google OAuth credentials are correct
- Ensure redirect URI matches: `http://localhost:8000/oauth/callback`
- Check Firebase credentials are valid

**Transactions not being tracked:**
- Verify user completed OAuth flow
- Check Gmail API permissions granted
- Test with `sync` command to force check

## License

MIT

## Author

HNG Stage 3 Backend Task - A2A Protocol Implementation
