import json
import time
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_html(url):
    """
    Usa un navegador real (Chrome) para cargar la página y ejecutar JS.
    Devuelve el código fuente HTML completo.
    """
    # Configuración de Chrome para que no se abra la ventana (Headless)
    chrome_options = Options()
    # Si quieres ver el navegador abrirse, comenta la línea siguiente:
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)
        
        # Esperamos hasta 10 segundos a que aparezca al menos un enlace (tag 'a')
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "a"))
            )
        except:
            print("  (Warning: Timeout esperando elementos, procesando lo que haya...)")

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



def main():
    # Nombre del fichero con las Url
    urls_file = 'urls.json'

    try:
        with open(urls_file, 'r', encoding='utf-8') as f:
            urls = json.load(f).get('urls', [])
            print(urls)
    except Exception:
        return

    # Palabras claves provisionales
    keywords = ["Junior", "python", "developer", "programador"]
    all_results = []


if __name__ == "__main__":
    main()