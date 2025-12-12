# RAG Server Python

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
-   🔐 **OAuth2 JWT Authentication System**
-   👤 **User Registration and Login**
-   🛡️ **Protected API Endpoints**
-   🔑 **Role-based Access Control**

## Tech Stack

-   Python 3.8+
-   FastAPI
-   LangChain
-   Uvicorn
-   **JWT Authentication (PyJWT)**
-   **Password Hashing (Passlib + Bcrypt)**
-   **OAuth2 Security**

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
# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_pinecone_index_name

# Groq API Configuration
GROQ_API_KEY=your_groq_api_key

# JWT Authentication Configuration (REQUIRED)
JWT_SECRET_KEY=your_super_secret_jwt_key_change_this_in_production

# Optional: Override default token expiration (in minutes)
# ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> **Security Note**: Make sure to use a strong, unique `JWT_SECRET_KEY` in production. You can generate one using: `openssl rand -hex 32`

5. Run the server

```bash
uvicorn server:app
```

## Project Structure

```
RAG/
├── server.py          # Main FastAPI server with OAuth2 integration
├── models.py          # Pydantic models and schemas
├── auth.py            # Authentication utilities and JWT functions
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variables template
├── users.json         # User storage file (created automatically)
└── README.md          # Project documentation
```

## API Documentation

### Base URL

```
http://localhost:8000
```

### Endpoints

#### 1. Health Check

```http
GET /
```

**Response:**

```json
{
    "message": "Hello World!"
}
```

#### 2. Keep Alive Health Check

```http
HEAD /v1/keep-alive
```

**Response:**

```json
{
    "status": "healthy"
}
```

## 🔐 Authentication Endpoints

#### 3. User Registration

```http
POST /v1/auth/register
```

**Description:** Register a new user account.

**Request Body:**

```json
{
    "email": "user@example.com",
    "username": "username",
    "password": "securepassword123",
    "full_name": "User Full Name (optional)"
}
```

**Response:**

```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
        "id": "user-uuid",
        "email": "user@example.com",
        "username": "username",
        "full_name": "User Full Name",
        "is_active": true,
        "created_at": "2025-01-25T10:30:00Z",
        "updated_at": "2025-01-25T10:30:00Z"
    }
}
```

#### 4. User Login

```http
POST /v1/auth/login
```

**Description:** Login with email and password.

**Request Body:**

