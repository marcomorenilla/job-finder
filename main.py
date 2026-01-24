import json
import time
import os
import asyncio
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from markdownify import markdownify as md
from dotenv import load_dotenv
from google import genai
from google.genai import types
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


# Abre navegador y espera a que se ejecute el JS
# Devuelve el código del HTML completo
async def get_html(urls):
    print('entering')
    # Configuración de Chrome para que no se abra la ventana (Headless)
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        html_collection=[]
        for url in urls:

            driver.get(url)
            print(f'parsing url {url}')
            
            # Esperamos hasta 10 segundos hasta que aparezca un <a></a>
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "a"))
                )
            except Exception as e:
                print(f"  Se produjo un error recuperando la web {url}: \n{e}")

            # Hacemos un pequeño scroll hacia abajo para activar "lazy loading" si lo hubiera
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2) 

            html_content = driver.page_source
            html_collection.append(html_content)
        return html_collection

    except Exception as e:
        print(f"Error con Selenium en {url}: {e}")
        return None
    finally:
        driver.quit() 

# Conviertte el html a md para limpieza excluyendo etiquetas head, script, style
async def parse_html_to_md(htmls):
    print('Cleaning and converting content...')
    
    for html in htmls:
        # Usamos BeautifulSoup para una limpieza profunda
        soup = BeautifulSoup(html, 'html.parser')
        # Añadimos 'style', 'noscript', 'meta' y 'svg' para ahorrar más tokens
        for element in soup(["script", "style", "head", "header", "footer", "nav", "noscript", "svg", "meta"]):
            element.decompose()

        # Seleccionamos solo el contenido principal si la web usa etiquetas semánticas
        main_content = soup.find('main') or soup.find('article') or soup.body
        
        # Convertimos a Markdown lo que queda (que ya está limpio)
        if main_content:
            clean_html = str(main_content)
            md_text = md(clean_html) 
            
            # Limpieza de saltos de línea excesivos
            md_text = "\n".join([line.strip() for line in md_text.splitlines() if line.strip()])

            with open('webs.md', 'a', encoding='utf-8') as f:
                f.write(md_text)
            print('File webs.md saved successfully.')

# Crea un cliente de Gemini y le pasa el archivo.md generado con las ofertas
async def ai_analyzer(model, system_instruction,md_file):
    client = genai.Client()

    with open(md_file,'r',encoding='utf-8') as f:
        file_content=f.read()

    response = client.models.generate_content(
        model = model,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction
        ),
        contents= [file_content,'Busca ofertas que coincidan con el perfil. Responde con un mensaje aceptable para markdown de telegram con la empresa la oferta y el link'
        'Utiliza el menor número de palabras posibles y no justifiques por qué se ajusta el perfil'
        'utiliza solamente el Markdown de Telegram:'
        '- Listas'
        '* Negrita']
    )
    


    return response



async def send_message(TELEGRAM_TOKEN, CHAT_ID,message):
    print('entering in send message')

    async with Bot(
        token=TELEGRAM_TOKEN
        )as bot:
        print('enviando mensaje')
        try:
            response = await bot.send_message(chat_id=CHAT_ID,text=message)
            print(f'respuesta: {response.text}')
        except Exception as e:
            print(f'fallo {e}')



async def main(TELEGRAM_TOKEN, CHAT_ID):
    # Nombre del fichero con las Url
    urls_file = 'urls.json'
    system_instructions_file = 'system_instructions.md'
    web_md_file = 'webs.md'
    model = "gemini-2.5-flash"
    md_file = Path('webs.md')
    try:
        if(md_file.exists()):
            print(md_file)
            md_file.unlink()
        else:
            print(f'No existe el archivo {md_file}')
        with open(urls_file, 'r', encoding='utf-8') as f:
            urls = json.load(f).get('urls', [])

        with open(system_instructions_file, 'r', encoding='utf-8') as f:
            system_instructions = f.read()



        htmls = await get_html([url for url in urls] if urls else '<h1>No content found</h1>')
        await parse_html_to_md(htmls)       
        gemini_response = await ai_analyzer(model, system_instructions,md_file)
        with open('gemini_response.md','w', encoding='utf-8') as f:
            f.write(gemini_response.text)
        await send_message(TELEGRAM_TOKEN, CHAT_ID, gemini_response.text)
    except Exception as e:
        print(f'Exception:\n{e}')

if __name__ == "__main__":
    # cargamos variables de entorno
    load_dotenv()

    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    CHAT_ID = os.getenv('CHAT_ID')

    print('Cargando variables de entorno....')
    print('|')
    print(f'|-> Gemini API KEY: {GEMINI_API_KEY[0:15]}.........')
    print(f'|-> Telegram Token: {TELEGRAM_TOKEN[0:15]}.........')
    print(f'|-> Chat Id: {CHAT_ID[0:15]}.........')
    print('')

    
    asyncio.run(main(TELEGRAM_TOKEN,CHAT_ID))
