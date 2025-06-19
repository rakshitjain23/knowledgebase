# Knowledgebase Import Tool

A modern tool to import technical knowledge from PDFs and blogs into a clean, Markdown-ready knowledgebase format. Supports multiple sources at once, auto-assigns team IDs, and provides a user-friendly web interface.

## Folder Structure

```
save align assignment/
  backend/    # FastAPI backend for scraping and processing
    app/
      api.py
      content_scraper.py
    requirements.txt
  frontend/   # Next.js frontend web app
    app/
      favicon.ico
      globals.css
      layout.tsx
      page.module.css
      page.tsx
    public/
      ... (SVGs, icons)
    package.json
    ... (other config files)
  README.md
  knowledgebase_output.json (It's the output of https://medium.com/@nurobyte and https://medium.com/@pranavpurohit73)
```

## Features
- Import from multiple PDFs and blog URLs at once
- Auto-assigns team IDs for each source
- Clean Markdown output, ready for knowledgebase ingestion
- Download results as JSON or Markdown
- Modern, responsive web UI

## Getting Started

### 1. Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
```

- The backend will run at `http://localhost:8000`

### 2. Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

- The frontend will run at `http://localhost:3000`
- Make sure the backend is running for full functionality

## Usage
1. Open the frontend in your browser (`http://localhost:3000`)
2. Upload one or more PDF files (optional)
3. Enter one or more blog URLs (one per line)
4. Set the max pages to crawl per blog (optional)
5. Click **Import**
6. Download the results as JSON or Markdown

## Notes
- Team IDs are assigned automatically (e.g., `team_1`, `team_2`, ...)
- The backend handles all scraping and conversion
- The frontend is fully responsive and easy to use

---

Built with Next.js & FastAPI. 