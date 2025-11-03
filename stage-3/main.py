"""FastAPI application - A2A-compliant Budget Tracker Agent"""

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from google_auth_oauthlib.flow import Flow
from contextlib import asynccontextmanager
from config import get_settings
from budget_agent.agent import BudgetAgent
from budget_agent.core import UserStore
from budget_agent.a2a import A2AProtocolHandler, create_agent_card
import logging
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Settings
settings = get_settings()

# Global instances
user_store = None
budget_agent = None
a2a_handler = None
BASE_URL = None  # Will be set from first request


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager"""
    global user_store, budget_agent, a2a_handler
    
    logger.info("Starting Budget Tracker Agent (A2A Protocol)...")
    
    # Initialize Firestore
    user_store = UserStore(settings.firebase_credentials_path)
    
    # Note: BASE_URL will be determined from first request
    # For now, initialize with placeholder
    budget_agent = BudgetAgent(user_store, settings.gemini_api_key, "https://dffec538518c.ngrok-free.app")
    
    # Initialize A2A protocol handler
    a2a_handler = A2AProtocolHandler(budget_agent, user_store)
    
    logger.info("Agent initialized successfully")
    
    yield
    
    logger.info("Agent shutdown complete")


# FastAPI app
app = FastAPI(
    title="Budget Tracker Agent",
    description="A2A-compliant AI budget tracking agent",
    version="0.1.0",
    lifespan=lifespan
)


@app.middleware("http")
async def set_base_url(request: Request, call_next):
    """Middleware to capture base URL from requests"""
    global BASE_URL, budget_agent
    
    if BASE_URL is None:
        # Determine base URL from first request
        scheme = request.url.scheme
        host = request.headers.get('host', request.client.host)
        BASE_URL = f"{scheme}://{host}"
        
        # Update budget agent with actual base URL
        if budget_agent:
            budget_agent.base_url = BASE_URL
        
        logger.info(f"Base URL set to: {BASE_URL}")
    
    response = await call_next(request)
    return response


@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "healthy",
        "service": "Budget Tracker Agent",
        "protocol": "A2A",
        "version": "0.1.0"
    }


@app.get("/.well-known/agent.json")
async def agent_card(request: Request):
    """
    Agent Card endpoint for A2A discovery
    Required by A2A protocol
    """
    base_url = f"{request.url.scheme}://{request.headers.get('host')}"
    card = create_agent_card(base_url)
    
    return JSONResponse(content=card)


@app.post("/a2a/agent")
async def a2a_endpoint(request: Request):
    """
    Main A2A protocol endpoint
    Handles JSON-RPC 2.0 requests from Telex
    """
    try:
        # Parse request body
        body = await request.json()
        logger.info(f"A2A Request: {body}")
        
        # Handle with protocol handler
        response = await a2a_handler.handle_request(body)
        
        logger.info(f"A2A Response: {response}")
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"A2A endpoint error: {e}")
        
        # Return JSON-RPC error
        error_response = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }
        return JSONResponse(content=error_response, status_code=500)


@app.get("/oauth/authorize")
async def oauth_authorize(user_id: str = Query(...)):
    """
    Start OAuth flow for user
    
    Args:
        user_id: User identifier from Telex (contextId)
    """
    try:
        # Create OAuth flow
        print("SETTINGS -____-", settings)
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.google_redirect_uri]
                }
            },
            scopes=[
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/drive.file',
                'https://www.googleapis.com/auth/gmail.modify'
            ]
        )
        
        flow.redirect_uri = settings.google_redirect_uri
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=user_id,  # Pass user_id in state
            prompt='consent'
        )
        
        logger.info(f"Generated OAuth URL for user {user_id}")
        
        return RedirectResponse(url=authorization_url)
        
    except Exception as e:
        logger.error(f"OAuth authorize error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/oauth/callback")
async def oauth_callback(code: str = Query(...), state: str = Query(...)):
    """
    OAuth callback handler
    
    Args:
        code: Authorization code
        state: User ID passed from authorize
    """
    try:
        user_id = state
        
        # Exchange code for tokens
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.google_redirect_uri]
                }
            },
            scopes=[
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/drive.file',
                'https://www.googleapis.com/auth/gmail.modify',
            ],
            state=state
        )
        
        flow.redirect_uri = settings.google_redirect_uri
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        # Complete setup (this will also send a proactive message to the user)
        message = await budget_agent.complete_oauth_setup(user_id, credentials)
        
        return HTMLResponse(f"""
            <html>
                <body>
                    <h1>✅ Authorization Successful!</h1>
                    <p>{message}</p>
                    <p>You can close this window and return to Telex.</p>
                </body>
            </html>
        """)
        
    except Exception as e: 
        logger.error(f"OAuth callback error: {e}")
        return HTMLResponse(f"""
            <html>
                <body>
                    <h1>❌ Authorization Failed</h1>
                    <p>Error: {str(e)}</p>
                </body>
            </html>
        """, status_code=500)


@app.get("/user/{user_id}/status")
async def user_status(user_id: str):
    """Check user connection status (for debugging)"""
    try:
        is_connected = user_store.is_user_connected(user_id)
        
        data = {
            "user_id": user_id,
            "connected": is_connected
        }
        
        if is_connected:
            file_id = user_store.get_drive_file_id(user_id)
            data["drive_file_id"] = file_id
        
        return data
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
