from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import requests
from pinecone import Pinecone, ServerlessSpec
from groq import Groq
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv

from models import IngestPayload, QuestionPayload, DeletePayload, ChatCompletionPayload

# Load environment variables
load_dotenv()
app = FastAPI()

# Pinecone init
pc = Pinecone(
    api_key=os.getenv("PINECONE_API_KEY")
)

index_name = os.getenv("PINECONE_INDEX_NAME")

# Groq init
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

# Define the text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ".", " ", ""]
)

# Check if the index exists, if not create it
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

# Connect to the index
index = pc.Index(index_name)


# Define endpoints
@app.get("/")
def hello_world():
    return {"message": "Hello World!"}

@app.post("/v1/ingest")
def ingest(payload: IngestPayload):
        
        chunks = text_splitter.split_text(payload.document)

        records = [
            {
                "id": f"{payload.documentId}-{i}",
                "text": chunk,
                'documentId': payload.documentId,
            } for i, chunk in enumerate(chunks)
        ]


        # index.upsert_records(payload.userId, records)

        # return {"status": "done"}
        # Batch size of 90 (below Pinecone's limit of 96)
        batch_size = 90
    
        # Split records into batches and upsert
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            index.upsert_records(payload.userId, batch)

        return {"status": "done", "chunks_processed": len(records)}

@app.post("/v1/question")
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
            "content": "Dựa trên các đoạn văn sau, hãy trả lời câu hỏi (hãy thêm các emoji để trực quan hơn, sử dụng dạng markdown để react-markdown định dạng): " + payload.query 
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

@app.post("/v1/delete-document")
def delete_document(payload: DeletePayload):

    ids_to_delete = list(index.list(prefix=payload.documentId, namespace=payload.userId))

    if not ids_to_delete:
        raise HTTPException(status_code=404, detail="Không tìm thấy vectors nào với documentId này.")

    # Bước 2: Xoá vector theo ID
    index.delete(
        namespace=payload.userId,
        ids=ids_to_delete
    )

    return {"deleted_ids": ids_to_delete}
