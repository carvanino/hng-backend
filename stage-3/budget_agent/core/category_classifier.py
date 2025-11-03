"""Transaction categorization using Gemini AI"""

import google.generativeai as genai
from typing import Dict, Optional
import logging
import json

logger = logging.getLogger(__name__)


class CategoryClassifier:
    """Categorize transactions using Gemini AI"""
    
    def __init__(self, api_key: str):
        """Initialize Gemini with API key"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
    
    def categorize(self, transaction: Dict) -> Dict:
        """
        Categorize a transaction
        
        Args:
            transaction: Dict with 'amount', 'description', 'type'
            
        Returns:
            Dict with 'category', 'confidence', 'needs_clarification'
        """
        description = transaction.get('description', '')
        amount = transaction.get('amount', 0)
        trans_type = transaction.get('type', 'expense')
        
        prompt = self._build_prompt(description, amount, trans_type)
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text)
            
            logger.info(f"Categorized '{description}' as '{result['category']}' "
                       f"(confidence: {result['confidence']})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error categorizing transaction: {e}")
            return {
                'category': 'Uncategorized',
                'confidence': 'low',
                'needs_clarification': True,
                'error': str(e)
            }
    
    def _build_prompt(self, description: str, amount: float, trans_type: str) -> str:
        """Build prompt for Gemini"""
        return f"""You are a financial transaction categorizer. Analyze this transaction and categorize it.

Transaction Details:
- Description: {description}
- Amount: ₦{amount:,.2f}
- Type: {trans_type}

Common Categories:
For EXPENSES: Transportation, Feeding, Utilities (Water/Electricity), Entertainment, Shopping, 
Healthcare, Education, Rent/Accommodation, Internet/Phone, Laundry, Toiletries, Consumables, Miscellaneous

For INCOME: Salary, Business Income, Gifts, Refunds, Investments, Other Income

Instructions:
1. Choose the MOST APPROPRIATE category from the list above
2. Assess your confidence (high/medium/low)
3. If the description is too vague or unclear, mark needs_clarification as true

Respond ONLY with valid JSON in this exact format:
{{
  "category": "Category Name",
  "confidence": "high|medium|low",
  "needs_clarification": true|false,
  "reason": "brief explanation"
}}

JSON Response:"""
    
    def _parse_response(self, response_text: str) -> Dict:
        """Parse Gemini response"""
        try:
            # Try to extract JSON from response
            # Gemini might include extra text, so we need to find the JSON block
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[start_idx:end_idx]
            result = json.loads(json_str)
            
            # Validate required fields
            if 'category' not in result:
                raise ValueError("Missing category in response")
            
            # Set defaults for missing fields
            result.setdefault('confidence', 'medium')
            result.setdefault('needs_clarification', False)
            
            # Determine if clarification needed based on confidence
            if result['confidence'] == 'low':
                result['needs_clarification'] = True
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing Gemini response: {e}")
            logger.debug(f"Raw response: {response_text}")
            
            # Fallback: try to extract category from text
            category = self._extract_category_fallback(response_text)
            
            return {
                'category': category,
                'confidence': 'low',
                'needs_clarification': True,
                'reason': 'Could not parse AI response'
            }
    
    def _extract_category_fallback(self, text: str) -> str:
        """Fallback category extraction from unstructured text"""
        # Common categories to look for
        categories = [
            'Transportation', 'Feeding', 'Utilities', 'Entertainment',
            'Shopping', 'Healthcare', 'Education', 'Rent', 'Accommodation',
            'Internet', 'Phone', 'Laundry', 'Toiletries', 'Consumables',
            'Salary', 'Business Income', 'Gifts', 'Refunds', 'Investments'
        ]
        
        text_lower = text.lower()
        for category in categories:
            if category.lower() in text_lower:
                return category
        
        return 'Uncategorized'
