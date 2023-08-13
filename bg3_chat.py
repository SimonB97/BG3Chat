"""
BG3Chat.py

This module contains the implementation of a chatbot for the Baldur's Gate 3 Wiki. 
The chatbot uses the Langchain library to scrape the wiki, build an index of the content, 
and generate responses to user queries based on the indexed content. 

The chatbot is designed to be used with the Streamlit library for a user-friendly interface. 
It also uses the OpenAI API for generating responses and the BeautifulSoup library for web scraping.

The chatbot's functionality includes:
- Scraping the Baldur's Gate 3 Wiki
- Building an index of the scraped content
- Generating responses to user queries based on the indexed content
- Displaying the chatbot interface using Streamlit
"""

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
from langchain.agents.agent_toolkits import (
    create_retriever_tool, create_conversational_retrieval_agent
)
from langchain.schema import BaseRetriever
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langsmith import Client
from openai.error import InvalidRequestError
from bs4 import BeautifulSoup as Soup

# Langsmith (only for tracing)
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "BG3Chat Tracing"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = "ls__6bf8445da91340fbae4da511452a2a65"
client = Client()

# URL to scrape
URL = 'https://baldursgate3.wiki.fextralife.com/'
# turn url into indexname (remove special characters)
indexname = re.sub('[^a-zA-Z0-9]', '_', URL)

msgs = StreamlitChatMessageHistory()
memory = ConversationBufferMemory(
    memory_key="chat_history", chat_memory=msgs, return_messages=True)
if len(msgs.messages) == 0:
    msgs.add_ai_message("How can I help you?")

# Page title
st.set_page_config(page_title="🦜🔗 Baldur's Gate 3-Wiki Chatbot")
st.sidebar.title("🦜🔗 Baldur's Gate 3-Wiki Chatbot")


