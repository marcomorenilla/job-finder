import json
import os
import asyncio
import logging
import telegramify_markdown

from telegramify_markdown.customize import get_runtime_config
from pathlib import Path
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from markdownify import markdownify as md
from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types
from aiogram import Bot

# --- Constants and Configuration ---
# Nombres de archivos centralizados para fácil modificación.
BASE_DIR = Path(__file__).resolve().parent
URLS_FILE = BASE_DIR / 'assets/urls.json'
SYSTEM_INSTRUCTIONS_FILE = BASE_DIR / 'assets/system_instructions.md'
OUTPUT_MD_FILE = BASE_DIR / 'assets/webs.md'
GEMINI_RESPONSE_FILE = BASE_DIR / 'logs/gemini_response.md'
AI_MODEL_NAME = "gemini-2.5-flash"

# Configuración del logging para reemplazar los 'print'.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración básica para poner una chincheta en h1 y links telegram
get_runtime_config().markdown_symbol.head_level_1 = "📌" 
get_runtime_config().markdown_symbol.link = "🔗" 

# --- Main Functions ---

async def get_html(urls: List[str]) -> List[str]:
    """
    Navega a una lista de URLs usando Selenium y devuelve el contenido HTML de cada una.
    Utiliza un navegador en modo headless (sin interfaz gráfica).
    """
    logging.info('Iniciando la obtención de HTMLs con Selenium.')
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    driver = webdriver.Chrome(options=chrome_options)
    html_collection: List[str] = []

    try:
        for url in urls:
            logging.info(f'Procesando URL: {url}')
            driver.get(url)

            try:
                # Espera explícita a que un elemento clave esté presente.
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                # Estrategia de scroll robusta para activar "lazy loading".
                last_height = driver.execute_script("return document.body.scrollHeight")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                
                # Espera a que el scroll cargue nuevo contenido (si lo hay).
                WebDriverWait(driver, 5).until(
                    lambda d: d.execute_script("return document.body.scrollHeight") > last_height
                )

            except Exception:
                logging.warning(f"No se detectó contenido nuevo por lazy loading en {url} o la página cargó instantáneamente.")

            html_collection.append(driver.page_source)
        return html_collection

    except Exception as e:
        logging.error(f"Error crítico con Selenium en la URL {url}: {e}")
        return []
    finally:
        driver.quit()
        logging.info('Driver de Selenium cerrado.')

async def parse_html_to_md(htmls: List[str]) -> None:
    """
    Limpia una lista de HTMLs, los convierte a Markdown y los guarda en un único archivo.
    """
    logging.info('Iniciando limpieza de HTML y conversión a Markdown.')
    
    # Asegurarse de que el archivo de salida esté limpio antes de empezar.
    if os.path.exists(OUTPUT_MD_FILE):
        os.remove(OUTPUT_MD_FILE)

    for html in htmls:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Eliminación de etiquetas innecesarias para reducir "ruido".
        for element in soup(["script", "style", "head", "header", "footer", "nav", "noscript", "svg", "meta"]):
            element.decompose()

        main_content = soup.find('main') or soup.find('article') or soup.body
        
        if main_content:
            clean_html = str(main_content)
            md_text = md(clean_html)
            
            # Limpieza de saltos de línea excesivos.
            md_text_cleaned = "\n".join([line.strip() for line in md_text.splitlines() if line.strip()])

            with open(OUTPUT_MD_FILE, 'a', encoding='utf-8') as f:
                f.write(md_text_cleaned + "\n\n")
    
    logging.info(f'Contenido guardado exitosamente en {OUTPUT_MD_FILE}.')

async def ai_analyzer() -> Optional[str]:
    """
    Utiliza la API de Gemini para analizar el contenido Markdown y generar una respuesta.
    """
    logging.info('Iniciando análisis con Gemini AI.')
    try:
        if not os.path.exists(SYSTEM_INSTRUCTIONS_FILE) or not os.path.exists(OUTPUT_MD_FILE):
            logging.error("No se encontraron los archivos de instrucciones o de contenido para la IA.")
            return None

        client = genai.Client()

        with open(SYSTEM_INSTRUCTIONS_FILE, 'r', encoding='utf-8') as f:
            system_instructions = f.read()

        with open(OUTPUT_MD_FILE, 'r', encoding='utf-8') as f:
            file_content = f.read()


        # El prompt se ha simplificado y se ha movido a las system_instructions para mayor claridad.
        prompt = "Busca ofertas que coincidan con el perfil.\
        Responde con un mensaje aceptable para markdown con la empresa como inicio de sección h1 lists de ofertas como ul con nombre de la oferta, - ciudad (si es posible) separador : y el link como [enlace](https://link.com).\
        Utiliza el menor número de palabras posibles y no justifiques por qué se ajusta la oferta.\
        Excluye aquellas que no coincidan con el perfil"

        response = client.models.generate_content(
            model=AI_MODEL_NAME,
            contents=[file_content,prompt]
        )

        response_text = response.text

        converted = telegramify_markdown.markdownify(
            response_text,
            max_line_length=None,
            normalize_whitespace=False
        )

        with open(GEMINI_RESPONSE_FILE, 'w', encoding='utf-8') as f:
            f.write(converted)
        
        logging.info(f"Respuesta de Gemini guardada en {GEMINI_RESPONSE_FILE}.")
        return converted

    except Exception as e:
        logging.error(f"Ocurrió un error durante el análisis de Gemini AI: {e}")
        return None

async def send_telegram_message(message: str) -> None:
    """
    Envía un mensaje a un chat de Telegram a través de un Bot.
    """
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    CHAT_ID = os.getenv('CHAT_ID')

    if not TELEGRAM_TOKEN or not CHAT_ID:
        logging.error("Token de Telegram o Chat ID no configurados en las variables de entorno.")
        return

    logging.info('Enviando mensaje a Telegram.')
    try:
        async with Bot(token=TELEGRAM_TOKEN) as bot:
            await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="MarkdownV2")
            logging.info('Mensaje enviado a Telegram correctamente.')
    except Exception as e:
        logging.error(f"Fallo al enviar el mensaje a Telegram: {e}")

async def main():
    """
    Función principal que orquesta el pipeline:
    1. Carga URLs.
    2. Obtiene HTML.
    3. Procesa y convierte a Markdown.
    4. Analiza con IA.
    5. Envía notificación por Telegram.
    """
    load_dotenv()

    try:
        with open(URLS_FILE, 'r', encoding='utf-8') as f:
            urls_data: Dict[str, Any] = json.load(f)
            urls: List[str] = urls_data.get('urls', [])
        
        if not urls:
            logging.warning("El archivo de URLs está vacío o no contiene la clave 'urls'.")
            return

        htmls = await get_html(urls)
        if not htmls:
            logging.error("No se pudo obtener ningún contenido HTML. Terminando ejecución.")
            return

        await parse_html_to_md(htmls)
        
        gemini_response = await ai_analyzer()
        if not gemini_response:
            logging.error("No se obtuvo respuesta de la IA. Terminando ejecución.")
            return
            
        await send_telegram_message(gemini_response)

    except FileNotFoundError:
        logging.error(f"Error: El archivo '{URLS_FILE}' no fue encontrado.")
    except json.JSONDecodeError:
        logging.error(f"Error: El archivo '{URLS_FILE}' no es un JSON válido.")
    except Exception as e:
        logging.critical(f"Ha ocurrido una excepción no controlada en main: {e}")

if __name__ == "__main__":
    asyncio.run(main())