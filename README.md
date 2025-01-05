<p align="center">
    <h1>🏰🔮 BG3Chat - Baldur's Gate 3-Wiki Chatbot</h1>
</p>

Welcome to BG3Chat! This educational project is designed to help fans of the game find the information they need quickly and easily. It's a simple tool, but one that I hope you'll find useful.

https://github.com/SimonB97/BG3Chat/assets/102378134/5940ad30-72ed-47e3-9a3a-3f9ea1eb0697

## 🤔 What is this?

BG3Chat is a chatbot that uses a combination of web scraping and retrival augmented generation (RAG) to provide answers to questions about the game Baldur's Gate 3. It scrapes content about Baldur's Gate 3 from [bg3.wiki](https://bg3.wiki/), builds an index, and generates responses to user queries based on this indexed content. 

## 🚀 Quick Start

Quick and easy access at:

☛ [bg3chat.streamlit.app](https://bg3chat.streamlit.app/) ☚

If you want to run the app locally to make changes or update the index, please follow the installation and usage instructions below.

## 🔧 Installation

To get started, you'll need to clone this repository to your local machine. From there, you can install the necessary dependencies using pip:

```bash
pip install -r requirements.txt
```

You'll also need to provide your OpenAI API key, which you can get from the [OpenAI website](https://platform.openai.com/account/api-keys).

## 💬 Usage

Once you've installed the necessary dependencies you can start the chatbot by running the `bg3_chat.py` script:

```bash
streamlit run BG3Chat.py
```

This will start the Streamlit server and open the chatbot in your web browser.

## 📝 Updating the Indexed Wiki Content

If you want to update the indexed wiki content, you can simply remove the `scraped_text_https___bg3_wiki_.txt` file and the `https___bg3_wiki_` folder. The chatbot will automatically re-scrape the wiki and re-index the content the next time you run it. Keep in mind that this queries the OpenAI API, so you may incur additional costs if you do this frequently. 💸

## 🛠️ Customizing the Chatbot

On the left side of the chatbot interface, you'll find a sidebar where you can customize your chatbot experience. 

- **OpenAI API Key**: Enter your OpenAI API key here. This is necessary for the chatbot to function.
- **Summarize Chain Type**: This option allows you to pick how the chatbot processes and presents the information it finds:
  - **Stuff**: Quick mode with answers based on a limited number of sources.
  - **Map-reduce**: A more thorough mode that takes a bit longer but can summarize any number of sources.
  - **Refine**: Ideal for detailed questions, it takes longer but ensures accuracy by examining any number of sources in-depth.

- **Model**: Select the OpenAI model the chatbot uses to generate responses. Options include 'gpt-3.5-turbo-0613', 'gpt-3.5-turbo-16k', and 'gpt-4-0613'.
- **Number of documents retrieved per wiki search**: Use the slider to adjust the number of documents the AI Agent retrieves for each index search. More documents can provide more comprehensive answers, but may also slow down response time and lead to higher costs for OpenAI API usage.

Remember to click 'Clear Message History' if you want to start a new conversation.

## 👥 Contributing

Contributions are always welcome!

## 🙏 Acknowledgements

I'd like to express my gratitude to the team behind the Baldur's Gate 3 Wiki. Their dedication to compiling and organizing a vast amount of information about the game has made this project possible. The chatbot relies heavily on the content provided by the BG3 Wiki, and I am deeply appreciative of their efforts.

## 🔑 License

This project is licensed under the Attribution-NonCommercial-ShareAlike 4.0 International ([CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)) license. You are free to share, copy, redistribute, remix, transform, and build upon the material, as long as you follow the license terms.

## 💭 Final Thoughts

This project is a humble attempt to make the vast world of Baldur's Gate 3 a little more accessible. It's not perfect, and there's always room for improvement. But I hope it can help you in your journey through the game. Enjoy!
