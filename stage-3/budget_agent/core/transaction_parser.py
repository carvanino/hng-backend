"""Transaction parsing from email notifications"""

import re
from typing import Optional, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TransactionParser:
    """Extract transaction details from bank alert emails"""
    
    # Common patterns for Nigerian banks and payment platforms
    DEBIT_PATTERNS = [
        r'debit',
        r'debited',
        r'dr',
        r'withdrawal',
        r'payment',
        r'transfer'
    ]
    
    CREDIT_PATTERNS = [
        r'credit',
        r'credited',
        r'cr',
        r'deposit',
        r'received'
    ]
    
    AMOUNT_PATTERNS = [
        r'NGN\s*([0-9,]+\.?\d*)',
        r'₦\s*([0-9,]+\.?\d*)',
        r'N\s*([0-9,]+\.?\d*)',
        r'amt:\s*([0-9,]+\.?\d*)',
        r'amount:\s*([0-9,]+\.?\d*)',
        r'([0-9,]+\.?\d*)\s*naira'
    ]
    
    def parse(self, email_data: Dict) -> Optional[Dict]:
        """
        Parse email for transaction details
        
        Args:
            email_data: Dictionary with 'subject', 'body', 'sender', 'date'
            
        Returns:
            Dict with transaction details or None if not a transaction
        """
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        text = f"{subject} {body}"
        
        # Check if this looks like a transaction alert
        if not self._is_transaction_alert(text):
            logger.debug(f"Not a transaction alert: {email_data.get('subject', '')}")
            return None
        
        # Determine transaction type
        transaction_type = self._extract_type(text)
        if not transaction_type:
            return None
        
        # Extract amount
        amount = self._extract_amount(text)
        if not amount:
            logger.warning(f"Could not extract amount from: {email_data.get('subject', '')}")
            return None
        
        # Extract description
        description = self._extract_description(email_data)
        
        # Extract date
        transaction_date = self._extract_date(email_data.get('date', ''))
        
        return {
            'type': transaction_type,  # 'income' or 'expense'
            'amount': amount,
            'description': description,
            'date': transaction_date,
            'raw_subject': email_data.get('subject', ''),
            'raw_body': email_data.get('body', ''),
            'sender': email_data.get('sender', ''),
            'email_id': email_data.get('id', '')
        }
    
    def _is_transaction_alert(self, text: str) -> bool:
        """Check if text looks like a transaction alert"""
        keywords = [
            'debit', 'credit', 'transaction', 'alert', 'notification',
            'account', 'balance', 'payment', 'transfer', 'withdrawal',
            'deposit', 'charged', 'acct'
        ]
        return any(keyword in text for keyword in keywords)
    
    def _extract_type(self, text: str) -> Optional[str]:
        """Determine if transaction is income or expense"""
        # Check for debit keywords
        for pattern in self.DEBIT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return 'expense'
        
        # Check for credit keywords
        for pattern in self.CREDIT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return 'income'
        
        return None
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract transaction amount"""
        for pattern in self.AMOUNT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        return None
    
    def _extract_description(self, email_data: Dict) -> str:
        """
        Extract meaningful description from email
        Tries to find merchant name, beneficiary, or transaction purpose
        """
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        
        # Common description patterns
        desc_patterns = [
            r'desc[ription]*:\s*([^\n\r]+)',
            r'narration:\s*([^\n\r]+)',
            r'details:\s*([^\n\r]+)',
            r'merchant:\s*([^\n\r]+)',
            r'beneficiary:\s*([^\n\r]+)',
            r'to:\s*([^\n\r]+)',
            r'from:\s*([^\n\r]+)'
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback: use subject if it contains useful info
        if len(subject) > 10 and len(subject) < 100:
            return subject
        
        # Last resort: return snippet of body
        return body[:100] if body else "Transaction"
    
    def _extract_date(self, date_str: str) -> str:
        """
        Extract and normalize date from email date header
        Returns ISO format date string
        """
        try:
            # Email date format: "Wed, 01 Nov 2025 10:30:00 +0100"
            # Parse common formats
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.strftime('%Y-%m-%d')
        except:
            # Fallback to current date
            return datetime.now().strftime('%Y-%m-%d')
