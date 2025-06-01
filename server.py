from fastapi import FastAPI, Request
from pydantic import BaseModel
import requests
from pinecone import Pinecone, ServerlessSpec
from groq import Groq
from langchain.text_splitter import RecursiveCharacterTextSplitter

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

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ".", " ", ""]
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
    documentId: str
    userId: str
    document: str
    

class QuestionPayload(BaseModel):
    userId: str
    query: str
    
    

@app.post("/ingest")
def ingest(payload: IngestPayload):
        
        chunks = text_splitter.split_text(payload.document)

        records = [
            {
                "id": f"{payload.documentId}-{i}",
                "text": chunk,
                'documentId': payload.documentId,
            } for i, chunk in enumerate(chunks)
        ]

        # records = [
        #     {
        #         "id": "doc-" + payload.documentId,
        #         "text": payload.text,

        #     }
        # ]

        index.upsert_records(payload.userId, records)

        return {"status": "done"}


@app.post("/question")
def question(payload: QuestionPayload):
    # Define the query

    # Search the dense index
    results = index.search(
        namespace=payload.userId,
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
            "content": "Dựa trên các đoạn văn sau, hãy trả lời ngắn gọn câu hỏi: " + payload.query 
            + "\n\n" + "\n".join([hit['fields']['text'] for hit in results['result']['hits']]),
        }
    ],
    model="llama-3.3-70b-versatile",
    )

    response_dict = chat_completion.model_dump()
    response_dict["choices"][0]["message"]["documents"] = [
        {
            "id": hit["_id"],
            "text": hit["fields"]["text"],
            "documentId": hit["fields"]["documentId"],
            "score": hit["_score"]
        } for hit in results['result']['hits']
    ]
    return response_dict

    