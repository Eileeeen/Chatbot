import os
from pathlib import Path
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from langchain import OpenAI, ConversationChain, LLMChain, PromptTemplate
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryBufferMemory
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chat_models import ChatOpenAI
import pickle
import argparse
from langchain.prompts.chat import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('.env')

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get('SLACK_APP_TOKEN')
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")


# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get(SLACK_BOT_TOKEN),
          signing_secret=os.environ.get(SLACK_SIGNING_SECRET))

# Langchain implementation
template = """Assistant is a large language model trained by OpenAI.

    Assistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, Assistant is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.

    Assistant is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Assistant is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.

    Overall, Assistant is a powerful tool that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether you need help with a specific question or just want to have a conversation about a particular topic, Assistant is here to assist.

    {history}
    Human: {human_input}
    Assistant:"""

system_template = """ Use the following pieces of context and to answer the users question.
You are an AI assistant for Saatva website which located at https://www.saatva.com/. 
You can ask more question to ask for more information to answer the question better. 
If you don't know the answer, just say that "Sorry, I don't know", don't try to make up an answer.
----------------
{summaries}"""

messages1 = [
    SystemMessagePromptTemplate.from_template(system_template),
    MessagesPlaceholder(variable_name="history"),
    HumanMessagePromptTemplate.from_template('{question}')
]
qa_prompt = ChatPromptTemplate.from_messages(messages1)

prompt = PromptTemplate(
    input_variables=["history", "human_input"],
    template=template
)

chatgpt_chain = LLMChain(
    llm=OpenAI(temperature=0),
    prompt=prompt,
    verbose=True,
    memory=ConversationBufferWindowMemory(k=2),
)

with open("faiss_store.pkl", "rb") as f:
    store = pickle.load(f)

# qa_chain = load_qa_with_sources_chain(llm=OpenAI(temperature=0), chain_type="stuff",prompt=prompt, memory=ConversationBufferWindowMemory(k=2))

# Modify model_name if you have access to GPT-4
# gpt-3.5-turbo-16k
llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k", temperature=0)
chain_type_kwargs = {
    "prompt": qa_prompt,
    "verbose": True,
    # "memory": ConversationSummaryBufferMemory(llm=llm, max_token_limit=10, return_messages=True),
}
chain = RetrievalQAWithSourcesChain.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=store.as_retriever(),
    return_source_documents=True,
    chain_type_kwargs=chain_type_kwargs,
    memory=ConversationSummaryBufferMemory(
        llm=llm, max_token_limit=10, return_messages=True, input_key="question", output_key="answer"),
    reduce_k_below_max_tokens=True
)


@app.message(".*")
def message_handler(message, say, logger):
    print(message)
    question = message['text']
    # output = chatgpt_chain.predict(human_input=message['text'])
    output = chain({"question": str(question)}, return_only_outputs=True)

    print(f"Sources: {output['sources']}")
    say(output['answer'])
    if (output['sources'] != ""):
        say(output['sources'])


# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
