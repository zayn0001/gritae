import streamlit as st
from search import *

def process_urls(company, case_studies, prospect, same_vector_store):
    
    if not same_vector_store:
        # Get a list of the case studies pages from the url
        allhrefs = get_case_studies(company, case_studies)

        # Store them in the vector store (empties out the vector store, generate html files from the links, store the html files)
        store_htmls(allhrefs)

    # Get the final redirected url of the prospect 
    final_url = get_final_url(prospect)

    # Get list of singly nested endpoints of the prospect (one of which has to be the about page) (an assumption, albeit a good one)
    listoflinks = get_single_nested_links(final_url)

    # Get the about page url from them (using an openai assistant)
    aboutpage = get_about_page(listoflinks)

    # Get all the text from the about paage and store it in a variable
    text = extract_text_with_line_breaks_from_url(aboutpage)

    # Generate a summary of the company and what it does (using an openai assistant)
    summary = summarize(text)

    # generate the draft (case study name, case study url, case study company url, 3 notable points) (using an openai assistant, but this one has access to the vector store)
    draft = get_draft(summary)
    return draft

st.title("GritAE Assignment (Not working rn cus there was something wrong with the openai api keys, but will run locally tho with your own key)")

company = st.text_input("Company Website URL", value="www.intercom.com")
case_studies = st.text_input("Company Case Studies URL", value="www.intercom.com/customers")
prospect = st.text_input("Prospect Website URL", value="www.loops.so")

same_vector_store = st.checkbox("Is the case studies url and company url the same as the last time you ran this?")

submit_button = st.button("Submit", key="submit_button")

# Add a placeholder for the loading bar
loading_placeholder = st.empty()

# Check if the submit button is clicked
if submit_button:

    with loading_placeholder:
        # Show the loading spinner
        with st.spinner("Processing..."):

            # Call the function to process URLs
            result = process_urls(company, case_studies, prospect, same_vector_store)

    # Show the Output
    st.write(result)

