import os
import re
import streamlit as st
from langchain.callbacks import StreamlitCallbackHandler
from langchain.vectorstores import FAISS
from langchain.document_loaders.recursive_url_loader import RecursiveUrlLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage
from langchain.agents.agent_toolkits import create_retriever_tool, create_conversational_retrieval_agent
from langchain.schema import BaseRetriever
from langchain.tools import Tool
from openai.error import InvalidRequestError
from bs4 import BeautifulSoup as Soup

# Langsmith (only needed for tracing)
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = f"BG3Chat Tracing"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = "ls__6bf8445da91340fbae4da511452a2a65"
from langsmith import Client
client = Client()

# URL to scrape
url = 'https://baldursgate3.wiki.fextralife.com/'
# turn url into indexname (remove special characters)
indexname = re.sub('[^a-zA-Z0-9]', '_', url)

# Page title
st.set_page_config(page_title="🦜🔗 Baldur's Gate 3-Wiki Chatbot")
st.title("🦜🔗 Baldur's Gate 3-Wiki Chatbot")

def scrape_url(url):
    print(f"Scraping {url}...")
    loader = RecursiveUrlLoader(
        url=url, 
        extractor=lambda x: Soup(x, "html.parser").text, 
        prevent_outside=True, 
        max_depth=1
    )
    docs = loader.load()
    # Combine docs
    combined_docs = [doc.page_content for doc in docs]
    text = " ".join(combined_docs)
    # Clean text
    cleaned_text = re.sub('\n{3,}', '\n\n', text)
    # save text to file
    with open(f"scraped_text_{indexname}.txt", 'w', encoding='utf-8') as f:
        f.write(cleaned_text)
    return cleaned_text

def build_index(text):
    print("Building index...")
    # split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=120)
    splits = text_splitter.split_text(text)
    # build index
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vectordb = FAISS.from_texts(splits, embeddings)
    vectordb.save_local(indexname)
    return vectordb

def create_retriever_tool(
    llm: ChatOpenAI, retriever: BaseRetriever, name: str, description: str
) -> Tool:
    
    def retrieve_and_combine_documents(query):
        pass
        

    return Tool(
        name=name, description=description, func=retriever.get_relevant_documents
    )

def create_agent(vectordb):
    print("Creating agent...")
    retriever = vectordb.as_retriever(search_kwargs={'k': num_docs})
    llm = ChatOpenAI(
        model=model,
        temperature=0,
        openai_api_key=openai_api_key, 
        streaming=True
    )
    tool = create_retriever_tool(
        llm,
        retriever, 
        "search_baldurs_gate_3_wiki",
        "Searches and returns documents regarding the Baldur's Gate 3 Wiki by using similarity search on embeddings of query and documents, so put in query that represents shortened optimal docs for answering. Use whenever you need to find information about the game, to make sure your answers are accurate.",
    )
    tools = [tool]
    system_message = SystemMessage(content="Yor are a helpful Assistant that is here to help the user find information about the game. Answer the question with the tone and style of Astaarion from Baldur's Gate 3. Always make sure to provide accurate information by searching the Baldur's Gate 3 Wiki whenever the user asks a question about the game. Make sure to perform multiple searches using slightly different queries to make sure you find the most relevant information.") 
    agent_executor = create_conversational_retrieval_agent(llm, tools, system_message=system_message)
    return agent_executor

def generate_response(agent_executor, input_query):
    print("Generating response...")
    try:
        # generate response
        response = agent_executor(
            input_query,
            callbacks=[st_callback]
        )['output']
        print(f"\nResponse: \n\n{response}")
        return response
    except InvalidRequestError as e:
        # Convert the exception to a string to get the error message
        error_message = str(e)

        # Extract the number of tokens from the error message
        match = re.search(r"your messages resulted in (\d+) tokens", error_message)
        if match:
            num_tokens = match.group(1)
        else:
            num_tokens = "an unknown number of"

        # Custom warning message
        context_size = str(4097 if model == "gpt-3.5-turbo" else 8191 if model == "gpt-4" else "an unknown (but too small) number of")
        warning_message = f"Your input resulted in too many tokens for the model to handle. The model's maximum context length is {context_size} tokens, but your messages resulted in {num_tokens} tokens. Please reduce the number of documents returned by the search (slider on the left) or the length of your input or use a model with larger context window and try again."
        st.warning(warning_message)
        return None




# Input Widgets
st.sidebar.header("Chatbot Settings")
openai_api_key = st.sidebar.text_input('OpenAI API Key', type='password')
chain_type = st.sidebar.selectbox('Chain Type', ['stuff', 'refine'], disabled=not openai_api_key.startswith('sk-'))
model = st.sidebar.selectbox('Model', ['gpt-3.5-turbo', 'gpt-4'], disabled=not openai_api_key.startswith('sk-'))
num_docs = st.sidebar.slider('Number of documents to search', 1, 50, 10)
st.sidebar.info('The "stuff" chain type is faster but less accurate. The "refine" chain type is slower but more accurate.')

# App Logic
if not openai_api_key.startswith('sk-'):
    st.warning('Please enter your OpenAI API key!', icon='⚠')
if openai_api_key.startswith('sk-'):
    st.sidebar.success('OpenAI API key entered!', icon='✅')
    placeholder = st.empty()

    # check if the scraped text file exists
    if os.path.exists(f'scraped_text_{indexname}.txt'):
        print("text file exists, loading...")
        with open(f"scraped_text_{indexname}.txt", 'r', encoding='utf-8') as f:
            scraped_text = f.read()
    else:
        print("text file doesn't exist, scraping...")
        placeholder.info('Scraping data...')
        scraped_text = scrape_url(url)
        placeholder.empty()

    # check if the index exists
    if os.path.isdir(indexname):
        try:
            embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
            vectordb = FAISS.load_local(indexname, embeddings)
        except Exception as e:
            print(f"Length of scraped text: {len(scraped_text)}")
            print(f"An error occurred: {e}")
            placeholder.info('Building index...')
            vectordb = build_index(scraped_text)
            placeholder.empty()
    else:
        # if the directory doesn't exist, rebuild the index
        placeholder.info('Building index...')
        vectordb = build_index(scraped_text)
        placeholder.empty()

    agent_executor = create_agent(vectordb)

    if query_text := st.chat_input():
        st.chat_message("user").write(query_text)
        with st.chat_message("assistant"):
            st_callback = StreamlitCallbackHandler(st.container())
            generated_response = generate_response(agent_executor, query_text)
            st.write(generated_response)
