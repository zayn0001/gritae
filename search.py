from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from xml.etree import ElementTree as ET
import requests
import os
import tempfile
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def get_case_studies(sitemap_url : str, case_study_url: str):
    """
    Retrieve links from a sitemap.xml with a maximum of single nesting.
    
    :param sitemap_url: URL of the sitemap.xml
    :return: List of filtered URLs
    """
    
    if sitemap_url[-1]!="/":
        sitemap_url += "/"
    if not sitemap_url.startswith("https://"):
        sitemap_url = "https://" + sitemap_url
    
    if case_study_url[-1]!="/":
        case_study_url += "/"
    if not case_study_url.startswith("https://"):
        case_study_url = "https://" + case_study_url
        
    sitemap_url += "sitemap.xml"

    response = requests.get(sitemap_url)
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve sitemap: {response.status_code}")

    sitemap_content = response.content
    root = ET.fromstring(sitemap_content)
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    single_nested_links = []
    
    for url in root.findall('ns:url', namespaces=namespace):
        loc = url.find('ns:loc', namespaces=namespace).text
        if loc.startswith(case_study_url):
            single_nested_links.append(loc)
    return single_nested_links


def save_html_to_tempfile(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8')
        temp_file.write(response.text)
        temp_file.close()
        print(f'Successfully saved {url} to {temp_file.name}')
        return temp_file.name
    except requests.exceptions.RequestException as e:
        print(f'Failed to retrieve {url}: {e}')
        return None

def store_htmls(all_hrefs):
    # List to hold the paths of temporary HTML files
    temp_files = []
    client = OpenAI()
    vector_store_files = client.beta.vector_stores.files.list(
    vector_store_id="vs_VwMZZPLE2n0cmHr0oqSgFzGL"
    )
    print(vector_store_files)
    for vector_store_file in vector_store_files:
                deleted = client.beta.vector_stores.files.delete(
                    vector_store_id='vs_VwMZZPLE2n0cmHr0oqSgFzGL',
                    file_id=vector_store_file.id
                )
                client.files.delete(vector_store_file.id)
                print("deleted",deleted.id)
    # Save HTML content from each href to a temporary HTML file\
    for href in all_hrefs:
        temp_file_path = save_html_to_tempfile(href)
        if temp_file_path:
            temp_files.append(temp_file_path)
    print("Temporary HTML files created:")
    print(temp_files)

    client_files = []
    for path in temp_files:
        cli =  client.files.create(file=open(path, "rb"),purpose="assistants")
        client_files.append(cli)
        print(cli)
        
    print(client_files)
    for file in client_files:
        vector_store_file = client.beta.vector_stores.files.create(
        vector_store_id="vs_VwMZZPLE2n0cmHr0oqSgFzGL",
        file_id=file.id
        )
        print(file.id)



allhrefs = get_case_studies("www.intercom.com", "www.intercom.com/customers")
store_htmls(allhrefs)
print(allhrefs)




