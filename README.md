# RAG Server Python (Ongoing)

A Retrieval Augmented Generation (RAG) server implementation using Python for enhanced question-answering capabilities and document processing.

## Overview

This project implements a RAG system that combines document retrieval with language model generation to provide accurate, context-aware responses. It serves as the AI processing backend for the Study Assistant Platform.

## Features

-   🚀 Document processing and indexing
-   📚 Vector database connection (Pinecone)
-   🔍 Semantic search capabilities (Pinecone)
-   🤖 LLM integration for response generation (Groq)
-   📝 Document embedding and chunking
-   🔄 API integration with main backend
-   🎯 Question answering from documents
-   📊 Text similarity search

## Tech Stack

-   Python 3.8+
-   FastAPI
-   LangChain
-   Uvicorn

## Installation

1. Clone repository

```bash
git clone https://github.com/lethinhhung/thesis_project_rag_server.git
cd thesis_project_rag_server
```

2. Create and activate virtual environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Create environment file
   Create a `.env` file in the root directory and configure:

```env
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_pinecone_index_name
GROQ_API_KEY=your_grok_api_key
```

## Project Structure

```
RAG/
├── server.py   # Main server
```

## API Documentation

🚧 This project is currently under active development.
