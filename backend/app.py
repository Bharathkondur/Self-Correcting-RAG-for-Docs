import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
try:
    from langchain_ollama import OllamaEmbeddings
except ImportError:
    OllamaEmbeddings = None

from rag_graph import build_graph
from logging_config import setup_logging, get_logger

# Configure Logging
setup_logging()
logger = get_logger(__name__)

app = FastAPI(title="Self-Correcting RAG API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
vectorstore = None
rag_app = None

class ChatRequest(BaseModel):
    question: str
    temperature: float = 0.5

def get_embeddings():
    if os.environ.get("OPENAI_API_KEY"):
        logger.info("Using OpenAI Embeddings")
        return OpenAIEmbeddings()
    else:
        logger.info("Using Ollama Embeddings (nomic-embed-text)")
        # Make sure the user has this model: 'ollama pull nomic-embed-text'
        return OllamaEmbeddings(model="nomic-embed-text")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global vectorstore, rag_app
    
    try:
        # Save temp file
        file_location = f"temp_{file.filename}"
        with open(file_location, "wb+") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Load and Split
        loader = PyPDFLoader(file_location)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=300, chunk_overlap=50
        )
        doc_splits = text_splitter.split_documents(docs)
        
        # Embed and Store
        embedding_model = get_embeddings()

        vectorstore = FAISS.from_documents(
            documents=doc_splits,
            embedding=embedding_model,
        )
        
        # Build the graph with the new retriever
        retriever = vectorstore.as_retriever()
        rag_app = build_graph(retriever)
        
        # Cleanup
        os.remove(file_location)
        
        return {"message": "File processed and indexed successfully", "count": len(doc_splits)}
        
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    global rag_app
    
    logger.info(f"Received chat request: {request.question}")
    
    if not rag_app:
        logger.error("RAG App not initialized")
        raise HTTPException(status_code=400, detail="Please upload a document first.")
    
    inputs = {"question": request.question}
    
    try:
        logger.info("Invoking RAG Graph...")
        result = rag_app.invoke(inputs)
        logger.info("RAG Graph Finished.")
        
        answer = result.get("generation", "No answer generated.")
        logger.info(f"Answer generated: {answer[:50]}...")
        
        return {
            "answer": answer,
            "trace": "Trace logic would go here",
            "final_question": result.get("question")
        }
    except Exception as e:
        logger.error(f"Error in RAG execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Mount Frontend
# We assume the frontend folder is at ../frontend relative to this file?
# Actually, the file is in backend/app.py, so frontend is ../frontend
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
