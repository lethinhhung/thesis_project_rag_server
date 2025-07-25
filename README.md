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
-   🔐 **OAuth2 Authentication System**
-   👤 **User Management & Registration**
-   🛡️ **JWT Token-based Security**
-   🔄 **Refresh Token Support**
-   👥 **Role-based Access Control**

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
# Vector Database Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_pinecone_index_name

# LLM API Configuration
GROQ_API_KEY=your_grok_api_key

# OAuth2 Authentication Configuration
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
```

5. Run the server

```bash
uvicorn server:app --reload
```

## Testing Authentication

A test script is provided to demonstrate the OAuth2 authentication flow:

```bash
# Install requests if not already installed
pip install requests

# Run the test script (make sure the server is running)
python test_auth.py
```

### Manual Testing with cURL

1. **Login to get tokens:**
```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123&grant_type=password"
```

2. **Use the access token in protected endpoints:**
```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

3. **Register a new user:**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com", 
    "password": "password123",
    "full_name": "New User"
  }'
```

## Project Structure

```
RAG/
├── server.py        # Main FastAPI server with OAuth2 endpoints
├── models.py        # Pydantic models for API and authentication
├── auth.py          # Authentication service and utilities
├── dependencies.py  # FastAPI dependencies for authentication
├── test_auth.py     # OAuth2 authentication test script
├── requirements.txt # Python dependencies
├── .env.example     # Environment variables template
└── README.md        # This documentation
```

## API Documentation

### Base URL

```
http://localhost:8000
```

## Authentication

This API uses OAuth2 with JWT tokens for authentication. All endpoints (except authentication endpoints) require a valid access token.

### Default Admin User

For testing purposes, a default admin user is created:
- **Username:** `admin`
- **Password:** `admin123`
- **Email:** `admin@example.com`

### Authentication Flow

1. **Register** a new user or use the default admin
2. **Login** to get access and refresh tokens
3. **Use access token** in Authorization header: `Bearer <access_token>`
4. **Refresh token** when access token expires
5. **Logout** to revoke tokens

### Endpoints

#### Authentication Endpoints

#### 1. Register User

```http
POST /auth/register
```

**Description:** Register a new user account.

**Request Body:**
```json
{
    "username": "string",
    "email": "user@example.com",
    "password": "string",
    "full_name": "string (optional)",
    "is_active": true
}
```

**Response:**
```json
{
    "id": "string",
    "username": "string",
    "email": "user@example.com",
    "full_name": "string",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
}
```

#### 2. Login (Get Token)

```http
POST /auth/token
```

**Description:** OAuth2 compatible login endpoint to obtain access and refresh tokens.

**Request Body (Form Data):**
```
username=admin
password=admin123
grant_type=password
scope=
```

**Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "refresh_token": "uuid-refresh-token"
}
```

#### 3. Refresh Token

```http
POST /auth/refresh
```

**Request Body:**
```json
{
    "refresh_token": "uuid-refresh-token"
}
```

**Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "refresh_token": "uuid-refresh-token"
}
```

#### 4. Get Current User

```http
GET /auth/me
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "id": "string",
    "username": "string",
    "email": "user@example.com",
    "full_name": "string",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
}
```

#### 5. Logout

```http
POST /auth/logout
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "refresh_token": "uuid-refresh-token"
}
```

#### 6. Logout All Devices

```http
POST /auth/logout-all
```

**Headers:**
```
Authorization: Bearer <access_token>
```

#### 7. List Users (Admin Only)

```http
GET /auth/users
```

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

#### 8. Get User by ID (Admin Only)

```http
GET /auth/users/{user_id}
```

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

#### Core API Endpoints

**Note:** All endpoints below require authentication via `Authorization: Bearer <access_token>` header.

#### 1. Health Check

```http
GET /
```

**Response:**

```json
{
    "message": "Hello World! RAG Server with OAuth2 Authentication"
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

#### 3. Document Ingestion

```http
POST /v1/ingest
```

**Description:** Processes and indexes documents into the vector database for retrieval.

**Headers:**
```
Authorization: Bearer <access_token>
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

**Note:** Users can only ingest documents for their own userId (or admin can access any userId).

**Response:**

```json
{
    "status": "done",
    "chunks_processed": 15
}
```

#### 4. Question Answering

```http
POST /v1/question
```

**Description:** Answers questions using RAG (Retrieval Augmented Generation) based on indexed documents.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**

```json
{
    "userId": "string",
    "query": "string"
}
```

**Note:** Users can only query documents for their own userId (or admin can access any userId).

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

#### 5. Delete Document

```http
POST /v1/delete-document
```

**Description:** Removes all vectors associated with a specific document from the vector database.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**

```json
{
    "documentId": "string",
    "userId": "string"
}
```

**Note:** Users can only delete documents for their own userId (or admin can access any userId).

**Response:**

```json
{
    "deleted_ids": ["doc-1-0", "doc-1-1", "doc-1-2"]
}
```

#### 6. Chat Completions

```http
POST /v1/chat/completions
```

**Description:** Provides chat completions with optional knowledge base integration.

**Headers:**
```
Authorization: Bearer <access_token>
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

**Note:** Users can only access chat completions for their own userId (or admin can access any userId).

**Response:**

-   When `isUseKnowledge: false`: Standard chat completion response
-   When `isUseKnowledge: true`: Chat completion with document references in the `documents` field

#### 7. Streaming Chat Completions (Under development)

```http
POST /v1/chat/streaming-completions
```

**Description:** Similar to chat completions but with streaming response support.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request/Response:** Same format as `/v1/chat/completions`

**Note:** Users can only access streaming completions for their own userId (or admin can access any userId).

### Error Responses

**400 Bad Request (Registration/Validation):**
```json
{
    "detail": "Username already exists"
}
```

**401 Unauthorized (Authentication):**
```json
{
    "detail": "Could not validate credentials",
    "WWW-Authenticate": "Bearer"
}
```

**403 Forbidden (Permission):**
```json
{
    "detail": "Not enough permissions"
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

### Features

-   📝 **Document Processing**: Automatic text cleaning and chunking
-   🔍 **Semantic Search**: Vector-based similarity search using Pinecone
-   🤖 **AI Integration**: Powered by Groq's LLM for response generation
-   📚 **Knowledge Base**: RAG implementation for context-aware responses
-   🎯 **Course Filtering**: Ability to filter search results by course
-   📊 **Document References**: Responses include source document information

## Security Best Practices

### Production Deployment

1. **Environment Variables:**
   - Change the `SECRET_KEY` to a strong, randomly generated key
   - Use environment-specific values for token expiration times
   - Never commit `.env` files to version control

2. **Database:**
   - Replace the in-memory user storage with a proper database (PostgreSQL, MongoDB, etc.)
   - Implement proper password policies and validation
   - Add rate limiting for authentication endpoints

3. **HTTPS:**
   - Always use HTTPS in production
   - Configure proper SSL/TLS certificates
   - Enable HSTS headers

4. **Token Security:**
   - Implement token blacklisting for logout functionality
   - Add refresh token rotation
   - Consider shorter access token expiration times
   - Implement proper token storage on client side

5. **Monitoring:**
   - Log authentication attempts and failures
   - Monitor for suspicious activity
   - Implement proper error handling without exposing sensitive information

### Development vs Production

- **Development:** Uses in-memory storage for simplicity
- **Production:** Should use persistent database storage
- **Default User:** Remove or change default admin credentials in production
