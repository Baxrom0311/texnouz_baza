"""Texnouz v2 ishga tushirish"""
import os
import sys

# Backend papkasini Python path ga qo'shish
sys.path.insert(0, os.path.dirname(__file__))

import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
        log_level="info",
    )
