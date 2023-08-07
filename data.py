import os
import xmltodict
import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import CharacterTextSplitter
import faiss
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
import pickle
from langchain import OpenAI
from langchain.chains import VectorDBQAWithSourcesChain
import argparse
import price

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('.env')

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')


def extract_text_from(url):
    html = requests.get(url).text
    soup = BeautifulSoup(html, features="html.parser")
    text = soup.get_text()

    lines = (line.strip() for line in text.splitlines())
    return '\n'.join(line for line in lines if line)


# r = requests.get("https://www.saatva.com/sitemap.xml")
r = requests.get(
    "https://www.xml-sitemaps.com/download/www.saatva.com-748752b55/sitemap.xml?view=1")
xml = r.text
raw = xmltodict.parse(xml)

pages = []

# crawler price of the mattress
url_list = price.get_url()
for u in url_list:
    pages.append({'text': price.get_data(u), 'source': u})

# crawler other information
for info in raw['urlset']['url']:
    # info example: {'loc': 'https://www.paepper.com/...', 'lastmod': '2021-12-28'}
    url = info['loc']
    if 'https://www.saatva.com/mattresses' in url:
        pages.append({'text': extract_text_from(url), 'source': url})
    if 'https://www.saatva.com/furniture' in url:
        pages.append({'text': extract_text_from(url), 'source': url})
    if 'https://www.saatva.com/bedding' in url:
        pages.append({'text': extract_text_from(url), 'source': url})
    if 'https://www.saatva.com/bundle' in url:
        pages.append({'text': extract_text_from(url), 'source': url})
    if 'https://www.saatva.com/bases' in url:
        pages.append({'text': extract_text_from(url), 'source': url})

# print(pages)

text_splitter = CharacterTextSplitter(
    separator="\n", chunk_size=1500, chunk_overlap=300)
docs, metadatas = [], []
for page in pages:
    splits = text_splitter.split_text(page['text'])
    docs.extend(splits)
    metadatas.extend([{"source": page['source']}] * len(splits))
    print(f"Split {page['source']} into {len(splits)} chunks")

store = FAISS.from_texts(docs, OpenAIEmbeddings(
    openai_api_key=OPENAI_API_KEY), metadatas=metadatas)
with open("faiss_store.pkl", "wb") as f:
    pickle.dump(store, f)
