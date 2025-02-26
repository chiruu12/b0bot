import sys
import os
from dotenv import load_dotenv
from pinecone import Pinecone , ServerlessSpec
from sentence_transformers import SentenceTransformer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cybernews.CyberNews import CyberNews
load_dotenv()

# configure client
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "cybernews-index"

# Delete the index if it already exists, so as to save storage
if index_name in pc.list_indexes().names():
    pc.delete_index(index_name)
    print(f"Deleted existing index: {index_name}")

# Create or access the index
if index_name not in pc.list_indexes():
    pc.create_index(
        name=index_name, 
        dimension=384, 
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )

# Connect to the index
index = pc.Index(index_name)

namespace = "c2si"

model = SentenceTransformer('all-MiniLM-L6-v2')

# Different types of news
news = CyberNews()

newsBox = dict()

newsBox["general_news"] = news.get_news("general")

newsBox["cyber_attack_news"] = news.get_news("cyberAttack")

newsBox["vulnerability_news"] = news.get_news("vulnerability")

newsBox["malware_news"] = news.get_news("malware")

newsBox["security_news"] = news.get_news("security")

newsBox["data_breach_news"] = news.get_news("dataBreach")   


"""
News Format:

news = {
    "id: ""
    "headlines": "",
    "author": "",
    "fullNews": "",
    "newsURL": "",
    "newsImgURL":
    "newsDate": "",
}

Notice: "id" should be removed before the news is inserted into the database. newsImgURL also not important right now.
"""

# Convert news articles to vectors and upsert into Pinecone
for news_type, articles in newsBox.items():
    for article in articles:
        # Combine headline and full news for embedding
        text = article["headlines"] + " " + article["fullNews"]
        
        # Convert text to vector
        vector = model.encode(text).tolist()  # Ensure the vector is a list
        
        # Prepare the document ID (use unique identifiers from your data)
        document_id = article["id"]
        document_id = str(document_id)
        
        # Prepare metadata
        metadata = {
            "headlines": article["headlines"],
            "author": article["author"],
            "fullNews": article["fullNews"],
            "newsURL": article["newsURL"],
            "newsImgURL": article["newsImgURL"],
            "newsDate": article["newsDate"]
        }
        
        # Upsert the vector with metadata into Pinecone
        index.upsert([(document_id, vector, metadata)] , namespace=namespace)
        
        print(f"Inserted article ID: {document_id} with metadata into index: {index_name}")