def scrape_url(link):
    """
    This function scrapes the content of a given URL.

    Parameters:
    link (str): The URL to be scraped.

    Returns:
    cleaned_text (str): The scraped and cleaned text from the URL.
    """

    print(f"Scraping {link}...")
    loader = RecursiveUrlLoader(
        url=link,
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
    with open(f"scraped_text_{indexname}.txt", 'w', encoding='utf-8') as file:
        file.write(cleaned_text)
    return cleaned_text


def build_index(text):
    """
    This function builds an index from the scraped text.

    Parameters:
    text (str): The scraped and cleaned text from the URL.

    Returns:
    database (FAISS): The built index from the text.
    """

    print("Building index...")
    # split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200, chunk_overlap=120)
    splits = text_splitter.split_text(text)
    # build index
    index_embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    database = FAISS.from_texts(splits, index_embeddings)
    database.save_local(indexname)
    return database


def create_retriever_tool(
    llm: ChatOpenAI, retriever: BaseRetriever, name: str, description: str
) -> Tool:

    def retrieve_and_combine_documents(query):
        pass

    return Tool(
        name=name, description=description, func=retriever.get_relevant_documents
    )


def create_agent(database):
    """
    This function creates an agent for retrieving and generating responses.

    Parameters:
    database (FAISS): The built index from the text.

    Returns:
    a_executor (AgentExecutor): The created agent executor.
    """

    print("Creating agent...")
    retriever = database.as_retriever(search_kwargs={'k': num_docs})
    llm = ChatOpenAI(
        model=model,
        temperature=0,
        openai_api_key=openai_api_key,
        streaming=True
    )
    tool_description = "Searches and returns documents regarding the Baldur's Gate 3 Wiki \
        by using similarity search on embeddings of query and documents, \
        so put in query that represents shortened optimal docs for answering. \
        Use whenever you need to find information about the game, to make sure \
        your answers are accurate."
    tool = create_retriever_tool(
        llm,
        retriever,
        "search_baldurs_gate_3_wiki",
        tool_description
    )
    tools = [tool]
    system_message = SystemMessage(
        content="Yor are a helpful Assistant that is here to help the user find information \
            about the game. Answer the question with the tone and style of Astaarion from \
            Baldur's Gate 3. Always make sure to provide accurate information by searching the \
            Baldur's Gate 3 Wiki whenever the user asks a question about the game. Make sure to \
            perform multiple searches using slightly different queries to make sure you find the \
            most relevant information."
    )
    a_executor = create_conversational_retrieval_agent(
        llm,
        tools,
        system_message=system_message,
        remember_intermediate_steps=False
    )
    a_executor.memory = memory
    return a_executor


def generate_response(a_executor, input_query):
    """
    This function generates a response to a given input query using the agent executor.

    Parameters:
    a_executor (AgentExecutor): The agent executor used to generate the response.
    input_query (str): The input query to generate a response for.

    Returns:
    response (str): The generated response to the input query.
    """

    print("Generating response...")
    try:
        # generate response
        response = a_executor(
            input_query,
            callbacks=[st_callback]
        )['output']
        print(f"\nResponse: \n\n{response}")
        return response
    except InvalidRequestError as error:
        # Convert the exception to a string to get the error message
        error_message = str(error)
        # Extract the number of tokens from the error message
        match = re.search(
            r"your messages resulted in (\d+) tokens", error_message)
        if match:
            num_tokens = match.group(1)
        else:
            num_tokens = "an unknown number of"

        # Custom warning message
        context_size = str(
            4097 if model == "gpt-3.5-turbo-0613"
            else 8191 if model == "gpt-4-0613"
            else 16384 if model == "gpt-3.5-turbo-16k"
            else "an unknown (but too small) number of"
        )
        warning_message = f"Your input resulted in too many tokens for the model to handle. \
            The model's maximum context length is {context_size} tokens, but your messages resulted \
            in {num_tokens} tokens. Please reduce the number of documents returned by the search \
            (slider on the left) or the length of your input or use a model with larger context \
            window and try again."
        st.warning(warning_message)
        return None


# Input Widgets
st.sidebar.header("Chatbot Settings")
openai_api_key = st.sidebar.text_input('OpenAI API Key', type='password')
chain_type = st.sidebar.selectbox(
    'Chain Type', ['stuff', 'refine'], disabled=not openai_api_key.startswith('sk-'))
st.sidebar.info(
    'stuff ⇒ faster, less accurate  \nrefine ⇒ slower, more accurate')
model = st.sidebar.selectbox('Model', ['gpt-3.5-turbo-0613', 'gpt-3.5-turbo-16k',
                             'gpt-4-0613'], disabled=not openai_api_key.startswith('sk-'))
num_docs = st.sidebar.slider(
    'Number of documents retrieved per wiki search', 1, 50, 10)

# App Logic
if not openai_api_key.startswith('sk-'):
    st.warning('Please enter your OpenAI API key!', icon='⚠')
if openai_api_key.startswith('sk-'):
    placeholder = st.empty()

    # check if the scraped text file exists
    if os.path.exists(f'scraped_text_{indexname}.txt'):
        print("text file exists, loading...")
        with open(f"scraped_text_{indexname}.txt", 'r', encoding='utf-8') as f:
            scraped_text = f.read()
    else:
        print("text file doesn't exist, scraping...")
        placeholder.info('Scraping data...')
        scraped_text = scrape_url(URL)
        placeholder.empty()

    # check if the index exists
    if os.path.isdir(indexname):
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        vectordb = FAISS.load_local(indexname, embeddings)
    else:
        # if the directory doesn't exist, rebuild the index
        placeholder.info('Building index...')
        vectordb = build_index(scraped_text)
        placeholder.empty()

    agent_executor = create_agent(vectordb)
    for msg in msgs.messages:
        st.chat_message(msg.type).write(msg.content)

    if query_text := st.chat_input():
        st.chat_message("human").write(query_text)
        with st.chat_message("assistant"):
            st_callback = StreamlitCallbackHandler(st.container())
            generated_response = generate_response(agent_executor, query_text)
            st.write(generated_response)
