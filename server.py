from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import requests
from pinecone import Pinecone, ServerlessSpec
from groq import Groq
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
import unicodedata
import os
from dotenv import load_dotenv
from datetime import timedelta

from typing import List
from models import (
    IngestPayload, QuestionPayload, DeletePayload, ChatCompletionPayload,
    UserCreate, User, Token, RefreshTokenRequest, LoginRequest
)
from auth import AuthService, ACCESS_TOKEN_EXPIRE_MINUTES
from dependencies import RequireAuth, RequireAdmin, OptionalAuth, validate_user_access

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
            "field_map":{"text": "text"}
        }
    )

# Connect to the index
index = pc.Index(index_name)


# Authentication endpoints
@app.post("/auth/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate):
    """
    Register a new user
    """
    try:
        db_user = AuthService.create_user(user_data)
        return User(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            full_name=db_user.full_name,
            is_active=db_user.is_active,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/auth/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = AuthService.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "scopes": form_data.scopes.split() if form_data.scopes else []
        },
        expires_delta=access_token_expires
    )
    
    refresh_token = AuthService.create_refresh_token(user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token
    }

@app.post("/auth/refresh", response_model=Token)
def refresh_token(refresh_request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    """
    token_data = AuthService.refresh_access_token(refresh_request.refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data

@app.post("/auth/logout")
def logout(refresh_request: RefreshTokenRequest, current_user: User = RequireAuth):
    """
    Logout user by revoking refresh token
    """
    success = AuthService.revoke_refresh_token(refresh_request.refresh_token)
    return {"message": "Logged out successfully" if success else "Token not found"}

@app.post("/auth/logout-all")
def logout_all(current_user: User = RequireAuth):
    """
    Logout from all devices by revoking all refresh tokens
    """
    revoked_count = AuthService.revoke_all_user_tokens(current_user.id)
    return {"message": f"Logged out from {revoked_count} devices"}

@app.get("/auth/me", response_model=User)
def get_current_user_info(current_user: User = RequireAuth):
    """
    Get current user information
    """
    return current_user

@app.get("/auth/users", response_model=List[User])  
def list_users(current_user: User = RequireAdmin):
    """
    List all users (admin only)
    """
    from auth import fake_users_db
    return [
        User(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        for user in fake_users_db.values()
    ]

@app.get("/auth/users/{user_id}", response_model=User)
def get_user_by_id(user_id: str, current_user: User = RequireAdmin):
    """
    Get user by ID (admin only)
    """
    user = AuthService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return User(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

# Define endpoints
@app.get("/")
def hello_world():
    return {"message": "Hello World! RAG Server with OAuth2 Authentication"}

@app.head("/v1/keep-alive")
def health_check():
        return {"status": "healthy"}

@app.post("/v1/ingest")
def ingest(payload: IngestPayload, current_user: User = RequireAuth):
    # Validate user access
    validate_user_access(current_user, payload.userId)
    
    # Clean the text
    def clean_text(text: str) -> str:
        # Loại bỏ đánh số trang
        text = re.sub(r'Page \d+ of \d+', '', text)
        
        # Xóa các markdown đơn giản thừa
        text = re.sub(r'\*\*|__|~~|```', '', text)
        
        # Loại bỏ khoảng trắng đầu cuối từng dòng
        lines = [line.strip() for line in text.splitlines()]
        
        # Loại bỏ các dòng trống thừa (nhiều dòng trống thành 1 dòng trống)
        cleaned_lines = []
        blank_line = False
        for line in lines:
            if line == '':
                if not blank_line:
                    cleaned_lines.append(line)
                blank_line = True
            else:
                cleaned_lines.append(line)
                blank_line = False
        
        # Ghép lại với xuống dòng chuẩn
        cleaned_text = '\n'.join(cleaned_lines)
        
        return cleaned_text.strip()
    
    # Clean the document text
    cleaned_document = clean_text(payload.document)
    
    chunks = text_splitter.split_text(cleaned_document)

    records = [
        {
            "id": f"{payload.documentId}-{i}",
            "text": chunk,
            'documentId': payload.documentId,
            'title': payload.title,
            'courseId': payload.courseId or "",
            'courseTitle': payload.courseTitle or "",
        } for i, chunk in enumerate(chunks)
    ]

    # Batch size of 90 (below Pinecone's limit of 96)
    batch_size = 90

    # Split records into batches and upsert
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        index.upsert_records(payload.userId, batch)

    return {"status": "done", "chunks_processed": len(records)}

@app.post("/v1/question")
def question(payload: QuestionPayload, current_user: User = RequireAuth):
    # Validate user access
    validate_user_access(current_user, payload.userId)
    # Define the query

    # Search the dense index
    results = index.search(
        namespace=payload.userId,
        query={
            "top_k": 15,
            "inputs": {
                'text': payload.query
            }
        }
    )

    # Print the results
    for hit in results['result']['hits']:
            print(f"id: {hit['_id']:<5} | documentId: {hit['fields']['documentId']} | title: {hit['fields']['title']} | score: {round(hit['_score'], 2):<5} | text: {hit['fields']['text']:<50}")
            

    chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": (
                "### 📘 Yêu cầu:\n"
                f"Trả lời câu hỏi sau bằng cách dựa trên các đoạn văn bên dưới. "
                "Nếu thông tin không đủ, hãy trả lời dựa trên kiến thức của bạn và ghi rõ điều đó.\n\n"
                f"**Câu hỏi:** {payload.query}\n\n"
                "### 📚 Đoạn văn tham khảo:\n"
                # + "\n---\n".join([hit['fields']['text'] for hit in results['result']['hits']]) +
                # "\n\n"
                + "\n---\n".join([
                     f"**Đoạn văn {i+1} (Document title: {hit['fields']['title']}):**\n"
                     f"{hit['fields']['text']}\n"
                     for i, hit in enumerate(results['result']['hits'])
                     ]) +
                "### ✏️ Ghi chú khi trả lời:\n"
                "- Trình bày câu trả lời bằng [Markdown] để hệ thống `react-markdown` có thể hiển thị tốt.\n"
                "- Đảm bảo mỗi thông tin được trích dẫn đều có tham chiếu đến **Document title** tương ứng (ví dụ: `[Tài liệu LLM]`m chỉ cần tên tài liệu, không cần ghi Document title).\n"
                "- Thêm emoji phù hợp để làm nổi bật nội dung chính 🧠📌💡.\n"
                "- Nếu câu trả lời không thể rút ra từ đoạn văn, hãy bắt đầu bằng câu: `⚠️ Không tìm thấy thông tin trong đoạn văn, câu trả lời được tạo từ kiến thức nền.`"
            )
        }
    ],
    model="deepseek-r1-distill-llama-70b",
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
def delete_document(payload: DeletePayload, current_user: User = RequireAuth):
    # Validate user access
    validate_user_access(current_user, payload.userId)

    ids_to_delete = list(index.list(prefix=payload.documentId, namespace=payload.userId))

    if not ids_to_delete:
        raise HTTPException(status_code=404, detail="Không tìm thấy vectors nào với documentId này.")

    # Bước 2: Xoá vector theo ID
    index.delete(
        namespace=payload.userId,
        ids=ids_to_delete
    )

    return {"deleted_ids": ids_to_delete}

@app.post("/v1/chat/completions")
def create_chat_completion(payload: ChatCompletionPayload, current_user: User = RequireAuth):
    # Validate user access
    validate_user_access(current_user, payload.userId)

    if not payload.isUseKnowledge:
        try:
            # Convert Pydantic Message models to dictionaries if payload.messages contains them
            messages_for_api = [message.model_dump() for message in payload.messages]

            last_message = messages_for_api[-1] if messages_for_api else None
            # Remove the last message since we'll handle it separately
            messages_for_api = messages_for_api[:-1]

            chat_completion = client.chat.completions.create(
                messages=messages_for_api + [
                     {
                        "role": "user",
                        "content": (
                            "### 📘 Yêu cầu:\n"
                            f"Trả lời câu hỏi sau: {last_message['content']}\n\n"
                            "### ✏️ Ghi chú khi trả lời:\n"
                            "- Trình bày câu trả lời bằng [Markdown] để hệ thống `react-markdown` có thể hiển thị tốt.\n"
                            "- Thêm emoji phù hợp để làm nổi bật nội dung chính 🧠📌💡.\n" 
                            "- Nếu nội dung có thể so sánh hoặc phân loại, hãy sử dụng **bảng Markdown** để trình bày.\n"
                        )
                     }
                ],
                model=payload.model or "deepseek-r1-distill-llama-70b",  # Use model from payload or default
                # You can pass other parameters from payload to the API call if needed
                # e.g., temperature=payload.temperature
                temperature=0.5,
                max_completion_tokens=1024,
                top_p=1,
            )

            return chat_completion
        
        except Exception as e:
            print(f"Error during chat completion: {e}") # For server-side logging
            raise HTTPException(status_code=500, detail=str(e))
        
    else:
         
        messages_for_api = [message.model_dump() for message in payload.messages]

        # Clean the question for the query
        def clean_text(text: str) -> str:
            # 1. Chuyển về chữ thường
            # text = text.lower()

            # 2. Chuẩn hóa Unicode (dùng NFC để ghép dấu)
            text = unicodedata.normalize("NFC", text)

            # 3. Loại bỏ ký tự đặc biệt (giữ lại tiếng Việt và chữ số)
            text = re.sub(r"[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩ"
                        r"òóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]", "", text)

            # 4. Loại bỏ khoảng trắng dư thừa
            text = re.sub(r"\s+", " ", text).strip()

            return text


        # Combine all previous user question into a single string for the query
        combined_question = [message.model_dump() for message in payload.messages]
        combined_question = [message for message in combined_question if message['role'] == 'user']
        combined_question = [message['content'] for message in combined_question]
        combined_question = " ".join(combined_question)
        combined_question = clean_text(combined_question)
        print(combined_question)




        # Search the dense index
        query = {
            "top_k": 15,
            "inputs": {
                # 'text': clean_text(payload.messages[len(payload.messages) - 1].content)
                'text': combined_question
            }
        }
        if payload.courseId:
            query["filter"] = {"courseId": payload.courseId}

        results = index.search(
            namespace=payload.userId,
            query=query
        )
        # results = index.search(
        #     namespace=payload.userId,
        #     query={
        #         "top_k": 15,
        #         "inputs": {
        #             'text': clean_text(payload.messages[len(payload.messages) - 1].content)
        #         },
        #         "filter": {
        #             "courseId": payload.courseId
        #         } if payload.courseId else None
        #     },
        # )

        # Print the results
        # for hit in results['result']['hits']:
        #         print(f"id: {hit['_id']:<5} | documentId: {hit['fields']['documentId']} | title: {hit['fields']['title']} | score: {round(hit['_score'], 2):<5} | text: {hit['fields']['text']:<50}")
                

        chat_completion = client.chat.completions.create(
            messages=messages_for_api + [
                {
                    "role": "user",
                    "content": (
                        "### 📘 Yêu cầu:\n"
                        f"Trả lời câu hỏi sau bằng cách dựa trên các đoạn văn bên dưới. "
                        "Nếu thông tin không đủ, hãy trả lời dựa trên kiến thức của bạn và ghi rõ điều đó.\n\n"
                        f"**Câu hỏi:** {payload.messages[len(payload.messages) - 1].content}\n\n"
                        "### 📚 Đoạn văn tham khảo:\n"
                        + "\n---\n".join([
                            f"**Đoạn văn {i+1} (Document title: {hit['fields']['title']}):**\n"
                            f"{hit['fields']['text']}\n"
                            for i, hit in enumerate(results['result']['hits'])
                        ]) +
                        "### ✏️ Ghi chú khi trả lời:\n"
                        "- Trình bày câu trả lời bằng [Markdown] để hệ thống `react-markdown` có thể hiển thị tốt.\n"
                        "- Đảm bảo mỗi thông tin được trích dẫn đều có tham chiếu đến **Document title** tương ứng (ví dụ: `[Python đại cương]` chỉ cần tựa của tài liệu gốc, không cần ghi đoạn văn nào, không nhắc lại 'Document title' và không nhắc lại tựa tài liệu nếu bị lặp).\n"
                        "- Thêm emoji phù hợp để làm nổi bật nội dung chính 🧠📌💡.\n"
                        "- Nếu nội dung có thể so sánh hoặc phân loại, hãy sử dụng **bảng Markdown** để trình bày.\n"
                        "- Nếu câu trả lời không thể rút ra từ đoạn văn, hãy bắt đầu bằng câu: `⚠️ Không tìm thấy thông tin trong đoạn văn, câu trả lời được tạo từ kiến thức nền.`\n"  
                    )
                }
            ],
            model=payload.model or "deepseek-r1-distill-llama-70b",
        )

        response_dict = chat_completion.model_dump()

        response_dict["choices"][len(response_dict["choices"])-1]["message"]["documents"] = [
            {
                "id": hit["_id"],
                "text": hit["fields"]["text"],
                "documentId": hit["fields"]["documentId"],
                "score": hit["_score"]
            } for hit in results['result']['hits']
        ]
        return response_dict
    

@app.post("/v1/chat/streaming-completions")
def create_streaming_chat_completion(payload: ChatCompletionPayload, current_user: User = RequireAuth):
    # Validate user access
    validate_user_access(current_user, payload.userId)

    if not payload.isUseKnowledge:
        try:
            # Convert Pydantic Message models to dictionaries if payload.messages contains them
            messages_for_api = [message.model_dump() for message in payload.messages]

            last_message = messages_for_api[-1] if messages_for_api else None
            # Remove the last message since we'll handle it separately
            messages_for_api = messages_for_api[:-1]

            chat_completion = client.chat.completions.create(
                messages=messages_for_api + [
                     {
                        "role": "user",
                        "content": (
                            "### 📘 Yêu cầu:\n"
                            f"Trả lời câu hỏi sau: {last_message['content']}\n\n"
                            "### ✏️ Ghi chú khi trả lời:\n"
                            "- Trình bày câu trả lời bằng [Markdown] để hệ thống `react-markdown` có thể hiển thị tốt.\n"
                            "- Thêm emoji phù hợp để làm nổi bật nội dung chính 🧠📌💡.\n" 
                            "- Nếu nội dung có thể so sánh hoặc phân loại, hãy sử dụng **bảng Markdown** để trình bày.\n"
                        )
                     }
                ],
                model=payload.model or "deepseek-r1-distill-llama-70b",  # Use model from payload or default
                # You can pass other parameters from payload to the API call if needed
                # e.g., temperature=payload.temperature
                temperature=0.5,
                max_completion_tokens=1024,
                top_p=1,
            )

            return chat_completion
        
        except Exception as e:
            print(f"Error during chat completion: {e}") # For server-side logging
            raise HTTPException(status_code=500, detail=str(e))
        
    else:
         
        messages_for_api = [message.model_dump() for message in payload.messages]

        # Clean the question for the query
        def clean_text(text: str) -> str:
            # 1. Chuyển về chữ thường
            # text = text.lower()

            # 2. Chuẩn hóa Unicode (dùng NFC để ghép dấu)
            text = unicodedata.normalize("NFC", text)

            # 3. Loại bỏ ký tự đặc biệt (giữ lại tiếng Việt và chữ số)
            text = re.sub(r"[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩ"
                        r"òóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]", "", text)

            # 4. Loại bỏ khoảng trắng dư thừa
            text = re.sub(r"\s+", " ", text).strip()

            return text


        # Combine all previous user question into a single string for the query
        combined_question = [message.model_dump() for message in payload.messages]
        combined_question = [message for message in combined_question if message['role'] == 'user']
        combined_question = [message['content'] for message in combined_question]
        combined_question = " ".join(combined_question)
        combined_question = clean_text(combined_question)
        print(combined_question)




        # Search the dense index
        query = {
            "top_k": 15,
            "inputs": {
                # 'text': clean_text(payload.messages[len(payload.messages) - 1].content)
                'text': combined_question
            }
        }
        if payload.courseId:
            query["filter"] = {"courseId": payload.courseId}

        results = index.search(
            namespace=payload.userId,
            query=query
        )
        # results = index.search(
        #     namespace=payload.userId,
        #     query={
        #         "top_k": 15,
        #         "inputs": {
        #             'text': clean_text(payload.messages[len(payload.messages) - 1].content)
        #         },
        #         "filter": {
        #             "courseId": payload.courseId
        #         } if payload.courseId else None
        #     },
        # )

        # Print the results
        # for hit in results['result']['hits']:
        #         print(f"id: {hit['_id']:<5} | documentId: {hit['fields']['documentId']} | title: {hit['fields']['title']} | score: {round(hit['_score'], 2):<5} | text: {hit['fields']['text']:<50}")
                

        chat_completion = client.chat.completions.create(
            messages=messages_for_api + [
                {
                    "role": "user",
                    "content": (
                        "### 📘 Yêu cầu:\n"
                        f"Trả lời câu hỏi sau bằng cách dựa trên các đoạn văn bên dưới. "
                        "Nếu thông tin không đủ, hãy trả lời dựa trên kiến thức của bạn và ghi rõ điều đó.\n\n"
                        f"**Câu hỏi:** {payload.messages[len(payload.messages) - 1].content}\n\n"
                        "### 📚 Đoạn văn tham khảo:\n"
                        + "\n---\n".join([
                            f"**Đoạn văn {i+1} (Document title: {hit['fields']['title']}):**\n"
                            f"{hit['fields']['text']}\n"
                            for i, hit in enumerate(results['result']['hits'])
                        ]) +
                        "### ✏️ Ghi chú khi trả lời:\n"
                        "- Trình bày câu trả lời bằng [Markdown] để hệ thống `react-markdown` có thể hiển thị tốt.\n"
                        "- Đảm bảo mỗi thông tin được trích dẫn đều có tham chiếu đến **Document title** tương ứng (ví dụ: `[Python đại cương]` chỉ cần tựa của tài liệu gốc, không cần ghi đoạn văn nào, không nhắc lại 'Document title' và không nhắc lại tựa tài liệu nếu bị lặp).\n"
                        "- Thêm emoji phù hợp để làm nổi bật nội dung chính 🧠📌💡.\n"
                        "- Nếu nội dung có thể so sánh hoặc phân loại, hãy sử dụng **bảng Markdown** để trình bày.\n"
                        "- Nếu câu trả lời không thể rút ra từ đoạn văn, hãy bắt đầu bằng câu: `⚠️ Không tìm thấy thông tin trong đoạn văn, câu trả lời được tạo từ kiến thức nền.`\n"  
                    )
                }
            ],
            model=payload.model or "deepseek-r1-distill-llama-70b",
        )

        response_dict = chat_completion.model_dump()

        response_dict["choices"][len(response_dict["choices"])-1]["message"]["documents"] = [
            {
                "id": hit["_id"],
                "text": hit["fields"]["text"],
                "documentId": hit["fields"]["documentId"],
                "score": hit["_score"]
            } for hit in results['result']['hits']
        ]
        return response_dict