```json
{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

**Response:**

```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
        "id": "user-uuid",
        "email": "user@example.com",
        "username": "username",
        "full_name": "User Full Name",
        "is_active": true,
        "created_at": "2025-01-25T10:30:00Z",
        "updated_at": "2025-01-25T10:30:00Z"
    }
}
```

#### 5. OAuth2 Token Endpoint

```http
POST /v1/auth/token
```

**Description:** OAuth2 compatible token endpoint (form-based login).

**Request Body (form-data):**

```
username=user@example.com
password=securepassword123
```

**Response:** Same as login endpoint.

#### 6. Get Current User Profile

```http
GET /v1/auth/me
```

**Description:** Get current authenticated user profile.

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response:**

```json
{
    "id": "user-uuid",
    "email": "user@example.com",
    "username": "username",
    "full_name": "User Full Name",
    "is_active": true,
    "created_at": "2025-01-25T10:30:00Z",
    "updated_at": "2025-01-25T10:30:00Z"
}
```

## 📚 RAG Endpoints (Protected)

> **🔒 Authentication Required**: All RAG endpoints require a valid JWT token in the `Authorization: Bearer <token>` header.

#### 7. Document Ingestion

```http
POST /v1/ingest
```

**Description:** Processes and indexes documents into the vector database for retrieval.

**Headers:**

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**

```json
{
    "documentId": "string",
    "userId": "string",
    "document": "string",
    "title": "string",
    "courseId": "string (optional)",
    "courseTitle": "string (optional)"
}
```

**Response:**

```json
{
    "status": "done",
    "chunks_processed": 15
}
```

#### 8. Question Answering

```http
POST /v1/question
```

**Description:** Answers questions using RAG (Retrieval Augmented Generation) based on indexed documents.

**Headers:**

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**

```json
{
    "userId": "string",
    "query": "string"
}
```

**Response:**

```json
{
    "id": "string",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "deepseek-r1-distill-llama-70b",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "string",
                "documents": [
                    {
                        "id": "string",
                        "text": "string",
                        "documentId": "string",
                        "score": 0.95
                    }
                ]
            },
            "finish_reason": "stop"
        }
    ]
}
```

#### 9. Delete Document

```http
POST /v1/delete-document
```

**Description:** Removes all vectors associated with a specific document from the vector database.

**Headers:**

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**

```json
{
    "documentId": "string",
    "userId": "string"
}
```

**Response:**

```json
{
    "deleted_ids": ["doc-1-0", "doc-1-1", "doc-1-2"]
}
```

#### 10. Chat Completions

```http
POST /v1/chat/completions
```

**Description:** Provides chat completions with optional knowledge base integration.

**Headers:**

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**

```json
{
    "messages": [
        {
            "role": "user|assistant|system",
            "content": "string"
        }
    ],
    "model": "string (optional, default: deepseek-r1-distill-llama-70b)",
    "userId": "string",
    "isUseKnowledge": "boolean (optional, default: false)",
    "courseId": "string (optional)",
    "courseTitle": "string (optional)"
}
```

**Response:**

-   When `isUseKnowledge: false`: Standard chat completion response
-   When `isUseKnowledge: true`: Chat completion with document references in the `documents` field

#### 11. Streaming Chat Completions (Under development)

```http
POST /v1/chat/streaming-completions
```

**Description:** Similar to chat completions but with streaming response support.

**Headers:**

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request/Response:** Same format as `/v1/chat/completions`

### Error Responses

**400 Bad Request (Registration):**

```json
{
    "detail": "Email already registered"
}
```

**401 Unauthorized:**

```json
{
    "detail": "Invalid authentication credentials",
    "headers": {"WWW-Authenticate": "Bearer"}
}
```

**403 Forbidden:**

```json
{
    "detail": "Access denied: Cannot access documents for other users"
}
```

**404 Not Found:**

```json
{
    "detail": "Không tìm thấy vectors nào với documentId này."
}
```

**500 Internal Server Error:**

```json
{
    "detail": "Error message details"
}
```

## 🔐 Authentication & Security

This RAG server implements a complete OAuth2 authentication system with JWT tokens:

### Authentication Flow

1. **Register** a new user account (`POST /v1/auth/register`)
2. **Login** to receive a JWT access token (`POST /v1/auth/login`)
3. **Include the token** in all API requests: `Authorization: Bearer <token>`
4. **Access protected endpoints** with your authenticated user context

### Security Features

-   🔐 **JWT-based Authentication**: Secure token-based authentication
-   🔒 **Password Hashing**: Bcrypt hashing for secure password storage
-   👤 **User Isolation**: Users can only access their own documents and data
-   ⏰ **Token Expiration**: Configurable token expiration times
-   🛡️ **CORS Support**: Cross-origin resource sharing configuration
-   🔑 **OAuth2 Compliance**: Standard OAuth2 Bearer token implementation

### User Data Isolation

Each user has their own:
- **Document namespace** in Pinecone vector database
- **Access control** preventing cross-user data access
- **Profile management** with personal information

### Features

-   📝 **Document Processing**: Automatic text cleaning and chunking
-   🔍 **Semantic Search**: Vector-based similarity search using Pinecone
-   🤖 **AI Integration**: Powered by Groq's LLM for response generation
-   📚 **Knowledge Base**: RAG implementation for context-aware responses
-   🎯 **Course Filtering**: Ability to filter search results by course
-   📊 **Document References**: Responses include source document information
-   🔐 **Complete OAuth2 System**: Full user authentication and authorization
-   👥 **Multi-user Support**: Isolated user environments and data
