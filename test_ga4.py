import streamlit as st
import os
from utils.ga4_connector import GA4Connector
from datetime import datetime, timedelta
import traceback

def test_ga4_connection():
    st.title("🧪 Test GA4 Connection")
    
    # Mostrar variables de entorno y secrets
    st.subheader("📋 Configuration Info")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Environment Variables:**")
        ga4_env_vars = {k: v for k, v in os.environ.items() if 'GA4' in k.upper()}
        if ga4_env_vars:
            for key, value in ga4_env_vars.items():
                st.write(f"- {key}: {'***' if 'KEY' in key or 'SECRET' in key else value}")
        else:
            st.write("No GA4 environment variables found")
    
    with col2:
        st.write("**Streamlit Secrets:**")
        try:
            secrets_keys = list(st.secrets.keys()) if st.secrets else []
            ga4_secrets = [k for k in secrets_keys if 'ga4' in k.lower() or 'GA4' in k]
            if ga4_secrets:
                for key in ga4_secrets:
                    st.write(f"- {key}: Available ✅")
            else:
                st.write("No GA4 secrets found")
                st.write(f"All available secrets: {secrets_keys}")
        except Exception as e:
            st.write(f"Error accessing secrets: {e}")
    
    st.markdown("---")
    
    # Test GA4 Connection
    st.subheader("🔗 GA4 Connection Test")
    
    if st.button("Test GA4 Connection", type="primary"):
        try:
            with st.spinner("Testing GA4 connection..."):
                # Crear instancia del conector
                ga4 = GA4Connector()
                
                st.write("**Connection Details:**")
                st.write(f"- Property ID: {ga4.property_id}")
                st.write(f"- Client initialized: {ga4.client is not None}")
                st.write(f"- Credentials path: {ga4.credentials_path}")
                
                if ga4.client and ga4.property_id:
                    st.success("✅ GA4 connector initialized successfully!")
                    
                    # Test basic data retrieval
                    st.subheader("📊 Data Retrieval Test")
                    
                    # Definir fechas de prueba
                    end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                    
                    st.write(f"Testing date range: {start_date} to {end_date}")
                    
                    try:
                        # Test metrics summary
                        with st.spinner("Getting metrics summary..."):
                            metrics = ga4.get_metrics_summary(start_date, end_date)
                            
                        if metrics:
                            st.success("✅ Successfully retrieved metrics summary!")
                            st.json(metrics)
                        else:
                            st.warning("⚠️ Metrics summary returned empty")
                            
                    except Exception as data_error:
                        st.error(f"❌ Error retrieving data: {str(data_error)}")
                        st.code(traceback.format_exc())
                    
                    # Test organic traffic
                    try:
                        with st.spinner("Getting organic traffic data..."):
                            organic = ga4.get_organic_traffic(start_date, end_date)
                            
                        if not organic.empty:
                            st.success(f"✅ Successfully retrieved organic traffic data! ({len(organic)} rows)")
                            st.dataframe(organic.head())
                        else:
                            st.warning("⚠️ Organic traffic data is empty")
                            
                    except Exception as organic_error:
                        st.error(f"❌ Error retrieving organic traffic: {str(organic_error)}")
                        st.code(traceback.format_exc())
                        
                else:
                    st.error("❌ GA4 connector failed to initialize")
                    if not ga4.property_id:
                        st.error("Property ID is missing")
                    if not ga4.client:
                        st.error("Client is not initialized")
                        
        except Exception as e:
            st.error(f"❌ Error during connection test: {str(e)}")
            st.code(traceback.format_exc())
    
    st.markdown("---")
    
    # Manual property ID test
    st.subheader("🔧 Manual Property ID Test")
    
    manual_property_id = st.text_input("Enter Property ID manually:", value="300886887")
    
    if st.button("Test with Manual Property ID"):
        try:
            with st.spinner("Testing with manual property ID..."):
                ga4_manual = GA4Connector(property_id=manual_property_id)
                
                st.write(f"Manual Property ID: {ga4_manual.property_id}")
                st.write(f"Client Status: {ga4_manual.client is not None}")
                
                if ga4_manual.client:
                    # Quick data test
                    end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    start_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
                    
                    test_data = ga4_manual.run_report(
                        start_date=start_date,
                        end_date=end_date,
                        dimensions=['date'],
                        metrics=['sessions'],
                        limit=10
                    )
                    
                    if not test_data.empty:
                        st.success(f"✅ Manual test successful! Retrieved {len(test_data)} rows")
                        st.dataframe(test_data)
                    else:
                        st.warning("⚠️ Manual test returned empty data")
                else:
                    st.error("❌ Manual test failed - client not initialized")
                    
        except Exception as e:
            st.error(f"❌ Manual test error: {str(e)}")
            st.code(traceback.format_exc())

if __name__ == "__main__":
    test_ga4_connection()