import json
import re
from bs4 import BeautifulSoup
import requests
import tempfile
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
ASSISTANT_ID=os.environ["ASSISTANT_ID"]
VECTOR_STORE_ID=os.environ["VECTOR_STORE_ID"]

def get_case_studies(ogurl : str, case_study_url: str):
    #Retrieve all links from the sitemap of the comapny website that starts with the case_study_url, i.e, return all the nested pages of the case studies page
    
    # Ensure the urls are in proper format
    ogurl = fix_url(ogurl)
    case_study_url = fix_url(case_study_url)


    # Get the sitemap link    
    sitemap_url = ogurl + "/sitemap.xml"

    # Get sitemap data or raise error
    response = requests.get(sitemap_url)
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve sitemap: {response.status_code}")
    sitemap_content = response.content

    # Initialise an empty list of links
    nested_links = []
    
    # use a regex pattern that extracts all the links
    loc_pattern = re.compile(r'<loc>(.*?)</loc>')
    loc_urls = loc_pattern.findall(str(sitemap_content))

    for loc in loc_urls:
        loc = fix_url(loc)

        # Check if it is a nested route of the case studies page
        if loc.startswith(case_study_url) and loc != ogurl:
            nested_links.append(loc)

    return nested_links


def fix_url(url):
    # Ensure the urls are in proper format
    
    url = url.strip("/")
    if not url.startswith("https://"):
        url = "https://" + url
    return url


def extract_text_with_line_breaks_from_url(url):
    # Retrieve all the text contents of the html of a page as a string

    # Ensure it is in the proper format
    url = fix_url(url)

    # Fetch the HTML content from the URL
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    html_content = response.text

    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract text with proper line breaks and remove duplicates
    text_with_line_breaks = '. '.join(list(set(soup.stripped_strings)))
    
    return text_with_line_breaks


def save_html_to_tempfile(url):
    #Given a url, saves the html into a Temporary File and returns the file path

    try:
        # Get HTML contents of the page 
        response = requests.get(url)
        response.raise_for_status()

        # Save to Temporary File
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8')
        temp_file.write(response.text)

        temp_file.close()
        print(f'Successfully saved {url} to {temp_file.name}')

        # Return Temp File path
        return temp_file.name
    
    except requests.exceptions.RequestException as e:
        print(f'Failed to retrieve {url}: {e}')
        return None
    

    
def summarize(text):
    #Given a string of text content from the about page of a company, creates a brief summary of the company


    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    my_assistant = client.beta.assistants.create(
        instructions="You are a company goals summarizer",
        name="testing",
        model="gpt-4o",
    )
    thread = client.beta.threads.create()
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=my_assistant.id,
        model="gpt-4o",
        instructions="Provide a brief single paragraph summary on what the following company does given the following sentences in their 'about' page: "+ text
        )
    if run.status == "completed":
        messages = client.beta.threads.messages.list(
            thread_id=thread.id,
            run_id=run.id
        )
        text = messages.data[0].content[0].text.value
        text = re.sub(r'【.*?】', '', text) # Remove unwanted stuff from the text

        # Delete the assistant and the thread after use
        client.beta.assistants.delete(assistant_id=my_assistant.id)
        client.beta.threads.delete(thread_id=thread.id)
        return text
    
def delete_previous_files_in_vs():
    # Delete all files present in the vector store

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    vector_store_files = client.beta.vector_stores.files.list(
    vector_store_id=VECTOR_STORE_ID
    )

    for vector_store_file in vector_store_files:
        deleted = client.beta.vector_stores.files.delete(
            vector_store_id=VECTOR_STORE_ID,
            file_id=vector_store_file.id
        )
        client.files.delete(vector_store_file.id)

def add_files_to_vector_store(files):
    # Add a list of files to the vector database

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    # Create client files
    client_files = []
    for path in files:    
        cli =  client.files.create(file=open(path, "rb"),purpose="assistants")
        client_files.append(cli)
        
    # Create vector store files
    for file in client_files:
        vector_store_file = client.beta.vector_stores.files.create(
        vector_store_id=VECTOR_STORE_ID,
        file_id=file.id
        )
    return

def list_of_temp_files(list_of_urls):
    # Convert a list of urls to list of temporary files and return their paths

    temp_files = []
    for href in list_of_urls:
        temp_file_path = save_html_to_tempfile(href)
        if temp_file_path:
            temp_files.append(temp_file_path)
    return temp_files

