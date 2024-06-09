import json
import re
import requests
from xml.etree import ElementTree as ET
from openai import OpenAI
import tempfile
from dotenv import load_dotenv
load_dotenv()

def extract_json_substring(text):
    # Define the regex pattern to match content between ```json and ```, excluding the markers
    pattern = r'```json\s*(.*?)\s*```'
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        # Extract and return the substring
        return match.group(1).strip()
    else:
        # Return None if no match is found
        return None

def get_about_page(listoflinks):
    client = OpenAI()
    thread = client.beta.threads.create()
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id="asst_EdCxX673x1nFzLPZhlD3yUZW",
        model="gpt-4o",
        instructions="You will be given a list of endpoints of a particular website. You are to provide back the website link that is most likely to be the about page of the website. Return nothing but the link. The list is as follows: "+str(listoflinks)
    )   
    if run.status == "completed":
        messages = client.beta.threads.messages.list(
            thread_id=thread.id,
            run_id=run.id
        )
        link = messages.data[0].content[0].text.value
        return link
    

def get_single_nested_links(sitemap_url):
    """
    Retrieve links from a sitemap.xml with a maximum of single nesting.
    
    :param sitemap_url: URL of the sitemap.xml
    :return: List of filtered URLs
    """
    
    if sitemap_url[-1]!="/":
        sitemap_url += "/"
    if sitemap_url[0:9]!="https://":
        sitemap_url = "https://" + sitemap_url
        
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
        count = loc.count("/")
        if count<4:
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
    
    
def update_vs2(aboutpage):
    client = OpenAI()                
    temp_file_path = save_html_to_tempfile(aboutpage)
    
    file = client.files.create(file=open(temp_file_path, "rb"),purpose="assistants")
    
    vector_store_file = client.beta.vector_stores.files.create(
    vector_store_id="vs_VwMZZPLE2n0cmHr0oqSgFzGL",
    file_id=file.id
    )
    return "success"


    
# Example usage
sitemap_url = "www.loops.so"
single_nested_links = get_single_nested_links(sitemap_url)
print(single_nested_links)

aboutpagelink = get_about_page(single_nested_links)
print(aboutpagelink)


update_vs2(aboutpagelink)

