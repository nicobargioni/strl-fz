import os
import pandas as pd
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import streamlit as st
from typing import Optional, Dict, List, Any
import json

class GSCConnector:
    def __init__(self, property_url: str = None, credentials_path: str = None):
        self.property_url = property_url or os.getenv('GSC_PROPERTY_URL')
        self.credentials_path = credentials_path or os.getenv('GSC_SERVICE_ACCOUNT_FILE')
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        try:
            if self.credentials_path and os.path.exists(self.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/webmasters.readonly']
                )
                self.service = build('searchconsole', 'v1', credentials=credentials)
                return True
        except Exception as e:
            st.error(f"Error al inicializar GSC: {str(e)}")
            return False
    
    @st.cache_data(ttl=3600)
    def get_search_analytics(_self, start_date: str, end_date: str, 
                           dimensions: List[str] = None,
                           filters: List[Dict] = None,
                           row_limit: int = 25000) -> pd.DataFrame:
        
        if not _self.service:
            return pd.DataFrame()
        
        dimensions = dimensions or ['date', 'query', 'page', 'country', 'device']
        
        try:
            request = {
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': dimensions,
                'rowLimit': row_limit,
                'startRow': 0
            }
            
            if filters:
                request['dimensionFilterGroups'] = [{
                    'filters': filters
                }]
            
            response = _self.service.searchanalytics().query(
                siteUrl=_self.property_url,
                body=request
            ).execute()
            
            if 'rows' not in response:
                return pd.DataFrame()
            
            rows = []
            for row in response['rows']:
                data_row = {}
                for i, dimension in enumerate(dimensions):
                    data_row[dimension] = row['keys'][i]
                
                data_row['clicks'] = row.get('clicks', 0)
                data_row['impressions'] = row.get('impressions', 0)
                data_row['ctr'] = row.get('ctr', 0)
                data_row['position'] = row.get('position', 0)
                
                rows.append(data_row)
            
            df = pd.DataFrame(rows)
            
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            
            return df
            
        except HttpError as e:
            st.error(f"Error al obtener datos de GSC: {str(e)}")
            return pd.DataFrame()
    
    def get_top_queries(self, start_date: str, end_date: str, limit: int = 10) -> pd.DataFrame:
        df = self.get_search_analytics(
            start_date=start_date,
            end_date=end_date,
            dimensions=['query'],
            row_limit=limit
        )
        
        if not df.empty:
            df = df.sort_values('clicks', ascending=False)
        
        return df
    
    def get_top_pages(self, start_date: str, end_date: str, limit: int = 10) -> pd.DataFrame:
        df = self.get_search_analytics(
            start_date=start_date,
            end_date=end_date,
            dimensions=['page'],
            row_limit=limit
        )
        
        if not df.empty:
            df = df.sort_values('clicks', ascending=False)
            df['page'] = df['page'].str.replace(self.property_url, '', regex=False)
        
        return df
    
    def get_performance_by_device(self, start_date: str, end_date: str) -> pd.DataFrame:
        return self.get_search_analytics(
            start_date=start_date,
            end_date=end_date,
            dimensions=['device']
        )
    
    def get_performance_by_country(self, start_date: str, end_date: str, limit: int = 10) -> pd.DataFrame:
        df = self.get_search_analytics(
            start_date=start_date,
            end_date=end_date,
            dimensions=['country'],
            row_limit=limit
        )
        
        if not df.empty:
            df = df.sort_values('clicks', ascending=False)
        
        return df
    
    def get_daily_performance(self, start_date: str, end_date: str) -> pd.DataFrame:
        return self.get_search_analytics(
            start_date=start_date,
            end_date=end_date,
            dimensions=['date']
        )
    
    def search_keywords(self, keyword: str, start_date: str, end_date: str) -> pd.DataFrame:
        filters = [{
            'dimension': 'query',
            'operator': 'contains',
            'expression': keyword
        }]
        
        return self.get_search_analytics(
            start_date=start_date,
            end_date=end_date,
            dimensions=['query'],
            filters=filters
        )
    
    def get_metrics_summary(self, start_date: str, end_date: str) -> Dict[str, Any]:
        df = self.get_search_analytics(
            start_date=start_date,
            end_date=end_date,
            dimensions=['date']
        )
        
        if df.empty:
            return {
                'total_clicks': 0,
                'total_impressions': 0,
                'avg_ctr': 0,
                'avg_position': 0
            }
        
        return {
            'total_clicks': int(df['clicks'].sum()),
            'total_impressions': int(df['impressions'].sum()),
            'avg_ctr': round(df['ctr'].mean() * 100, 2),
            'avg_position': round(df['position'].mean(), 1)
        }
    
    def compare_periods(self, current_start: str, current_end: str,
                       previous_start: str, previous_end: str) -> Dict[str, Dict]:
        
        current_metrics = self.get_metrics_summary(current_start, current_end)
        previous_metrics = self.get_metrics_summary(previous_start, previous_end)
        
        comparison = {}
        for metric in current_metrics:
            current_val = current_metrics[metric]
            previous_val = previous_metrics[metric]
            
            if previous_val > 0:
                change_pct = ((current_val - previous_val) / previous_val) * 100
            else:
                change_pct = 100 if current_val > 0 else 0
            
            comparison[metric] = {
                'current': current_val,
                'previous': previous_val,
                'change': current_val - previous_val,
                'change_pct': round(change_pct, 2)
            }
        
        return comparison