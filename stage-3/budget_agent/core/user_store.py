"""Firestore user data management"""

import firebase_admin
from firebase_admin import credentials, firestore
from google.oauth2.credentials import Credentials
from typing import Optional, Dict
import logging
import json

logger = logging.getLogger(__name__)


class UserStore:
    """Manage user data in Firestore"""
    
    _initialized = False
    
    def __init__(self, credentials_path: str):
        """Initialize Firestore"""
        if not UserStore._initialized:
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)
            UserStore._initialized = True
        
        self.db = firestore.client()
        self.users_ref = self.db.collection('users')
    
    def save_user(self, user_id: str, data: Dict) -> bool:
        """
        Save or update user data
        
        Args:
            user_id: Unique user identifier
            data: User data dictionary
        """
        try:
            self.users_ref.document(user_id).set(data, merge=True)
            logger.info(f"Saved user data for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving user data: {e}")
            return False
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user data"""
        try:
            doc = self.users_ref.document(user_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error getting user data: {e}")
            return None
    
    def save_oauth_tokens(self, user_id: str, credentials: Credentials) -> bool:
        """
        Save OAuth tokens for user
        
        Args:
            user_id: User identifier
            credentials: Google OAuth credentials object
        """
        try:
            token_data = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            
            self.users_ref.document(user_id).set({
                'oauth_tokens': token_data
            }, merge=True)
            
            logger.info(f"Saved OAuth tokens for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving OAuth tokens: {e}")
            return False
    
    def get_credentials(self, user_id: str) -> Optional[Credentials]:
        """
        Retrieve OAuth credentials for user
        
        Returns:
            Credentials object or None
        """
        try:
            user_data = self.get_user(user_id)
            if not user_data or 'oauth_tokens' not in user_data:
                return None
            
            token_data = user_data['oauth_tokens']
            
            credentials = Credentials(
                token=token_data['token'],
                refresh_token=token_data.get('refresh_token'),
                token_uri=token_data['token_uri'],
                client_id=token_data['client_id'],
                client_secret=token_data['client_secret'],
                scopes=token_data.get('scopes')
            )
            
            return credentials
            
        except Exception as e:
            logger.error(f"Error retrieving credentials: {e}")
            return None
    
    def save_drive_file_id(self, user_id: str, file_id: str) -> bool:
        """Save Google Drive file ID for user's budget tracker"""
        return self.save_user(user_id, {'drive_file_id': file_id})
    
    def get_drive_file_id(self, user_id: str) -> Optional[str]:
        """Get user's budget tracker file ID"""
        user_data = self.get_user(user_id)
        if user_data:
            return user_data.get('drive_file_id')
        return None
    
    def save_telex_channel(self, user_id: str, channel_id: str) -> bool:
        """Save Telex channel ID for user"""
        return self.save_user(user_id, {'telex_channel_id': channel_id})
    
    def get_telex_channel(self, user_id: str) -> Optional[str]:
        """Get user's Telex channel ID"""
        user_data = self.get_user(user_id)
        if user_data:
            return user_data.get('telex_channel_id')
        return None
    
    def is_user_connected(self, user_id: str) -> bool:
        """Check if user has completed OAuth setup"""
        user_data = self.get_user(user_id)
        if not user_data:
            return False
        return 'oauth_tokens' in user_data and 'drive_file_id' in user_data
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user data"""
        try:
            self.users_ref.document(user_id).delete()
            logger.info(f"Deleted user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False

    def save_webhook_config(self, user_id: str, webhook_url: str, token: str) -> bool:
        """Save Telex webhook config for user"""
        logger.info(f"SAVING WEBHOOK URL AND TOKEN")
        return self.save_user(user_id, {
            'webhook_url': webhook_url,
            'webhook_token': token
        })

    def get_webhook_url(self, user_id: str) -> Optional[str]:
        """Get user's Telex webhook URL"""
        user_data = self.get_user(user_id)
        return user_data.get('webhook_url') if user_data else None

    def get_webhook_token(self, user_id: str) -> Optional[str]:
        """Get user's Telex webhook token"""
        user_data = self.get_user(user_id)
        return user_data.get('webhook_token') if user_data else None

    def get_user_id_by_token(self, token: str) -> Optional[str]:
        """Find a user_id by their webhook token."""
        if not token:
            return None
        try:
            # Query for a user with the matching token
            docs = self.users_ref.where('oauth_tokens.token', '==', token).limit(1).stream()
            
            # Return the ID of the first document found
            for doc in docs:
                logger.info(f"Found user {doc.id} for token.")
                return doc.id
            
            # No user found with that token
            logger.info(f"No user found for the provided token.")
            return None
            
        except Exception as e:
            logger.error(f"Error querying user by token: {e}", exc_info=True)
            return None
