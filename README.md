# Job Finder AI Pipeline

Este proyecto es un pipeline asíncrono automatizado que extrae contenido de una lista de URLs, utiliza un modelo de IA (Gemini) para analizar la información y envía un resumen de las ofertas de trabajo encontradas a un chat de Telegram.

## Características

- **Scraping Asíncrono:** Utiliza `Selenium` y `asyncio` para obtener el contenido HTML de múltiples sitios de manera eficiente.
- **Procesamiento de Contenido:** Limpia el HTML y lo convierte a Markdown con `BeautifulSoup` y `markdownify` para un análisis más limpio.
- **Análisis con IA:** Emplea la API de `Gemini` para leer el contenido procesado, identificar ofertas de trabajo relevantes según un perfil y generar un resumen.
- **Notificaciones:** Envía los resultados directamente a un chat de Telegram usando `aiogram`.
- **Configurable:** Gestiona todas las claves de API y configuraciones a través de un archivo `.env` y constantes centralizadas.
- **Logging Profesional:** Incorpora el módulo `logging` para un seguimiento detallado de la ejecución del script.

## Librerías Utilizadas

Las dependencias del proyecto se encuentran en el archivo `requirements.txt`.

## Instalación

Sigue estos pasos para poner en marcha el proyecto:

1.  **Clona el repositorio:**
    ```bash
    git clone <URL-DEL-REPOSITORIO>
    cd <NOMBRE-DEL-DIRECTORIO>
    ```

2.  **Crea y activa un entorno virtual:**
    ```bash
    # Para Linux/macOS
    python3 -m venv .venv
    source .venv/bin/activate

    # Para Windows
    python -m venv .venv
    .venv\Scripts\activate
    ```

3.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuración

Antes de ejecutar el script, necesitas configurar tres archivos en la raíz del proyecto:

1.  **`.env`**: Crea este archivo para almacenar tus claves de API y IDs.
    ```env
    GEMINI_API_KEY="TU_API_KEY_DE_GEMINI"
    TELEGRAM_TOKEN="TU_TOKEN_DE_BOT_DE_TELEGRAM"
    CHAT_ID="EL_ID_DE_TU_CHAT_DE_TELEGRAM"
    ```

2.  **`urls.json`**: Este archivo debe contener las URLs que el scraper visitará.
    ```json
    {
      "urls": [
        "https://www.ejemplo.com/ofertas-de-trabajo",
        "https://otro-ejemplo.es/carreras"
      ]
    }
    ```

3.  **`system_instructions.md`**: Define el comportamiento de la IA. Aquí le das el "rol" o el perfil que debe buscar.
    ```markdown
    Eres un asistente experto en recursos humanos especializado en encontrar ofertas para un desarrollador Python con 3 años de experiencia en desarrollo web con Django y FastAPI.
    ```

## Uso

Una vez configurado todo, ejecuta el script principal:

```bash
python main.py
```

El script comenzará el proceso y, si encuentra ofertas relevantes, enviará un mensaje al chat de Telegram configurado.

## Contacto

- **LinkedIn:** [linkedin.com/in/marcomorenilla](https://linkedin.com/in/marcomorenilla)
- **GitHub:** [github.com/marcomorenilla](https://github.com/marcomorenilla)
