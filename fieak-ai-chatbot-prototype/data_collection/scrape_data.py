"""
Data collection script for FIEK chatbot.
Scrapes web pages and extracts content from PDFs.
"""

import requests
from bs4 import BeautifulSoup
import pdfplumber
import json
import os
from pathlib import Path
import time

BASE_URL = "https://fiek.uni-pr.edu"
DATA_DIR = Path(__file__).parent.parent / "knowledge_base" / "raw_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Headers to mimic a real browser and avoid 403 errors
# Note: Using only gzip, deflate (not br/Brotli) as requests handles these automatically
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,sq;q=0.8',
    'Accept-Encoding': 'gzip, deflate',  # Removed 'br' (Brotli) as requests may not handle it properly
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0',
}

def scrape_web_page(url, title):
    """Scrape content from a web page."""
    try:
        print(f"Scraping: {title}")
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        # Ensure proper encoding - requests handles decompression automatically
        if not response.encoding or response.encoding == 'ISO-8859-1':
            response.encoding = response.apparent_encoding or 'utf-8'
        
        # Use response.text which handles decompression and encoding automatically
        html_content = response.text
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned_text = '\n'.join(lines)
        
        return {
            "title": title,
            "url": url,
            "content": cleaned_text,
            "type": "web_page"
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def extract_pdf_content(pdf_url, title):
    """Extract text content from a PDF."""
    try:
        print(f"Extracting PDF: {title}")
        # Use simpler headers for PDFs
        pdf_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,application/octet-stream,*/*',
        }
        response = requests.get(pdf_url, headers=pdf_headers, timeout=60)
        response.raise_for_status()
        
        # Save PDF temporarily
        pdf_path = DATA_DIR / f"{title.replace(' ', '_')}.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(response.content)
        
        # Extract text from PDF
        text_content = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
        
        # Clean up
        os.remove(pdf_path)
        
        return {
            "title": title,
            "url": pdf_url,
            "content": '\n'.join(text_content),
            "type": "pdf"
        }
    except Exception as e:
        print(f"Error extracting PDF {pdf_url}: {e}")
        return None

def collect_all_data():
    """Collect all data from provided sources."""
    data_sources = [
        # General FIEK information
        ("https://fiek.uni-pr.edu/page.aspx?id=1,8", "Te dhenat per FIEK", "web"),
        ("https://fiek.uni-pr.edu/page.aspx?id=1,9", "Vizioni", "web"),
        ("https://fiek.uni-pr.edu/page.aspx?id=1,10", "Misioni", "web"),
        ("https://fiek.uni-pr.edu/page.aspx?id=1,18", "Objektivat", "web"),
        
        # Management
        ("https://fiek.uni-pr.edu/page.aspx?id=1,11", "Dekanati dhe Menaxhmenti", "web"),
        ("https://fiek.uni-pr.edu/page.aspx?id=1,12", "Menaxhmenti", "web"),
        
        # Staff
        ("https://fiek.uni-pr.edu/page.aspx?id=1,14", "Stafi Akademik", "web"),
        ("https://fiek.uni-pr.edu/page.aspx?id=1,15", "Stafi Administrativ", "web"),
        
        # Programs
        ("https://fiek.uni-pr.edu/page.aspx?id=1,19", "Programet e akredituara", "web"),
        ("https://fiek.uni-pr.edu/page.aspx?id=1,20", "Programi MSc", "web"),
        ("https://fiek.uni-pr.edu/page.aspx?id=1,21", "Programi PhD", "web"),
        
        # PDFs
        ("https://fiek.uni-pr.edu/desk/inc/media/60A0DFF3-EEE8-4616-A971-BE28EE743F22.pdf", "Programi BSc", "pdf"),
        ("https://fiek.uni-pr.edu/desk/inc/media/A949D835-7CA6-41D9-9763-33557C44A376.pdf", "Orari BSc", "pdf"),
        ("https://fiek.uni-pr.edu/desk/inc/media/E9CF450C-0B40-4951-8B42-482BC0705AD6.pdf", "Orari MSc", "pdf"),
        ("https://fiek.uni-pr.edu/desk/inc/media/E946AEB9-8F4C-4FE5-ABFD-849CEC6038E5.pdf", "Rregullore mobilitet", "pdf"),
        ("https://fiek.uni-pr.edu/desk/inc/media/A3712F8A-CEF5-41A7-ABA3-7F97ED800363.pdf", "Rregullore Bachelor", "pdf"),
        ("https://fiek.uni-pr.edu/desk/inc/media/D2B5D07B-7AD9-4EEE-B1A8-8CE338EAE800.pdf", "Rregullore Master", "pdf"),
        ("https://fiek.uni-pr.edu/desk/inc/media/D82C85AD-D1FB-40D9-AE4C-FF5CD841BCA0.pdf", "Rregullore Doktorature", "pdf"),
        
        # Other pages
        ("https://fiek.uni-pr.edu/page.aspx?id=1,64", "Projekte te fakultetit", "web"),
        ("https://fiek.uni-pr.edu/page.aspx?id=1,80", "Bashkepunime me industrine", "web"),
        ("https://fiek.uni-pr.edu/page.aspx?id=1,81", "Bashkepunime me universitete", "web"),
        ("https://fiek.uni-pr.edu/page.aspx?id=1,82", "Bashkepunime me institucione publike", "web"),
        ("https://fiek.uni-pr.edu/page.aspx?id=1,90", "Trupa keshilldhenese", "web"),
        ("https://fiek.uni-pr.edu/page.aspx?id=1,66", "Infrastruktura", "web"),
        ("https://fiek.uni-pr.edu/page.aspx?id=1,37", "Njoftime", "web"),
        ("https://fiek.uni-pr.edu/page.aspx?id=1,38", "Bursa dhe mobilitete", "web"),
    ]
    
    all_data = []
    
    for url, title, source_type in data_sources:
        if source_type == "web":
            data = scrape_web_page(url, title)
        else:
            data = extract_pdf_content(url, title)
        
        if data:
            all_data.append(data)
        
        time.sleep(2)  # Be respectful with requests
    
    # Save collected data
    output_file = DATA_DIR.parent / "collected_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nCollected {len(all_data)} documents")
    print(f"Data saved to {output_file}")
    
    return all_data

if __name__ == "__main__":
    collect_all_data()

