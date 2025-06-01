from fastapi import FastAPI, Request
from pydantic import BaseModel
import requests
from pinecone import Pinecone, ServerlessSpec
from groq import Groq

import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Pinecone init
pc = Pinecone(
    api_key=os.getenv("PINECONE_API_KEY")
    # environment=os.getenv("PINECONE_ENVIRONMENT")
)

index_name = os.getenv("PINECONE_INDEX_NAME")

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)



if not pc.has_index(index_name):
    pc.create_index_for_model(
        name=index_name,
        cloud="aws",
        region="us-east-1",
        embed={
            "model":"llama-text-embed-v2",
            "field_map":{"text": "chunk_text"}
        }
    )

index = pc.Index(index_name)

@app.get("/")
def hello_world():
    return {"message": "Hello World!"}

class IngestPayload(BaseModel):
    text: str
    metadata: dict[str, str]

class QuestionPayload(BaseModel):
    query: str
    
    

@app.post("/ingest")
def ingest(payload: IngestPayload):
    # Bước 1: Gọi Groq API để tạo embedding
    # response = requests.post(
    #     "https://api.groq.com/v1/embeddings",
    #     headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
    #     json={
    #         "model": "nomic-embed-text",
    #         "input": payload.text
    #     }
    # )
    # print(response.json())
    # embedding = response.json()['data'][0]['embedding']

    # Bước 2: Lưu vào Pinecone
    # index.upsert([
    #     ("doc-" + payload.metadata["filename"], embedding, payload.metadata)
    # ])

        metadata_list = [f"{k}:{v}" for k, v in payload.metadata.items()]
        records = [
            {
                "_id": "doc-" + payload.metadata["filename"],
                "text": payload.text,
                "metadata": metadata_list
            }
        ]

        index.upsert_records(index_name, records)

        return {"status": "done"}

@app.post("/question")
def question(payload: QuestionPayload):
    # Define the query

    # Search the dense index
    results = index.search(
        namespace=index_name,
        query={
            "top_k": 10,
            "inputs": {
                'text': payload.query
            }
        }
    )

    # Print the results
    for hit in results['result']['hits']:
            print(f"id: {hit['_id']:<5} | score: {round(hit['_score'], 2):<5} | text: {hit['fields']['text']:<50}")

    chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Dựa trên các đoạn văn sau, hãy trả lời câu hỏi: " + payload.query 
            + "\n\n" + "\n".join([hit['fields']['text'] for hit in results['result']['hits']]),
        }
    ],
    model="llama-3.3-70b-versatile",
    )
    return chat_completion

    