from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from api import chatbot
from models.query_model import QueryRequest
from core.db import messages_collection, friendrequests_collection, users_collection
from api.auth import auth_router
from api.auth import get_current_user, TokenData
from models.auth import User

# load_dotenv()
# os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
# os.environ["OPENAI_API_BASE"] = os.getenv("OPENAI_API_BASE")

app = FastAPI()
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = ChatOpenAI(model_name="gemma2-9b-it", temperature=0.3, max_tokens=512)
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

VECTOR_DIR = "scope_vector_db"
SCOPE_FILE = "scope_data.txt"

if not os.path.exists(VECTOR_DIR):
    loader = TextLoader(SCOPE_FILE)
    docs = loader.load()
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=200, chunk_overlap=20
    ).split_documents(docs)
    db = FAISS.from_documents(chunks, embedding)
    db.save_local(VECTOR_DIR)
else:
    db = FAISS.load_local(VECTOR_DIR, embedding, allow_dangerous_deserialization=True)

retriever = db.as_retriever()
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, chain_type="stuff")


def is_in_scope(query: str) -> bool:
    result = qa_chain.invoke(
        {"query": f"Is this query related to food delivery app support? '{query}'"}
    )
    print("Scope Check Response:", result["result"])
    return "yes" in result["result"].lower()


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    response: str


@app.get("/")
def root():
    return {"message": "Application running!"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_route(query: ChatRequest, user: User = Depends(get_current_user)):
    try:
        print(f"user_id: {user.email}")
        user_id = users_collection.find_one({"email": user.email})
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")
        response = await chatbot.chat_with_bot(
            QueryRequest(user_query=query.query), str(user_id["_id"])
        )
        print(f"response in chat_route: {response}")
        return ChatResponse(response=response["response"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# @app.post("/api/chat", response_model=ChatResponse)
# async def chat_route(req: ChatRequest, user: User = Depends(get_current_user)):
#     try:
#         if is_in_scope(req.query):
#             # Delegate to agent-based chatbot
#             response = await chatbot.chat_with_bot(QueryRequest(user_query=req.query))

#             return ChatResponse(response=response["response"])
#         else:
#             return ChatResponse(
#                 response="I'm here to assist only with food delivery app support-related questions."
#             )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


from fastapi import HTTPException
from bson import ObjectId


@app.get("/api/chat_history/{friend_id}", response_model=list)
def get_chat_history(friend_id: str, user: TokenData = Depends(get_current_user)):
    try:
        print(f"sender_id: {friend_id}, user_id: {user.email}")
        sender_docs = (
            messages_collection.find({"sender": friend_id, "recipient": user.email})
            .sort("timestamp", +1)
            .limit(10)
            .to_list()
        )

        user_docs = (
            messages_collection.find({"recipient": friend_id, "sender": user.email})
            .sort("timestamp", +1)
            .limit(10)
            .to_list()
        )

        docs = sorted(
            sender_docs + user_docs, key=lambda x: x["timestamp"], reverse=False
        )

        print(f"Found {len(docs)} documents")
        chats = []
        for chat in docs:
            chat["_id"] = str(chat["_id"])
            chats.append(chat)
        return chats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recent_chats", response_model=list)
def get_recent_chats(user: TokenData = Depends(get_current_user)):
    try:
        print(f"user_id: {user.email}")
        friend_requests = list(
            friendrequests_collection.find(
                {
                    "$or": [{"sender": user.email}, {"recipient": user.email}],
                    "accepted": True,
                    "rejected": False,
                }
            )
        )

        chat_ids = []
        for friend in friend_requests:
            if friend["sender"] == user.email:
                chat_ids.append(friend["recipient"])
            else:
                chat_ids.append(friend["sender"])

        return JSONResponse(content=json.loads(json_util.dumps(chat_ids)))
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


from datetime import datetime


@app.post("/api/friend_requests/{friend_id}")
def send_friend_request(friend_id: str, user: TokenData = Depends(get_current_user)):
    try:
        print(f"friend_id: {friend_id}")
        friend = users_collection.find_one({"email": friend_id})
        if not friend:
            raise HTTPException(status_code=404, detail="Friend not found")
        friendrequests_collection.insert_one(
            {
                "sender": user.email,
                "recipient": friend_id,
                "friend_name": user.username,
                "accepted": False,
                "rejected": False,
                "timestamp": datetime.now(),
            }
        )
        return {"message": "Friend request sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/friend_requests/{friend_id}/accept")
def accept_friend_request(friend_id: str, user: TokenData = Depends(get_current_user)):
    try:
        print(f"friend_id: {friend_id}")
        friendrequests_collection.update_one(
            {"recipient": user.email, "sender": friend_id},
            {"$set": {"accepted": True}},
        )
        return {"message": "Friend request accepted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/friend_requests/{friend_id}/reject")
def reject_friend_request(friend_id: str, user: TokenData = Depends(get_current_user)):
    try:
        print(f"friend_id: {friend_id}")
        friendrequests_collection.update_one(
            {"recipient": user.email, "sender": friend_id},
            {"$set": {"rejected": True}},
        )
        return {"message": "Friend request rejected successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from fastapi.responses import JSONResponse
from bson import json_util
import json


@app.get("/api/friend_requests")
def get_friend_requests(user: TokenData = Depends(get_current_user)):
    try:
        print(f"user_id: {user.email}")
        friend_requests = list(
            friendrequests_collection.find(
                {"recipient": user.email, "rejected": False, "accepted": False}
            )
        )
        return JSONResponse(content=json.loads(json_util.dumps(friend_requests)))
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/api/find_friends/{friend_id}")
def find_friends(friend_id: str):
    try:
        print(f"friend_id: {friend_id}")
        friend_docs = list(users_collection.find({"email": friend_id}))
        if len(friend_docs) == 0:
            raise HTTPException(status_code=404, detail="Friend not found")

        return JSONResponse(content=json.loads(json_util.dumps(friend_docs)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


app.include_router(auth_router)