def store_htmls(list_of_urls):

    # Delete previous files in the vector database
    delete_previous_files_in_vs()

    
    # Create a list of temporary file paths from the lit of urls
    temp_file_paths = list_of_temp_files(list_of_urls)

    # Store the files in the vector database
    add_files_to_vector_store(temp_file_paths)

    return

    

def get_about_page(listoflinks):
    # Given a list of singly nested links return the one that is most likely to be of the about page
    # Can be /about, /who-we-are, /about-us, etc

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    thread = client.beta.threads.create()
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
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
    
 
    
def get_single_nested_links(og_url):
    # Given the company website, return all the singly nested urls, one of these is to be the about page (an assumption, albeit a good one)

    # Ensure it is in the proper format
    fixed_url = fix_url(og_url)
    
    sitemap_url = fixed_url + "/sitemap.xml"

    # Get sitemap contents
    response = requests.get(sitemap_url, allow_redirects=True)
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve sitemap: {response.status_code}")
    sitemap_content = response.content


    single_nested_links = []
    
    # Get all the links that are singly nested, i.e, 'www.intercom.com/customers' and 'www.intercom.com/about' 
    loc_pattern = re.compile(r'<loc>(.*?)</loc>')
    loc_urls = loc_pattern.findall(str(sitemap_content))
    for loc in loc_urls:
        loc = fix_url(loc)
        seperated = loc.replace(fixed_url, "")
        if seperated.count("/")==1:
            single_nested_links.append(loc)

    return single_nested_links

def get_final_url(url):
    # Some pages redirect according to location. For example, 'www.accenture.com' redirects to 'www.accenture.com/in-en'. this function returns the url after redirect

    try:
        url = fix_url(url)
        response = requests.get(url, allow_redirects=True)
        final_url = response.url
        return final_url
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return url
    

def extract_json_substring(text):
    #Extract the json part from an openAI assistant's output

    pattern = r'```json\s*(.*?)\s*```'
    match = re.search(pattern, text, re.DOTALL)
    try:
        if match:
            # Extract and return the substring
            text = match.group(1).strip()
            text = re.sub(r'【.*?】', '', text)
            text = text.replace("```json", "").replace("```","")
            text = json.loads(text)
            return text
        else:
            # Return the same text if no json is found
            return json.loads(text)
    except Exception as e:
        return text
    
def get_draft(summary):
    # Given a summary of the company (extracted from the about page), return the desired output (the comapny url, and the 3 points), using the vector store previously configured

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    thread = client.beta.threads.create()
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
        model="gpt-4o",
        instructions="You have been given HTML documents of case studies for companies done for different companies in the past."
        "I will provide the summary of a company prospect. Find the most similar case study of a company from the documents that are similar to the summary of the prospect and provide 3 reasons why the case study is worth looking into."
        "Provide in json format only and nothing extra." 
        "Example output: {\"case_study\":\"Fundrise\", \"case_study_link\":\"https://www.intercom.com/customers/fundrise\", \"company_link\":\"https://fundrise.com/\", \"similarity\":\"Both fundrise and you company deal in finance and asset management...\"  \"reasons\":[\"We have helped ABC do X more efficiently which also could benefit you because...\", \"We incorporated X into the ABC ecosystem... \", \" We helped ABC do this better, you could use it too.....\"]}"
        "The summary of the company is as follows: " + summary
        )
    if run.status == "completed":
        messages = client.beta.threads.messages.list(
            thread_id=thread.id,
            run_id=run.id
        )
        text = messages.data[0].content[0].text.value
        text = extract_json_substring(text)
        return text


"""
webpage = "www.intercom.com"
case_studies_page = "www.intercom.com/customers"
prospect = 'https://www.loops.so'

final_url = get_final_url(prospect)
print(final_url)
print(prospect.strip("/").split("/")[3::])
allhrefs = get_case_studies(webpage, case_studies_page)
print(allhrefs)
store_htmls(allhrefs)
print(final_url)
listoflinks = get_single_nested_links(final_url)
print(listoflinks)
aboutpage = get_about_page(listoflinks)
print(aboutpage)
text = extract_text_with_line_breaks_from_url(aboutpage)
summary = summarize(text)
print(summary)
draft = get_draft(summary)
"""





