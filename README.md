# Dashboard SEO - Flokzu

Dashboard de seguimiento SEO con integración de Google Search Console y Google Analytics 4.

## Características

- 📊 Visualización de métricas SEO en tiempo real
- 🔍 Integración con Google Search Console
- 📈 Integración con Google Analytics 4
- 🎯 Análisis de keywords y páginas
- 📱 Métricas por dispositivo y ubicación
- 📅 Filtros por rango de fechas

## Instalación

1. Clona el repositorio
2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Configura las credenciales:
   - Copia `.env.example` a `.env`
   - Agrega tus credenciales de Google

## Configuración de APIs de Google

### Google Search Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la API de Search Console
4. Crea una cuenta de servicio y descarga el archivo JSON
5. Da permisos a la cuenta de servicio en tu propiedad de Search Console

### Google Analytics 4

1. En Google Cloud Console, habilita la API de Google Analytics Data
2. Usa la misma cuenta de servicio o crea una nueva
3. En GA4, agrega el email de la cuenta de servicio como usuario con permisos de lectura

## Uso

### Aplicación básica (sin integración):
```bash
streamlit run app.py
```

### Aplicación con integración completa:
```bash
streamlit run app_integrated.py
```

## Estructura del Proyecto

```
streamlit_flokzu/
│
├── app.py                 # Dashboard básico sin integración
├── app_integrated.py      # Dashboard con integración completa
├── requirements.txt       # Dependencias del proyecto
├── .env.example          # Plantilla de configuración
├── .gitignore            # Archivos ignorados por git
│
└── utils/
    ├── __init__.py
    ├── gsc_connector.py  # Conector para Google Search Console
    └── ga4_connector.py  # Conector para Google Analytics 4
```

## Configuración con Streamlit Secrets

Para usar la aplicación con Streamlit Cloud, configura los secrets en el dashboard de Streamlit o crea un archivo `.streamlit/secrets.toml` localmente.

## Funcionalidades Principales

- **Overview**: Métricas generales y tendencias
- **Search Console**: Análisis de búsquedas orgánicas
- **Analytics**: Métricas de tráfico y comportamiento
- **Keywords**: Análisis detallado de palabras clave
- **Páginas**: Rendimiento por página