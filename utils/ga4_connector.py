import os
import pandas as pd
from datetime import datetime, timedelta
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    FilterExpression,
    Filter
)
from google.oauth2 import service_account
import streamlit as st
from typing import Optional, Dict, List, Any
import json
import tempfile
import base64

class GA4Connector:
    def __init__(self, property_id: str = None, credentials_path: str = None):
        # Hardcoded property ID
        self.property_id = "300886887"
        
        self.credentials_path = credentials_path or os.getenv('GA4_SERVICE_ACCOUNT_FILE')
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        try:
            # Intentar usar las credenciales de Streamlit Secrets primero
            if "GA4_SERVICE_ACCOUNT_BASE64" in st.secrets:
                # Decodificar Base64
                creds_json = base64.b64decode(st.secrets["GA4_SERVICE_ACCOUNT_BASE64"]).decode()
                creds_dict = json.loads(creds_json)
                
                # Crear archivo temporal con las credenciales
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(creds_dict, f)
                    temp_path = f.name
                
                credentials = service_account.Credentials.from_service_account_file(
                    temp_path,
                    scopes=['https://www.googleapis.com/auth/analytics.readonly']
                )
                # Eliminar archivo temporal
                os.unlink(temp_path)
            
            elif "ga4_service_account" in st.secrets:
                # Fallback al método anterior
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(dict(st.secrets["ga4_service_account"]), f)
                    temp_path = f.name
                
                credentials = service_account.Credentials.from_service_account_file(
                    temp_path,
                    scopes=['https://www.googleapis.com/auth/analytics.readonly']
                )
                os.unlink(temp_path)
                
            elif self.credentials_path and os.path.exists(self.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/analytics.readonly']
                )
            else:
                if not self.property_id:
                    st.error("GA4_PROPERTY_ID no está configurado")
                return False
            
            self.client = BetaAnalyticsDataClient(credentials=credentials)
            
            return True
            
        except Exception as e:
            st.error(f"Error al inicializar GA4: {str(e)}")
            return False
    
    @st.cache_data(ttl=3600)
    def run_report(_self, start_date: str, end_date: str,
                  dimensions: List[str], metrics: List[str],
                  _dimension_filter: Optional[FilterExpression] = None,
                  limit: int = 10000) -> pd.DataFrame:
        
        if not _self.client or not _self.property_id:
            return pd.DataFrame()
        
        try:
            dimension_objects = [Dimension(name=d) for d in dimensions]
            metric_objects = [Metric(name=m) for m in metrics]
            
            request = RunReportRequest(
                property=f"properties/{_self.property_id}",
                dimensions=dimension_objects,
                metrics=metric_objects,
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                limit=limit
            )
            
            if _dimension_filter:
                request.dimension_filter = _dimension_filter
            
            response = _self.client.run_report(request)
            
            rows = []
            for row in response.rows:
                data_row = {}
                
                for i, dimension_value in enumerate(row.dimension_values):
                    data_row[dimensions[i]] = dimension_value.value
                
                for i, metric_value in enumerate(row.metric_values):
                    data_row[metrics[i]] = float(metric_value.value) if metric_value.value else 0
                
                rows.append(data_row)
            
            df = pd.DataFrame(rows)
            
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            
            return df
            
        except Exception as e:
            error_msg = f"Error al obtener datos de GA4: {str(e)}"
            if "403" in str(e):
                error_msg += "\n\n🔍 **Posibles soluciones:**\n"
                error_msg += "1. Verificar que la cuenta de servicio tenga permisos en GA4\n"
                error_msg += "2. Confirmar que GA4_PROPERTY_ID sea correcto\n"
                error_msg += "3. Verificar que la propiedad GA4 tenga datos"
            elif "404" in str(e):
                error_msg += f"\n\n❌ Property ID '{_self.property_id}' no encontrado"
            
            st.error(error_msg)
            return pd.DataFrame()
    
    def get_organic_traffic(self, start_date: str, end_date: str) -> pd.DataFrame:
        organic_filter = FilterExpression(
            filter=Filter(
                field_name="sessionDefaultChannelGroup",
                string_filter=Filter.StringFilter(value="Organic Search")
            )
        )
        
        return self.run_report(
            start_date=start_date,
            end_date=end_date,
            dimensions=['date'],
            metrics=['sessions', 'totalUsers', 'newUsers', 'bounceRate', 
                    'averageSessionDuration', 'screenPageViews'],
            _dimension_filter=organic_filter
        )
    
    def get_traffic_sources(self, start_date: str, end_date: str) -> pd.DataFrame:
        return self.run_report(
            start_date=start_date,
            end_date=end_date,
            dimensions=['sessionSource', 'sessionMedium'],
            metrics=['sessions', 'totalUsers', 'bounceRate']
        )
    
    def get_top_landing_pages(self, start_date: str, end_date: str, limit: int = 20) -> pd.DataFrame:
        df = self.run_report(
            start_date=start_date,
            end_date=end_date,
            dimensions=['landingPagePlusQueryString'],
            metrics=['sessions', 'totalUsers', 'bounceRate', 'averageSessionDuration'],
            limit=limit
        )
        
        if not df.empty:
            df = df.sort_values('sessions', ascending=False)
            df['landingPagePlusQueryString'] = df['landingPagePlusQueryString'].str.replace(
                r'^https?://[^/]+', '', regex=True
            )
        
        return df
    
    def get_device_metrics(self, start_date: str, end_date: str) -> pd.DataFrame:
        return self.run_report(
            start_date=start_date,
            end_date=end_date,
            dimensions=['deviceCategory'],
            metrics=['sessions', 'totalUsers', 'bounceRate', 'screenPageViews']
        )
    
    def get_geo_metrics(self, start_date: str, end_date: str, limit: int = 20) -> pd.DataFrame:
        df = self.run_report(
            start_date=start_date,
            end_date=end_date,
            dimensions=['country'],
            metrics=['sessions', 'totalUsers', 'bounceRate'],
            limit=limit
        )
        
        if not df.empty:
            df = df.sort_values('sessions', ascending=False)
        
        return df
    
    def get_page_metrics(self, start_date: str, end_date: str, limit: int = 20) -> pd.DataFrame:
        df = self.run_report(
            start_date=start_date,
            end_date=end_date,
            dimensions=['pagePath'],
            metrics=['screenPageViews', 'totalUsers', 'averageSessionDuration', 'bounceRate'],
            limit=limit
        )
        
        if not df.empty:
            df = df.sort_values('screenPageViews', ascending=False)
        
        return df
    
    def get_user_engagement(self, start_date: str, end_date: str) -> pd.DataFrame:
        return self.run_report(
            start_date=start_date,
            end_date=end_date,
            dimensions=['date'],
            metrics=['activeUsers', 'newUsers', 'userEngagementDuration', 
                    'engagedSessions', 'engagementRate']
        )
    
    def get_conversions(self, start_date: str, end_date: str) -> pd.DataFrame:
        return self.run_report(
            start_date=start_date,
            end_date=end_date,
            dimensions=['eventName'],
            metrics=['eventCount', 'totalUsers']
        )
    
    def get_metrics_summary(self, start_date: str, end_date: str) -> Dict[str, Any]:
        df = self.run_report(
            start_date=start_date,
            end_date=end_date,
            dimensions=['date'],
            metrics=['sessions', 'totalUsers', 'newUsers', 'bounceRate', 
                    'averageSessionDuration', 'screenPageViews']
        )
        
        if df.empty:
            return {
                'total_sessions': 0,
                'total_users': 0,
                'new_users': 0,
                'avg_bounce_rate': 0,
                'avg_session_duration': 0,
                'total_page_views': 0
            }
        
        return {
            'total_sessions': int(df['sessions'].sum()),
            'total_users': int(df['totalUsers'].sum()),
            'new_users': int(df['newUsers'].sum()),
            'avg_bounce_rate': round(df['bounceRate'].mean() * 100, 2),
            'avg_session_duration': round(df['averageSessionDuration'].mean(), 2),
            'total_page_views': int(df['screenPageViews'].sum())
        }
    
    def get_organic_keywords(self, start_date: str, end_date: str) -> pd.DataFrame:
        organic_filter = FilterExpression(
            filter=Filter(
                field_name="sessionMedium",
                string_filter=Filter.StringFilter(value="organic")
            )
        )
        
        return self.run_report(
            start_date=start_date,
            end_date=end_date,
            dimensions=['sessionSourceMedium', 'landingPagePlusQueryString'],
            metrics=['sessions', 'totalUsers', 'bounceRate'],
            _dimension_filter=organic_filter
        )
    
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