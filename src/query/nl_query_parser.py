"""
Natural language query parser using Google Gemini.
"""

import os
import json
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

# Load environment variables
load_dotenv()


class NLQueryParser:
    """
    Parses natural language queries into structured operations.
    
    Uses Google Gemini to understand user intent and extract:
    - Filters (depth > 50%, feature_type == 'metal_loss')
    - Aggregations (count, mean, max, min)
    - Sort operations
    - Group by clauses
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize query parser.
        
        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Google API key not found. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # Initialize Gemini model
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=self.api_key,
            temperature=0.1  # Low temperature for consistent parsing
        )
        
        # Conversation history for context
        self.conversation_history: List[Dict[str, str]] = []
    
    def parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parse natural language query into structured format.
        
        Args:
            query: Natural language query
        
        Returns:
            Dictionary with parsed query structure:
            {
                'filters': [{'column': 'depth_pct', 'operator': '>', 'value': 50}],
                'aggregations': [{'function': 'count', 'column': '*'}],
                'sort': [{'column': 'depth_pct', 'ascending': False}],
                'group_by': ['feature_type'],
                'limit': 10
            }
        """
        # Build prompt with schema information
        prompt = self._build_prompt(query)
        
        # Get response from Gemini
        messages = [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse JSON response
        try:
            parsed = json.loads(response.content)
            
            # Store in conversation history
            self.conversation_history.append({
                'query': query,
                'parsed': parsed
            })
            
            return parsed
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response: {e}\nResponse: {response.content}")
    
    def _get_system_prompt(self) -> str:
        """Get system prompt with schema information."""
        return """You are a query parser for a pipeline inspection database.

Available columns:
- id: Anomaly ID (string)
- run_id: Inspection run ID (string)
- feature_type: Type of anomaly (metal_loss, dent, crack, etc.)
- depth_pct: Depth as percentage of wall thickness (0-100)
- length_in: Length in inches
- width_in: Width in inches
- clock_position: Clock position (1-12)
- corrected_distance: Distance along pipeline in feet
- original_distance: Original distance before correction

Parse the user's natural language query into a structured JSON format with these fields:
- filters: List of filter conditions [{column, operator, value}]
  - Operators: ==, !=, >, <, >=, <=, in, not_in, contains
- aggregations: List of aggregation functions [{function, column}]
  - Functions: count, sum, mean, median, min, max, std
- sort: List of sort operations [{column, ascending}]
- group_by: List of columns to group by
- limit: Maximum number of results (optional)

Return ONLY valid JSON, no additional text.

Examples:
Query: "Show me all metal loss anomalies deeper than 50%"
Response: {"filters": [{"column": "feature_type", "operator": "==", "value": "metal_loss"}, {"column": "depth_pct", "operator": ">", "value": 50}], "aggregations": [], "sort": [], "group_by": [], "limit": null}

Query: "What's the average depth by feature type?"
Response: {"filters": [], "aggregations": [{"function": "mean", "column": "depth_pct"}], "sort": [], "group_by": ["feature_type"], "limit": null}

Query: "Top 10 deepest anomalies"
Response: {"filters": [], "aggregations": [], "sort": [{"column": "depth_pct", "ascending": false}], "group_by": [], "limit": 10}
"""
    
    def _build_prompt(self, query: str) -> str:
        """Build prompt with query and context."""
        prompt = f"Parse this query: {query}"
        
        # Add conversation context if available
        if self.conversation_history:
            last_query = self.conversation_history[-1]
            prompt += f"\n\nPrevious query: {last_query['query']}"
        
        return prompt
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
