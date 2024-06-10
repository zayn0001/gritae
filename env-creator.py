from openai import OpenAI

openaiapikey = input("OpenAI API KEY: ")
client = OpenAI(api_key=openaiapikey)

vector_store = client.beta.vector_stores.create(
  name="casestudymatcher"
)

assistant = client.beta.assistants.create(
    instructions="You have been given HTML documents of case studies of projects done for different companies in the past."
    " You will be provided the about page of a website of a company that deals in a specific field of IT servicing."
    " You are to provide the name of the company that corresponds to the most similar case study, "
    "and also 3 reasons why that case study is worth going through by the prospect that is, how it could be beneficial for them."
    " in json format only. " 
    "Example output: {\"url\":\"www.ABC.com\", \"points\":[\"We have helped ABC do X more efficiently which also could benefit you as you deal in similar fields\", \"We incorporated X into the ABC ecosystem... \", \" We helped ABC do this better, you could use it too.....\"]}",
    name="casestudymatcher",
    tools=[{"type": "file_search"}],
    model="gpt-4o", 
    tool_resources={
    "file_search": {
      "vector_store_ids": [vector_store.id]
    },
    }
)
print("VECTOR_STORE_ID=" + vector_store.id)
print("ASSISTANT_ID=" + assistant.id)

env_content = f"""\
OPENAI_API_KEY={openaiapikey}
VECTOR_STORE_ID={vector_store.id}
ASSISTANT_ID={assistant.id}
"""

# Write the content to a .env file
with open('.env', 'w') as file:
    file.write(env_content)