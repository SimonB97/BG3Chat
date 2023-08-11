import os
import re
import streamlit as st
from langchain.callbacks import StreamlitCallbackHandler
from langchain.vectorstores import FAISS
from langchain.document_loaders.recursive_url_loader import RecursiveUrlLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import SystemMessage
from langchain.agents.agent_toolkits import create_retriever_tool, create_conversational_retrieval_agent
from bs4 import BeautifulSoup as Soup


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

def create_agent(vectordb):
    print("Creating agent...")
    retriever = vectordb.as_retriever(search_kwargs={'k': 6})
    tool = create_retriever_tool(
        retriever, 
        "search_baldurs_gate_3_wiki",
        "Searches and returns documents regarding the Baldur's Gate 3 Wiki. Use whenever you need to find information about the game, to make sure your answers are accurate.",
    )
    tools = [tool]
    llm = ChatOpenAI(
        model="gpt-3.5-turbo", 
        temperature=0, 
        openai_api_key=openai_api_key, 
        streaming=True
    )
    system_message = SystemMessage(content="Yor are a helpful Assistant that is here to help the user find information about the game. Answer the question with the tone and style of Astaarion from Baldur's Gate 3. Always make sure to provide accurate information by searching the Baldur's Gate 3 Wiki whenever the user asks a question about the game.") 
    agent_executor = create_conversational_retrieval_agent(llm, tools, system_message=system_message)
    return agent_executor

def generate_response(agent_executor, input_query):
    print("Generating response...")
    # generate response
    response = agent_executor(
        input_query,
        callbacks=[st_callback]
    )['output']
    print(f"\nResponse: \n\n{response}")
    return response

# Input Widgets
st.sidebar.header("Chatbot Settings")
openai_api_key = st.sidebar.text_input('OpenAI API Key', type='password')
chain_type = st.sidebar.selectbox('Chain Type', ['stuff', 'refine'], disabled=not openai_api_key.startswith('sk-'))
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
