"""
Query executor that runs parsed queries against data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

load_dotenv()


class QueryExecutor:
    """
    Executes parsed queries against anomaly data.
    
    Supports:
    - Filtering
    - Aggregations
    - Sorting
    - Grouping
    - Natural language result summaries
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize query executor.
        
        Args:
            api_key: Google API key for result summarization
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        
        if self.api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=self.api_key,
                temperature=0.3
            )
        else:
            self.llm = None
    
    def execute(
        self,
        data: pd.DataFrame,
        parsed_query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute parsed query against data.
        
        Args:
            data: DataFrame with anomaly data
            parsed_query: Parsed query structure from NLQueryParser
        
        Returns:
            Dictionary with results and summary
        """
        df = data.copy()
        
        # Apply filters
        if parsed_query.get('filters'):
            df = self._apply_filters(df, parsed_query['filters'])
        
        # Apply grouping and aggregations
        if parsed_query.get('group_by') or parsed_query.get('aggregations'):
            df = self._apply_aggregations(
                df,
                parsed_query.get('aggregations', []),
                parsed_query.get('group_by', [])
            )
        
        # Apply sorting
        if parsed_query.get('sort'):
            df = self._apply_sort(df, parsed_query['sort'])
        
        # Apply limit
        if parsed_query.get('limit'):
            df = df.head(parsed_query['limit'])
        
        # Generate natural language summary
        summary = self._generate_summary(df, parsed_query)
        
        return {
            'results': df,
            'summary': summary,
            'row_count': len(df)
        }
    
    def _apply_filters(
        self,
        df: pd.DataFrame,
        filters: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """Apply filter conditions."""
        for filter_cond in filters:
            column = filter_cond['column']
            operator = filter_cond['operator']
            value = filter_cond['value']
            
            if column not in df.columns:
                continue
            
            if operator == '==':
                df = df[df[column] == value]
            elif operator == '!=':
                df = df[df[column] != value]
            elif operator == '>':
                df = df[df[column] > value]
            elif operator == '<':
                df = df[df[column] < value]
            elif operator == '>=':
                df = df[df[column] >= value]
            elif operator == '<=':
                df = df[df[column] <= value]
            elif operator == 'in':
                df = df[df[column].isin(value)]
            elif operator == 'not_in':
                df = df[~df[column].isin(value)]
            elif operator == 'contains':
                df = df[df[column].str.contains(value, case=False, na=False)]
        
        return df
    
    def _apply_aggregations(
        self,
        df: pd.DataFrame,
        aggregations: List[Dict[str, str]],
        group_by: List[str]
    ) -> pd.DataFrame:
        """Apply aggregation functions."""
        if not aggregations:
            return df
        
        # Build aggregation dict
        agg_dict = {}
        for agg in aggregations:
            func = agg['function']
            column = agg['column']
            
            if column == '*':
                # Count all rows
                agg_dict['count'] = ('id', 'count')
            else:
                if func == 'count':
                    agg_dict[f'{column}_count'] = (column, 'count')
                elif func == 'sum':
                    agg_dict[f'{column}_sum'] = (column, 'sum')
                elif func == 'mean':
                    agg_dict[f'{column}_mean'] = (column, 'mean')
                elif func == 'median':
                    agg_dict[f'{column}_median'] = (column, 'median')
                elif func == 'min':
                    agg_dict[f'{column}_min'] = (column, 'min')
                elif func == 'max':
                    agg_dict[f'{column}_max'] = (column, 'max')
                elif func == 'std':
                    agg_dict[f'{column}_std'] = (column, 'std')
        
        # Apply grouping if specified
        if group_by:
            result = df.groupby(group_by).agg(**agg_dict).reset_index()
        else:
            # Aggregate entire dataset
            result = pd.DataFrame([{
                key: df[col].agg(func) if col in df.columns else 0
                for key, (col, func) in agg_dict.items()
            }])
        
        return result
    
    def _apply_sort(
        self,
        df: pd.DataFrame,
        sort_ops: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """Apply sorting operations."""
        for sort_op in sort_ops:
            column = sort_op['column']
            ascending = sort_op.get('ascending', True)
            
            if column in df.columns:
                df = df.sort_values(column, ascending=ascending)
        
        return df
    
    def _generate_summary(
        self,
        df: pd.DataFrame,
        parsed_query: Dict[str, Any]
    ) -> str:
        """Generate natural language summary of results."""
        if self.llm is None:
            return f"Found {len(df)} results."
        
        # Create summary of results
        summary_data = {
            'row_count': len(df),
            'columns': list(df.columns),
            'sample_data': df.head(3).to_dict('records') if len(df) > 0 else []
        }
        
        prompt = f"""Summarize these query results in 1-2 sentences:

Query structure: {parsed_query}
Results: {summary_data}

Provide a natural language summary that a pipeline engineer would understand.
Focus on key findings and numbers."""
        
        try:
            messages = [
                SystemMessage(content="You are a helpful assistant summarizing pipeline inspection data."),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"Found {len(df)} results. (Summary generation failed: {e})"
