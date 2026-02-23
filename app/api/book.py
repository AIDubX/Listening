from fastapi import APIRouter, HTTPException
import json
from pathlib import Path
from typing import List, Dict, Any

router = APIRouter()

def load_book_data() -> List[Dict[str, Any]]:
    try:
        book_file = Path("configs/book.json")
        if not book_file.exists():
            raise FileNotFoundError("Book configuration file not found")
        
        with open(book_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading book data: {str(e)}")

@router.get("/books")
async def get_books():
    """
    获取所有推书信息
    """
    return load_book_data()

@router.get("/books/latest")
async def get_latest_books():
    """
    获取最新的推书信息
    """
    books = load_book_data()
    if not books:
        return []
    return books[0]  # 返回最新日期的推书信息 