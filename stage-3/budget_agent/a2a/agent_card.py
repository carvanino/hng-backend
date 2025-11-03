"""Agent Card definition for Budget Tracker Agent"""

from .schemas import AgentCard, AgentSkill
from typing import Dict, Any


def create_agent_card(base_url: str) -> Dict[str, Any]:
    """
    Create Agent Card for Budget Tracker Agent
    
    Args:
        base_url: Base URL where agent is hosted (e.g., https://abc123.ngrok.io)
    
    Returns:
        Agent Card as dictionary
    """
    card = AgentCard(
        name="Budget Tracker Agent",
        description="AI-powered budget tracking agent that monitors Gmail for transaction alerts and maintains a monthly budget spreadsheet in Google Drive",
        url=f"{base_url}/a2a/agent",
        version="0.1.0",
        skills=[
            AgentSkill(
                name="connect_gmail",
                description="Connect user's Gmail and Google Drive for automatic budget tracking"
            ),
            AgentSkill(
                name="track_transactions",
                description="Monitor Gmail for bank transaction alerts and automatically categorize expenses"
            ),
            AgentSkill(
                name="manage_budget",
                description="Maintain and update monthly budget spreadsheet in user's Google Drive"
            ),
            AgentSkill(
                name="check_status",
                description="Check connection status and budget summary"
            ),
            AgentSkill(
                name="sync_transactions",
                description="Manually trigger sync of recent transactions"
            )
        ],
        authentication=None,  # No auth required for basic interaction
        supportsStreaming=False,
        supportsPushNotifications=True
    )
    
    return card.model_dump()


def get_agent_card_json(base_url: str) -> str:
    """Get Agent Card as JSON string"""
    import json
    return json.dumps(create_agent_card(base_url), indent=2)
