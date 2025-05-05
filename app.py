from fastapi import FastAPI, HTTPException
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

from api import chatbot  # Import router
from models.query_model import QueryRequest
from core.db import messages_collection

from mangum import Mangum

# # === Load Env ===
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_BASE"] = os.getenv("OPENAI_API_BASE")

# # === App ===
app = FastAPI()
lambda_handler = Mangum(app)
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

# # === LLM & Vector DB Setup for Scope Checking ===
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


# # === Scope Checker ===
def is_in_scope(query: str) -> bool:
    result = qa_chain.invoke(
        {"query": f"Is this query related to food delivery app support? '{query}'"}
    )
    print("Scope Check Response:", result["result"])
    return "yes" in result["result"].lower()


# # === Models ===
class ChatRequest(BaseModel):
    user_id: str
    query: str


class ChatResponse(BaseModel):
    response: str


@app.get("/")
def root():
    return {"message": "Application running!"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_route(req: ChatRequest):
    try:
        if is_in_scope(req.query):
            # Delegate to agent-based chatbot
            response = await chatbot.chat_with_bot(QueryRequest(user_query=req.query))

            return ChatResponse(response=response["response"])
        else:
            return ChatResponse(
                response="I'm here to assist only with food delivery app support-related questions."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


from fastapi import HTTPException
from bson import ObjectId


@app.get("/api/chats/sender/{user_id}/{sender_id}", response_model=list)
def get_chats_by_sender(sender_id: str, user_id: str):
    try:
        print(f"sender_id: {sender_id}, user_id: {user_id}")
        sender_docs = (
            messages_collection.find({"sender": sender_id, "recipient": user_id})
            .sort("timestamp", -1)
            .limit(10)
            .to_list()
        )

        user_docs = (
            messages_collection.find({"recipient": sender_id, "sender": user_id})
            .sort("timestamp", -1)
            .limit(10)
            .to_list()
        )

        ##sorting sender docs and user docs together
        docs = sorted(
            sender_docs + user_docs, key=lambda x: x["timestamp"], reverse=True
        )  # Sort by created_at

        print(f"Found {len(docs)} documents")
        chats = []
        for chat in docs:
            chat["_id"] = str(chat["_id"])  # Convert ObjectId to string
            chats.append(chat)
        return chats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recent_chats/{user_id}", response_model=list)
def get_recent_chats(user_id: str):
    try:
        query = {"$or": [{"recipient": user_id}, {"sender": user_id}]}
        docs = messages_collection.find(query).sort("timestamp", -1).limit(10).to_list()

        # print(f"Found {docs.count()} documents")

        chat_ids = set()
        for chat in docs:
            chat_ids.add(chat["sender"])
            chat_ids.add(chat["recipient"])

        # Remove the current user_id from the set if needed
        chat_ids.discard(user_id)

        return list(chat_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
