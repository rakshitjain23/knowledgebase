from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
import shutil
import json
from app.content_scraper import ContentScraper
import random

app = FastAPI()

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def ensure_item_format(item, content_type, source_url=None):
    return {
        "title": item.get("title", "Untitled"),
        "content": item.get("content", ""),
        "content_type": content_type,
        "source_url": source_url or item.get("source_url", ""),
        "author": item.get("author", ""),
        "user_id": item.get("user_id", "")
    }

@app.post("/scrape-pdf")
async def scrape_pdf(file: UploadFile = File(...), team_id: str = Form("aline123")):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    scraper = ContentScraper()
    items = scraper.scrape_pdf(temp_path)
    os.remove(temp_path)
    return JSONResponse({
        "team_id": team_id,
        "items": items
    })

@app.post("/scrape-multi-pdf")
async def scrape_multi_pdf(files: List[UploadFile] = File(...), team_id: str = Form("aline123")):
    all_items = []
    scraper = ContentScraper()
    temp_paths = []
    try:
        for file in files:
            temp_path = f"temp_{file.filename}"
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            temp_paths.append(temp_path)
            items = scraper.scrape_pdf(temp_path)
            all_items.extend(items)
        return JSONResponse({
            "team_id": team_id,
            "items": all_items
        })
    finally:
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                os.remove(temp_path)

@app.post("/scrape-blog")
async def scrape_blog(url: str = Form(...), team_id: str = Form("aline123")):
    scraper = ContentScraper()
    items = scraper.scrape_generic_blog(url)
    return JSONResponse({
        "team_id": team_id,
        "items": items
    })

@app.post("/scrape-multi-blog")
async def scrape_multi_blog(urls: str = Form(...), team_id: str = Form("aline123")):
    scraper = ContentScraper()
    all_items = []
    url_list = [u.strip() for u in urls.splitlines() if u.strip()]
    for url in url_list:
        items = scraper.scrape_generic_blog(url)
        all_items.extend(items)
    return JSONResponse({
        "team_id": team_id,
        "items": all_items
    })

@app.post("/scrape-all")
async def scrape_all(
    files: Optional[List[UploadFile]] = File(None),
    urls: Optional[str] = Form(None),
    max_pages: Optional[int] = Form(10),
    source_team_map: Optional[str] = Form(None)
):
    all_items = []
    scraper = ContentScraper()
    temp_paths = []
    try:
        # Process PDFs
        if files:
            for file in files:
                temp_path = f"temp_{file.filename}"
                with open(temp_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                temp_paths.append(temp_path)
                pdf_items = scraper.scrape_pdf(temp_path)
                for item in pdf_items:
                    all_items.append(ensure_item_format(item, content_type="book", source_url=""))
        # Process blog URLs
        if urls:
            url_list = [u.strip() for u in urls.splitlines() if u.strip()]
            for url in url_list:
                blog_items = scraper.scrape_generic_blog(url, max_pages=max_pages)
                for item in blog_items:
                    all_items.append(ensure_item_format(item, content_type="blog", source_url=item.get("source_url", url)))
        # Pick a random team_id (e.g., 1-10000 as string)
        team_id = str(random.randint(1, 10000))
        return JSONResponse({
            "team_id": team_id,
            "items": all_items
        })
    finally:
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                os.remove(temp_path) 