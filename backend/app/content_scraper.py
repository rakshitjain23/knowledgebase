import requests
import json
import re
from typing import List, Dict, Optional, Union
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import feedparser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from markdownify import markdownify as md
import PyPDF2
import io
from tqdm import tqdm
import time
import os
from readability import Document
import fitz  # PyMuPDF


class ContentScraper:
    """
    A scalable content scraper that can handle various content sources
    and output content in the required knowledgebase format.
    """
    
    def __init__(self, headless: bool = True):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.headless = headless
        self.driver = None
        
    def _get_driver(self):
        """Initialize Selenium WebDriver for JavaScript-heavy sites."""
        if self.driver is None:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        return self.driver
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove special characters that might break markdown
        text = re.sub(r'[^\w\s\-.,!?;:()[\]{}"\']', '', text)
        return text
    
    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract title from various sources."""
        # Try different title selectors
        title_selectors = [
            'h1',
            'title',
            '[class*="title"]',
            '[class*="heading"]',
            'h2',
            'h3'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.get_text().strip():
                return self._clean_text(title_elem.get_text())
        
        # Fallback to URL-based title
        parsed_url = urlparse(url)
        return parsed_url.path.split('/')[-1].replace('-', ' ').title()
    
    def _extract_content(self, html: str) -> str:
        """Extract main content from HTML using readability-lxml."""
        try:
            doc = Document(html)
            content_html = doc.summary()
            markdown_content = md(content_html, heading_style="ATX")
            return markdown_content.strip()
        except Exception:
            return ""
    
    def scrape_blog_url(self, url: str) -> dict:
        """Scrape a single blog post URL (generalized for any blog)."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            title = self._extract_title(soup, url)
            content = self._extract_content(html)
            if not content:
                # Try with Selenium for JS-heavy sites
                driver = self._get_driver()
                driver.get(url)
                time.sleep(3)
                page_source = driver.page_source
                content = self._extract_content(page_source)
            return {
                "title": title,
                "content": content,
                "content_type": "blog",
                "source_url": url,
                "author": "",
                "user_id": ""
            }
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None
    
    def scrape_blog_feed(self, feed_url: str) -> List[Dict]:
        """Scrape all posts from a blog RSS feed."""
        try:
            feed = feedparser.parse(feed_url)
            items = []
            
            for entry in tqdm(feed.entries, desc="Scraping blog posts"):
                if hasattr(entry, 'link'):
                    item = self.scrape_blog_url(entry.link)
                    if item:
                        items.append(item)
                time.sleep(1)  # Be respectful to servers
            
            return items
            
        except Exception as e:
            print(f"Error scraping feed {feed_url}: {str(e)}")
            return []
    
    def scrape_blog_sitemap(self, sitemap_url: str) -> List[Dict]:
        """Scrape all posts from a blog sitemap."""
        try:
            response = self.session.get(sitemap_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            urls = []
            
            # Extract URLs from sitemap
            for loc in soup.find_all('loc'):
                url = loc.get_text()
                if '/blog/' in url or '/post/' in url or '/article/' in url:
                    urls.append(url)
            
            items = []
            for url in tqdm(urls, desc="Scraping blog posts"):
                item = self.scrape_blog_url(url)
                if item:
                    items.append(item)
                time.sleep(1)
            
            return items
            
        except Exception as e:
            print(f"Error scraping sitemap {sitemap_url}: {str(e)}")
            return []
    
    def scrape_blog_pages(self, base_url: str, max_pages: int = 10) -> List[Dict]:
        """Scrape blog posts by crawling pages. Uses Selenium if no links found with requests."""
        items = []
        page = 1
        while page <= max_pages:
            try:
                # Try different pagination patterns
                page_urls = [
                    f"{base_url}?page={page}",
                    f"{base_url}/page/{page}",
                    f"{base_url}/p/{page}",
                    f"{base_url}?paged={page}"
                ]
                page_scraped = False
                for page_url in page_urls:
                    try:
                        response = self.session.get(page_url, timeout=10)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            all_links = [link['href'] for link in soup.find_all('a', href=True)]
                            post_links = []
                            for href in all_links:
                                # Only keep likely blog post links
                                if href.startswith('/blog/') and len(href) > len('/blog/'):
                                    full_url = urljoin(base_url, href)
                                    post_links.append(full_url)
                            post_links = list(set(post_links))
                            if not post_links:
                                try:
                                    driver = self._get_driver()
                                    driver.get(page_url)
                                    time.sleep(3)
                                    page_source = driver.page_source
                                    soup = BeautifulSoup(page_source, 'html.parser')
                                    selenium_links = [link['href'] for link in soup.find_all('a', href=True)]
                                    for href in selenium_links:
                                        if href.startswith('/blog/') and len(href) > len('/blog/'):
                                            full_url = urljoin(base_url, href)
                                            post_links.append(full_url)
                                    post_links = list(set(post_links))
                                except Exception as e:
                                    pass
                            if not post_links:
                                break
                            for link in tqdm(post_links, desc=f"Scraping page {page}"):
                                item = self.scrape_blog_url(link)
                                if item:
                                    items.append(item)
                                time.sleep(1)
                            page_scraped = True
                            break
                    except Exception as e:
                        continue
                if not page_scraped:
                    break
                page += 1
            except Exception as e:
                break
        return items
    
    def scrape_pdf(self, pdf_path: str, chunk_size: int = 2000) -> list:
        """Extract content from PDF and chunk it using PyMuPDF."""
        items = []
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            # Split into chunks
            chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
            for i, chunk in enumerate(chunks[:8]):  # Only first 8 chapters/chunks
                items.append({
                    "title": f"Book Chapter {i+1}",
                    "content": chunk.strip(),
                    "content_type": "book",
                    "source_url": "",
                    "author": "",
                    "user_id": ""
                })
        except Exception as e:
            print(f"PDF error: {e}")
        return items
    
    def scrape_generic_blog(self, blog_url: str, max_pages: int = 10) -> List[Dict]:
        """Generic blog scraper that tries multiple approaches."""
        print(f"Scraping blog: {blog_url}")
        # Try RSS feed first
        feed_urls = [
            f"{blog_url}/feed",
            f"{blog_url}/rss",
            f"{blog_url}/feed.xml",
            f"{blog_url}/rss.xml"
        ]
        for feed_url in feed_urls:
            try:
                response = self.session.get(feed_url, timeout=5)
                if response.status_code == 200:
                    print(f"Found RSS feed: {feed_url}")
                    items = self.scrape_blog_feed(feed_url)
                    if items:
                        return items
                    # If feed is empty, continue to next method
            except:
                continue
        # Try sitemap
        sitemap_urls = [
            f"{blog_url}/sitemap.xml",
            f"{blog_url}/sitemap_index.xml"
        ]
        for sitemap_url in sitemap_urls:
            try:
                response = self.session.get(sitemap_url, timeout=5)
                if response.status_code == 200:
                    print(f"Found sitemap: {sitemap_url}")
                    items = self.scrape_blog_sitemap(sitemap_url)
                    if items:
                        return items
            except:
                continue
        # Fallback to page crawling
        print("Using page crawling approach")
        return self.scrape_blog_pages(blog_url, max_pages=max_pages)
    
    def close(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
        self.session.close() 