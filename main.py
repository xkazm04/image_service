from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import database
import os
import uvicorn
import logging
from routes import api_router
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("image_service")
    
app = FastAPI(
    title="Local Image Service",
    description="Local image generation and processing service",
    version="2.0.0"
)

app.include_router(api_router, prefix="", tags=["Images"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        return {"status": "healthy", "service": "Local Image Service"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
    
@app.on_event("startup")
async def startup_db_client():
    """Initialize database, local storage, and services"""
    database.Base.metadata.create_all(bind=database.engine)
    logger.info("Database tables created")
    
    # Create local storage directories
    storage_dir = os.getenv("LOCAL_STORAGE_PATH", "./storage")
    os.makedirs(storage_dir, exist_ok=True)
    os.makedirs(os.path.join(storage_dir, "images"), exist_ok=True)
    logger.info(f"Local storage initialized at: {storage_dir}")
    
    # Mount static files for serving images
    try:
        app.mount("/storage", StaticFiles(directory=storage_dir), name="storage")
        logger.info("Static file serving enabled for local images")
    except Exception as e:
        logger.warning(f"Could not mount static files: {e}")
    
    # Initialize prompt validation service
    try:
        from services.prompt_validation import get_prompt_validator
        validator = get_prompt_validator()
        ollama_available = await validator.check_ollama_availability()
        
        if ollama_available:
            logger.info("✅ Ollama prompt validation service is available")
        else:
            logger.warning("⚠️  Ollama not available - prompt optimization will be disabled")
            logger.info("   To enable: 1) Install Ollama 2) Run 'ollama serve' 3) Pull model 'ollama pull gpt-oss:20b'")
    except Exception as e:
        logger.warning(f"Failed to initialize prompt validation: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    try:
        from services.unified_generation import get_unified_service
        from services.prompt_validation import close_global_validator
        from services.ollama import close_global_client
        
        # Close services
        service = get_unified_service()
        await service.close()
        
        await close_global_validator()
        await close_global_client()
        
        logger.info("Services cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8003))
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)