import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import os

from utils import GSCConnector, GA4Connector

st.set_page_config(
    page_title="Dashboard SEO - Flokzu",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar conectores sin caché para GA4
@st.cache_resource
def init_gsc():
    return GSCConnector()

# GA4 sin caché para asegurar que use el property ID hardcodeado
def init_ga4():
    return GA4Connector()

gsc_connector = init_gsc()
ga4_connector = init_ga4()

st.title("📊 Dashboard SEO - Flokzu")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Configuración")
    
    st.subheader("📅 Rango de Fechas")
    
    # Selector de período predefinido
    period_options = {
        "Últimas 24 horas": 1,
        "Últimos 7 días": 7,
        "Últimos 28 días": 28,
        "Últimos 3 meses": 90,
        "Últimos 6 meses": 180,
        "Últimos 12 meses": 365,
        "Últimos 16 meses": 480,
        "Personalizado": 0
    }
    
    selected_period = st.selectbox(
        "Seleccionar período",
        options=list(period_options.keys()),
        index=1  # Por defecto "Últimos 28 días"
    )
    
    if selected_period == "Personalizado":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Fecha inicio",
                value=datetime.now() - timedelta(days=30)
            )
        with col2:
            end_date = st.date_input(
                "Fecha fin",
                value=datetime.now() - timedelta(days=1)
            )
    else:
        days = period_options[selected_period]
        end_date = datetime.now().date() - timedelta(days=1)
        start_date = end_date - timedelta(days=days-1)
        
        col1, col2 = st.columns(2)
        with col1:
            st.date_input(
                "Fecha inicio",
                value=start_date,
                disabled=True
            )
        with col2:
            st.date_input(
                "Fecha fin",
                value=end_date,
                disabled=True
            )
    
    # Comparación de períodos
    st.markdown("---")
    enable_comparison = st.checkbox("📊 Comparar con período anterior")
    
    if enable_comparison:
        period_days = (end_date - start_date).days + 1
        comparison_end = start_date - timedelta(days=1)
        comparison_start = comparison_end - timedelta(days=period_days-1)
        
        st.caption(f"**Período anterior:**")
        st.caption(f"{comparison_start.strftime('%d/%m/%Y')} - {comparison_end.strftime('%d/%m/%Y')}")
        
        date_format_comparison_start = comparison_start.strftime('%Y-%m-%d')
        date_format_comparison_end = comparison_end.strftime('%Y-%m-%d')
    
    date_format_start = start_date.strftime('%Y-%m-%d')
    date_format_end = end_date.strftime('%Y-%m-%d')
    
    st.subheader("🔗 Estado de Conexiones")
    
    if gsc_connector.service:
        st.success("✅ Google Search Console conectado")
    else:
        st.error("❌ GSC no conectado")
        st.info("Configura las credenciales en Streamlit Secrets")
    
    if ga4_connector.client and ga4_connector.property_id:
        st.success("✅ Google Analytics 4 conectado")
        st.caption(f"Property ID: {ga4_connector.property_id}")
    else:
        st.error("❌ GA4 no conectado")
        st.info("❌ Configurar credenciales GA4 en Streamlit Secrets")
    
    st.markdown("---")
    
    if st.button("🔄 Actualizar Datos", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

tabs = st.tabs(["📊 Overview", "🔍 Search Console", "📈 Analytics", "🎯 Keywords", "📄 Páginas"])

with tabs[0]:
    st.header("Overview General")
    
    if gsc_connector.service:
        metrics = gsc_connector.get_metrics_summary(date_format_start, date_format_end)
        
        # Obtener comparación si está habilitada
        if enable_comparison:
            comparison = gsc_connector.compare_periods(
                date_format_start, date_format_end,
                date_format_comparison_start, date_format_comparison_end
            )
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if enable_comparison:
                st.metric(
                    label="Impresiones Totales",
                    value=f"{metrics['total_impressions']:,}",
                    delta=f"{comparison['total_impressions']['change_pct']:.1f}%"
                )
            else:
                st.metric(
                    label="Impresiones Totales",
                    value=f"{metrics['total_impressions']:,}"
                )
        
        with col2:
            if enable_comparison:
                st.metric(
                    label="Clicks Totales",
                    value=f"{metrics['total_clicks']:,}",
                    delta=f"{comparison['total_clicks']['change_pct']:.1f}%"
                )
            else:
                st.metric(
                    label="Clicks Totales",
                    value=f"{metrics['total_clicks']:,}"
                )
        
        with col3:
            if enable_comparison:
                st.metric(
                    label="CTR Promedio",
                    value=f"{metrics['avg_ctr']}%",
                    delta=f"{comparison['avg_ctr']['change']:.2f}%"
                )
            else:
                st.metric(
                    label="CTR Promedio",
                    value=f"{metrics['avg_ctr']}%"
                )
        
        with col4:
            if enable_comparison:
                # Para posición, negativo es mejor (más cerca de 1)
                delta_pos = -comparison['avg_position']['change']
                st.metric(
                    label="Posición Promedio",
                    value=f"{metrics['avg_position']}",
                    delta=f"{delta_pos:.1f}"
                )
            else:
                st.metric(
                    label="Posición Promedio",
                    value=f"{metrics['avg_position']}"
                )
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Tendencia de Clicks e Impresiones")
            daily_data = gsc_connector.get_daily_performance(date_format_start, date_format_end)
            
            if not daily_data.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=daily_data['date'],
                    y=daily_data['clicks'],
                    mode='lines',
                    name='Clicks',
                    line=dict(color='blue', width=2)
                ))
                fig.add_trace(go.Scatter(
                    x=daily_data['date'],
                    y=daily_data['impressions'],
                    mode='lines',
                    name='Impresiones',
                    line=dict(color='lightblue', width=2),
                    yaxis='y2'
                ))
                
                fig.update_layout(
                    yaxis=dict(title='Clicks', side='left'),
                    yaxis2=dict(title='Impresiones', overlaying='y', side='right'),
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Top Keywords")
            top_queries = gsc_connector.get_top_queries(date_format_start, date_format_end, limit=10)
            
            if not top_queries.empty:
                fig = px.bar(
                    top_queries.head(10),
                    x='clicks',
                    y='query',
                    orientation='h',
                    title='Top 10 Keywords por Clicks',
                    labels={'clicks': 'Clicks', 'query': 'Keyword'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Nuevos gráficos de cruzamiento de datos
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("📱 Rendimiento por Dispositivo")
            device_data = gsc_connector.get_performance_by_device(date_format_start, date_format_end)
            
            if not device_data.empty:
                fig = px.scatter(
                    device_data,
                    x='impressions',
                    y='clicks',
                    size='ctr',
                    color='device',
                    title='Clicks vs Impresiones por Dispositivo',
                    labels={'impressions': 'Impresiones', 'clicks': 'Clicks', 'ctr': 'CTR'},
                    hover_data=['position']
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🌍 CTR vs Posición por País")
            country_data = gsc_connector.get_performance_by_country(date_format_start, date_format_end, limit=15)
            
            if not country_data.empty:
                fig = px.scatter(
                    country_data,
                    x='position',
                    y='ctr',
                    size='clicks',
                    color='country',
                    title='CTR vs Posición Promedio',
                    labels={'position': 'Posición Promedio', 'ctr': 'CTR', 'clicks': 'Clicks'}
                )
                fig.update_layout(
                    xaxis=dict(autorange="reversed"),  # Posición 1 es mejor
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col3:
            st.subheader("📊 Keywords: Posición vs CTR")
            keywords_scatter = gsc_connector.get_search_analytics(
                date_format_start, 
                date_format_end,
                dimensions=['query'],
                row_limit=100
            )
            
            if not keywords_scatter.empty:
                # Filtrar solo keywords con más de 50 impresiones para mejor visualización
                keywords_filtered = keywords_scatter[keywords_scatter['impressions'] >= 50].head(30)
                
                fig = px.scatter(
                    keywords_filtered,
                    x='position',
                    y='ctr',
                    size='impressions',
                    color='clicks',
                    hover_name='query',
                    title='CTR vs Posición (Keywords)',
                    labels={'position': 'Posición Promedio', 'ctr': 'CTR', 'impressions': 'Impresiones', 'clicks': 'Clicks'}
                )
                fig.update_layout(
                    xaxis=dict(autorange="reversed"),
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Evolución del CTR vs Posición")
            daily_perf = gsc_connector.get_daily_performance(date_format_start, date_format_end)
            
            if not daily_perf.empty:
                fig = go.Figure()
                
                # CTR en eje Y izquierdo
                fig.add_trace(go.Scatter(
                    x=daily_perf['date'],
                    y=daily_perf['ctr'],
                    mode='lines+markers',
                    name='CTR (%)',
                    line=dict(color='blue', width=2),
                    yaxis='y'
                ))
                
                # Posición en eje Y derecho (invertido)
                fig.add_trace(go.Scatter(
                    x=daily_perf['date'],
                    y=daily_perf['position'],
                    mode='lines+markers',
                    name='Posición',
                    line=dict(color='red', width=2),
                    yaxis='y2'
                ))
                
                fig.update_layout(
                    title='Evolución CTR vs Posición Promedio',
                    yaxis=dict(title='CTR (%)', side='left'),
                    yaxis2=dict(title='Posición Promedio', overlaying='y', side='right', autorange='reversed'),
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🔥 Top Páginas por CTR")
            top_pages_ctr = gsc_connector.get_search_analytics(
                date_format_start,
                date_format_end,
                dimensions=['page'],
                row_limit=20
            )
            
            if not top_pages_ctr.empty:
                # Filtrar páginas con al menos 100 impresiones y ordenar por CTR
                top_pages_filtered = top_pages_ctr[top_pages_ctr['impressions'] >= 100].sort_values('ctr', ascending=False).head(10)
                
                # Limpiar URLs
                top_pages_filtered['page_clean'] = top_pages_filtered['page'].str.replace(
                    gsc_connector.property_url, '', regex=False
                ).str[:30] + '...'
                
                fig = px.bar(
                    top_pages_filtered,
                    x='ctr',
                    y='page_clean',
                    orientation='h',
                    color='clicks',
                    title='Top 10 Páginas por CTR (>100 imp.)',
                    labels={'ctr': 'CTR (%)', 'page_clean': 'Página', 'clicks': 'Clicks'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Conecta Google Search Console para ver las métricas")

with tabs[1]:
    st.header("Google Search Console")
    
    if gsc_connector.service:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Métricas por Dispositivo")
            device_data = gsc_connector.get_performance_by_device(date_format_start, date_format_end)
            
            if not device_data.empty:
                fig = px.pie(
                    device_data,
                    values='clicks',
                    names='device',
                    title='Distribución de Clicks por Dispositivo'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🌍 Métricas por País")
            country_data = gsc_connector.get_performance_by_country(date_format_start, date_format_end, limit=10)
            
            if not country_data.empty:
                fig = px.bar(
                    country_data.head(10),
                    x='clicks',
                    y='country',
                    orientation='h',
                    title='Top 10 Países por Clicks'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📊 Datos Detallados")
        
        detailed_data = gsc_connector.get_search_analytics(
            date_format_start, 
            date_format_end,
            dimensions=['query', 'page'],
            row_limit=100
        )
        
        if not detailed_data.empty:
            st.dataframe(
                detailed_data[['query', 'page', 'clicks', 'impressions', 'ctr', 'position']].round(2),
                use_container_width=True
            )
    else:
        st.warning("⚠️ Conecta tu cuenta de Google Search Console para ver métricas")

with tabs[2]:
    st.header("Google Analytics 4")
    
    if ga4_connector.client:
        metrics = ga4_connector.get_metrics_summary(date_format_start, date_format_end)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Usuarios", f"{metrics['total_users']:,}")
        
        with col2:
            st.metric("Sesiones", f"{metrics['total_sessions']:,}")
        
        with col3:
            st.metric("Tasa de Rebote", f"{metrics['avg_bounce_rate']}%")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Tráfico Orgánico")
            organic_data = ga4_connector.get_organic_traffic(date_format_start, date_format_end)
            
            if not organic_data.empty:
                # Ordenar por fecha para evitar líneas cruzadas
                organic_data = organic_data.sort_values('date')
                
                fig = px.line(
                    organic_data,
                    x='date',
                    y='sessions',
                    title='Sesiones de Tráfico Orgánico',
                    labels={'sessions': 'Sesiones', 'date': 'Fecha'},
                    markers=True
                )
                fig.update_traces(line=dict(width=2))
                fig.update_layout(
                    xaxis_tickformat='%d %b',
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📱 Tráfico por Dispositivo")
            device_data = ga4_connector.get_device_metrics(date_format_start, date_format_end)
            
            if not device_data.empty:
                fig = px.pie(
                    device_data,
                    values='sessions',
                    names='deviceCategory',
                    title='Distribución por Tipo de Dispositivo'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🎯 Top Landing Pages")
        
        landing_pages = ga4_connector.get_top_landing_pages(date_format_start, date_format_end)
        
        if not landing_pages.empty:
            st.dataframe(
                landing_pages[['landingPagePlusQueryString', 'sessions', 'totalUsers', 'bounceRate']].round(2),
                use_container_width=True
            )
    else:
        st.warning("⚠️ Conecta tu cuenta de GA4 para ver métricas")

with tabs[3]:
    st.header("Análisis de Keywords")
    
    if gsc_connector.service:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🔍 Búsqueda de Keywords")
            keyword_search = st.text_input("Buscar keyword", placeholder="Ingresa una keyword...")
        
        with col2:
            st.subheader("Filtros")
            min_impressions = st.number_input("Impresiones mínimas", min_value=0, value=100)
        
        st.markdown("---")
        
        if keyword_search:
            st.subheader(f"Resultados para: '{keyword_search}'")
            search_results = gsc_connector.search_keywords(
                keyword_search, 
                date_format_start, 
                date_format_end
            )
            
            if not search_results.empty:
                st.dataframe(
                    search_results[['query', 'clicks', 'impressions', 'ctr', 'position']].round(2),
                    use_container_width=True
                )
            else:
                st.info("No se encontraron resultados para esta keyword")
        else:
            st.subheader("📊 Todas las Keywords")
            all_queries = gsc_connector.get_search_analytics(
                date_format_start,
                date_format_end,
                dimensions=['query'],
                row_limit=500
            )
            
            if not all_queries.empty:
                filtered_queries = all_queries[all_queries['impressions'] >= min_impressions]
                
                st.info(f"Mostrando {len(filtered_queries)} keywords con más de {min_impressions} impresiones")
                
                st.dataframe(
                    filtered_queries[['query', 'clicks', 'impressions', 'ctr', 'position']]
                    .sort_values('clicks', ascending=False)
                    .round(2),
                    use_container_width=True
                )
    else:
        st.warning("⚠️ Conecta Google Search Console para ver datos de keywords")

with tabs[4]:
    st.header("Análisis de Páginas")
    
    if gsc_connector.service:
        st.subheader("🏆 Top Páginas por Rendimiento")
        
        top_pages = gsc_connector.get_top_pages(date_format_start, date_format_end, limit=20)
        
        if not top_pages.empty:
            fig = px.bar(
                top_pages.head(10),
                x='clicks',
                y='page',
                orientation='h',
                title='Top 10 Páginas por Clicks',
                labels={'clicks': 'Clicks', 'page': 'Página'}
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            st.subheader("📊 Tabla Detallada de Páginas")
            st.dataframe(
                top_pages[['page', 'clicks', 'impressions', 'ctr', 'position']].round(2),
                use_container_width=True
            )
        
        if ga4_connector.client:
            st.markdown("---")
            st.subheader("📈 Métricas de Páginas (GA4)")
            
            page_metrics = ga4_connector.get_page_metrics(date_format_start, date_format_end)
            
            if not page_metrics.empty:
                st.dataframe(
                    page_metrics[['pagePath', 'screenPageViews', 'totalUsers', 'bounceRate']].round(2),
                    use_container_width=True
                )
    else:
        st.warning("⚠️ Conecta Google Search Console para ver datos de páginas")

st.markdown("---")
st.caption("Dashboard SEO para Flokzu - Actualizado: " + datetime.now().strftime("%Y-%m-%d %H:%M"))