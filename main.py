import json
import time
import os
import asyncio
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






# Abre navegador y espera a que se ejecute el JS
# Devuelve el código del HTML completo
async def get_html(url):

    # Configuración de Chrome para que no se abra la ventana (Headless)
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)
        
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
        return html_content

    except Exception as e:
        print(f"Error con Selenium en {url}: {e}")
        return None
    finally:
        driver.quit() 

async def ai_analyzer(model, system_instruction, contents):
    client = genai.Client()

    # Create a cache with a 5 minute TTL (300 seconds)
    """
    cache = client.caches.create(
        model=model,
        config=types.CreateCachedContentConfig(
            display_name='recruiter', 
            system_instruction=system_instruction,
            contents=[contents],
            ttl="300s",
        )
    )"""

    response = client.models.generate_content(
        model = model,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction
        ),
        contents= [contents, 'Extrae nombre de la oferta, enlace si se ajustan al perfil descrito en las instrucciones']
        #config=types.GenerateContentConfig(cached_content=cache.name)
    )
    


    return response

# Conviertte el html a md para limpieza excluyendo etiquetas head, script, style
def parse_html_to_md(html):
    print('Cleaning and converting content...')
    
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

        with open('web.md', 'w', encoding='utf-8') as f:
            f.write(md_text)
        print('File web.md saved successfully.')




async def main():
    # Nombre del fichero con las Url
    urls_file = 'urls.json'
    system_instructions_file = 'system_instructions.md'
    web_md_file = 'webs.md'
    model = "gemini-2.5-flash"
    print(f'Gemini API_KEY: {GEMINI_API_KEY[0:10]}....')
    try:
        with open(urls_file, 'r', encoding='utf-8') as f:
            urls = json.load(f).get('urls', [])
            print(urls)
        with open(system_instructions_file, 'r', encoding='utf-8') as f:
            instructions = []
            for line in f:
                instructions.append(line)
            system_instructions = "\n".join(instructions)

        with open(web_md_file, 'r', encoding='utf-8') as f:
            web_content = []
            for line in f:
                web_content.append(line)
            content = "\n".join(web_content)
    

    except Exception:
        return

    # Palabras claves provisionales
    keywords = ["Junior", "python", "developer", "programador"]
    html = await get_html(urls[0] if len(urls)>0 else '<h1>No content found</h1>')
    parse_html_to_md(html)
    gemini_response = await ai_analyzer(model, system_instructions, content)
    print(gemini_response.text)




if __name__ == "__main__":
    # cargamos variables de entorno
    load_dotenv()

    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

    
    asyncio.run(main())
