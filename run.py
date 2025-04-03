import uvicorn
from app.logging_config import setup_logging

# Initialize centralized logging
setup_logging()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
