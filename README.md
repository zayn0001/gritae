
# Case Study Matcher

The problem is in the context of a seller trying to sell their product to a company (prospect) and trying to find relevant case studies that they can reference when pitching their product.


It takes 3 inputs

- Seller website url
- Seller case-studies page url
- Prospect website url



The Output

- It gives the case study that best matches the goals of the prospect and also 3 reasons why this case study is worth going through by the prospect. This will help the seller draft an email better to market their services.




## Installation

```python
  pip install -r requirements.txt 
  python env-creator.py
  streamlit run server.py
```
    
## Demo

[https://gritae-assignment.streamlit.app/](https://gritae-assignment.streamlit.app/)


## Run Locally

Clone the project

```bash
  git clone https://github.com/zayn0001/gritae.git
```

Go to the project directory

```bash
  cd my-project
```

Install dependencies

```bash
  pip install -r requirements.txt 
```

Initialize environment variables

```bash
  python env-creator.py
```


Start the server

```bash  
  streamlit run server.py
```


## How it works

**PART A ( Handling the case studies )**


- Get the sitemap link of the company website at /sitemap.xml
- Using regex extract all the links that start with the case studies page url. This leaves us with all the nested endpoints of the case studies page, i.e, the case studies.
- For each case study, generate the HTML, and store in a temporary file using tempfile library
- Store these HTML files into your OpenAI vector store 

**PART B ( Handling the prospect )**

- Get the sitemap link of the prospect website at /sitemap.xml.
- Using regex extract all the links that are singly nested ( /homepage, /about, etc. ) one of which has to be about page.
- Using an OpenAI assistant, provide the list of links and extract the one that is most likely to be of the about page.
- Get the HTML contents of the about page.
- Extract all the text from the HTML and store in a string.
- Using an OpenAI assistant, provide the text contents string, and generate a summary of the prospect's goals and services.

**PART C ( Final Result )**

- Using the main assistant that has access to the vector store created in PART A, provide the summary in the prompt and generate the relevant case study


## Screenshots
![App Screenshot](https://github.com/zayn0001/gritae/blob/main/sample.png)


## License

[MIT](https://choosealicense.com/licenses/mit/)

