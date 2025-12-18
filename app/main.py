from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.schemas import ChatRequest, ChatResponse, IngestResponse
from app.llm.openai import OpenAILLM
from app.memory import MemoryManager
from app.rag import rag_manager
from app.utils.loaders import loader
import logging
import os
import shutil

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM (OpenAI Only)
openai_llm = OpenAILLM()

def get_llm():
    return openai_llm

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main Chat Endpoint.
    1. Retrieve History
    2. Retrieve Context (RAG)
    3. LLM Generation
    4. Save History
    """
    try:
        memory = MemoryManager(request.business_id, request.session_id)
        history = memory.get_history()
        
        # RAG Search
        context = await rag_manager.search(request.business_id, request.message)
        
        llm = get_llm()
        response_text = await llm.generate_response(
            prompt=request.message,
            history=history,
            context=context
        )
        
        # Update Memory
        memory.add_message("user", request.message)
        memory.add_message("assistant", response_text)
        
        return ChatResponse(
            response=response_text,
            session_id=request.session_id,
            business_id=request.business_id
        )

    except Exception as e:
        logger.error(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/text")
async def ingest_text(
    business_id: str = Form(...),
    text: str = Form(...)
):
    await rag_manager.ingest_document(business_id, text, "Manual Text Input")
    return {"status": "success", "message": "Text ingested."}

@app.post("/ingest/url")
async def ingest_url(
    business_id: str = Form(...),
    url: str = Form(...)
):
    try:
        from app.utils.web import web_loader
        from starlette.concurrency import run_in_threadpool
        
        # Run blocking scraping in threadpool
        content = await run_in_threadpool(web_loader.load, url)
        
        await rag_manager.ingest_document(business_id, content, url)
        return {"status": "success", "message": f"Website Content Ingested: {url}"}
    except Exception as e:
        logger.error(f"URL Ingestion Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/ingest/file")
async def ingest_file(
    business_id: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        from starlette.concurrency import run_in_threadpool
        
        # Save temp file
        temp_dir = "temp_ingest"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = f"{temp_dir}/{file.filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Load content (Non-blocking now)
        content = await run_in_threadpool(loader.load, file_path)
        
        if not content:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Could not extract text from file.")
            
        # Ingest
        await rag_manager.ingest_document(business_id, content, file.filename)
        
        # Cleanup
        os.remove(file_path)
        
        return {"status": "success", "message": f"File {file.filename} processed."}

    except Exception as e:
        logger.error(f"Ingest Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
