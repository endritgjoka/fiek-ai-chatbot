import os
import shutil
import time
from urllib.parse import urlparse, urljoin
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

import pytesseract
from pdf2image import convert_from_path
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document 

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_FALLBACK = True
except ImportError:
    HAS_FALLBACK = False
    print("⚠️  requests/BeautifulSoup not available. Install with: pip install requests beautifulsoup4")

# Cross-platform Tesseract OCR path detection
def find_tesseract():
    """Find Tesseract executable path across different platforms."""
    import platform
    import shutil
    
    # First check environment variable (user override)
    env_path = os.getenv("TESSERACT_CMD")
    if env_path and os.path.exists(env_path):
        return env_path
    
    # Check if tesseract is in PATH
    tesseract_path = shutil.which("tesseract")
    if tesseract_path:
        return tesseract_path
    
    # Platform-specific default paths
    system = platform.system()
    if system == "Windows":
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
        ]
    elif system == "Darwin":  # macOS
        possible_paths = [
            "/usr/local/bin/tesseract",
            "/opt/homebrew/bin/tesseract",
            "/usr/bin/tesseract",
        ]
    else:  # Linux and others
        possible_paths = [
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract",
        ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

# Set Tesseract path if found, otherwise OCR will be disabled
TESSERACT_PATH = find_tesseract()
if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    HAS_TESSERACT = True
else:
    HAS_TESSERACT = False
    print("⚠️  Tesseract OCR not found. OCR functionality will be disabled.")
    print("   To enable OCR, install Tesseract:")
    print("   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
    print("   - macOS: brew install tesseract")
    print("   - Linux: sudo apt-get install tesseract-ocr (Ubuntu/Debian) or sudo yum install tesseract (RHEL/CentOS)")
    print("   - Or set TESSERACT_CMD environment variable to the tesseract executable path")

os.environ["USER_AGENT"] = "FIEK_Student_Project/1.0"


if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found. Please check your .env file.")

FOLDER_PATH = "./fiek_documents/"

# URLs that contain staff listings with profile links
STAFF_PAGES = [
    "https://fiek.uni-pr.edu/page.aspx?id=1,12",  # Menaxhmenti
    "https://fiek.uni-pr.edu/page.aspx?id=1,14",  # Stafi Akademik
    "https://fiek.uni-pr.edu/page.aspx?id=1,15",  # Stafi Administrativ
]

URLS = [
    "https://fiek.uni-pr.edu/page.aspx?id=1,8",   # Te dhenat per FIEK
    "https://fiek.uni-pr.edu/page.aspx?id=1,9",   # Vizioni
    "https://fiek.uni-pr.edu/page.aspx?id=1,10",  # Misioni
    "https://fiek.uni-pr.edu/page.aspx?id=1,18",  # Objektivat
    "https://fiek.uni-pr.edu/page.aspx?id=1,66",  # Infrastruktura

    "https://fiek.uni-pr.edu/page.aspx?id=1,11",  # Dekanati
    "https://fiek.uni-pr.edu/page.aspx?id=1,12",  # Menaxhmenti
    "https://fiek.uni-pr.edu/page.aspx?id=1,14",  # Stafi Akademik
    "https://fiek.uni-pr.edu/page.aspx?id=1,15",  # Stafi Administrativ
    "https://fiek.uni-pr.edu/page.aspx?id=1,13",  # Sekretari

    "https://fiek.uni-pr.edu/page.aspx?id=1,37",  # Njoftime
    "https://fiek.uni-pr.edu/page.aspx?id=1,38",  # Bursa dhe Mobilitete

    "https://fiek.uni-pr.edu/page.aspx?id=1,64",  # Projekte (Main Page)
    "https://fiek.uni-pr.edu/page.aspx?id=1,80",  # Bashkëpunime me Industrinë
    "https://fiek.uni-pr.edu/page.aspx?id=1,81",  # Bashkëpunime me Universitete
    "https://fiek.uni-pr.edu/page.aspx?id=1,82",  # Bashkëpunime me Institucione Publike
]

def extract_staff_profile_links(html_content, base_url):
    """
    Extract staff profile links from staff listing pages.
    Handles multiple URL formats:
    - Absolute: https://staff.uni-pr.edu/profile/username
    - Relative: staff.aspx?id=1,12,6 (Management)
    - Relative: staff.aspx?id=1,15,15 (Administrative Staff)
    Handles multiple HTML structures: col-xl-6 cards and border media cards.
    """
    profile_links = []
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract base domain from base_url
        from urllib.parse import urlparse, urljoin
        parsed_base = urlparse(base_url)
        base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
        
        # Method 1: Find all staff cards (divs with class containing col-xl-6)
        staff_cards_col = soup.find_all('div', class_=lambda x: x and 'col-xl-6' in str(x))
        
        # Method 2: Find all media cards (divs with class containing 'border media' or 'media-body')
        staff_cards_media = soup.find_all('div', class_=lambda x: x and ('border media' in str(x) or 'media-body' in str(x)))
        
        # Combine both methods
        all_cards = staff_cards_col + staff_cards_media
        
        print(f"    🔍 Found {len(staff_cards_col)} col-xl-6 cards and {len(staff_cards_media)} media cards")
        
        for card in all_cards:
            # Find all links in the card
            links = card.find_all('a', href=True)
            for link in links:
                href = link.get('href', '').strip()
                if not href:
                    continue
                
                # Check for different profile link patterns
                is_profile_link = False
                full_url = None
                
                # Pattern 1: Absolute URL to staff.uni-pr.edu
                if 'staff.uni-pr.edu/profile' in href:
                    is_profile_link = True
                    if href.startswith('http'):
                        full_url = href
                    elif href.startswith('/'):
                        full_url = f"https://staff.uni-pr.edu{href}"
                    else:
                        full_url = f"https://staff.uni-pr.edu/{href}"
                
                # Pattern 2: Relative URL staff.aspx?id=... (Management, Administrative Staff)
                elif 'staff.aspx?id=' in href:
                    is_profile_link = True
                    # Convert relative URL to absolute
                    if href.startswith('/'):
                        full_url = urljoin(base_domain, href)
                    else:
                        # Relative path like "staff.aspx?id=1,12,6"
                        full_url = urljoin(base_url, href)
                
                if is_profile_link and full_url:
                    if full_url not in profile_links:
                        profile_links.append(full_url)
                        # Print the URL as requested
                        print(f"      📌 Found profile: {full_url}")
        
        # Method 3: Also try finding links directly (fallback)
        if len(profile_links) == 0:
            print(f"    🔍 Trying direct link search...")
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '').strip()
                if not href:
                    continue
                
                is_profile_link = False
                full_url = None
                
                if 'staff.uni-pr.edu/profile' in href:
                    is_profile_link = True
                    if href.startswith('http'):
                        full_url = href
                    elif href.startswith('/'):
                        full_url = f"https://staff.uni-pr.edu{href}"
                    else:
                        full_url = f"https://staff.uni-pr.edu/{href}"
                elif 'staff.aspx?id=' in href:
                    is_profile_link = True
                    if href.startswith('/'):
                        full_url = urljoin(base_domain, href)
                    else:
                        full_url = urljoin(base_url, href)
                
                if is_profile_link and full_url:
                    if full_url not in profile_links:
                        profile_links.append(full_url)
                        print(f"      📌 Found profile: {full_url}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in profile_links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        
        print(f"    ✅ Extracted {len(unique_links)} unique profile links")
        return unique_links
    except Exception as e:
        print(f"    ⚠️  Error extracting profile links: {e}")
        import traceback
        traceback.print_exc()
        return []

def extract_text_from_scanned_pdf(pdf_path):
    """
    Converts PDF pages to images, then runs OCR to get text.
    Requires Tesseract OCR to be installed.
    """
    if not HAS_TESSERACT:
        print(f"⚠️  OCR not available for {pdf_path}. Tesseract not installed.")
        return ""
    
    print(f"🔍 Running OCR on scanned doc: {pdf_path}...")
    try:
        images = convert_from_path(pdf_path)
        text = ""
        for i, image in enumerate(images):
            # Extract text from image
            # Try English and Albanian languages
            try:
                page_text = pytesseract.image_to_string(image, lang='eng+sqi')
            except Exception:
                # Fallback to English only if Albanian language pack not available
                try:
                    page_text = pytesseract.image_to_string(image, lang='eng')
                except Exception:
                    page_text = pytesseract.image_to_string(image)
            text += f"\n[Page {i+1}]\n{page_text}"
        return text
    except Exception as e:
        print(f"OCR Failed for {pdf_path}: {e}")
        return ""

def load_documents():
    all_docs = []

    # Load PDFs and text files if folder exists
    if os.path.exists(FOLDER_PATH):
        for filename in os.listdir(FOLDER_PATH):
            file_path = os.path.join(FOLDER_PATH, filename)
            
            # Handle PDF files
            if filename.endswith(".pdf"):
                try:
                    loader = PyPDFLoader(file_path)
                    pages = loader.load()
                    
                    if len(pages) > 0 and len(pages[0].page_content.strip()) < 10:
                        raise ValueError("Empty text - likely scanned")
                    
                    print(f"📄 Loaded Digital PDF: {filename}")
                    all_docs.extend(pages)
                    
                except Exception:
                    print(f"⚠️ Digital read failed for {filename}. Switching to OCR...")
                    raw_text = extract_text_from_scanned_pdf(file_path)
                    if raw_text:
                        doc = Document(page_content=raw_text, metadata={"source": filename, "type": "scanned_pdf"})
                        all_docs.append(doc)
            
            # Handle text files
            elif filename.endswith((".txt", ".text")):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if len(content) > 10:
                        doc = Document(
                            page_content=content,
                            metadata={
                                "source": filename,
                                "type": "text_file"
                            }
                        )
                        all_docs.append(doc)
                        print(f"📝 Loaded Text File: {filename} ({len(content)} chars)")
                    else:
                        print(f"⚠️ Text file {filename} is too short or empty, skipping")
                except Exception as e:
                    print(f"⚠️ Failed to load text file {filename}: {e}")
    else:
        print(f"⚠️ Folder '{FOLDER_PATH}' does not exist. Skipping file loading. Creating folder for future use...")
        os.makedirs(FOLDER_PATH, exist_ok=True)

    print("🌐 Scraping URLs...")
    print("   Note: Website is protected by Cloudflare (bot protection).")
    
    # Try to import browser-based scraping
    HAS_BROWSER_SCRAPING = False
    try:
        from .scrape_with_browser import scrape_with_browser
        HAS_BROWSER_SCRAPING = True
    except ImportError:
        try:
            from scrape_with_browser import scrape_with_browser
            HAS_BROWSER_SCRAPING = True
        except ImportError:
            HAS_BROWSER_SCRAPING = False
    
    # Check if Playwright is actually available (not just the module)
    PLAYWRIGHT_AVAILABLE = False
    if HAS_BROWSER_SCRAPING:
        try:
            from playwright.sync_api import sync_playwright
            # Try to actually use it to see if browser is installed
            with sync_playwright() as p:
                PLAYWRIGHT_AVAILABLE = True
        except Exception:
            PLAYWRIGHT_AVAILABLE = False
    
    if PLAYWRIGHT_AVAILABLE:
        print("   ✅ Playwright detected - will use browser automation to bypass Cloudflare")
    else:
        print("   ⚠️  WARNING: Playwright not installed or Chromium not downloaded!")
        print("   📌 Most URLs will FAIL due to Cloudflare protection")
        print("")
        print("   🔧 To fix, run these commands:")
        print("      1. pip install playwright")
        print("      2. playwright install chromium")
        print("")
        print("   📖 See backend/INSTALL_PLAYWRIGHT.md for detailed instructions")
        print("")
    
    web_docs_count = 0
    
    def scrape_with_fallback(url, extract_profile_links=False):
        """
        Try browser-based scraping first (for Cloudflare), then WebBaseLoader.
        If extract_profile_links=True, also extracts and scrapes staff profile links.
        """
        # Check if we got Cloudflare challenge page
        is_cloudflare_challenge = False
        html_content_for_links = None
        
        # Try browser-based scraping first (if available) - handles Cloudflare
        if HAS_BROWSER_SCRAPING:
            try:
                print(f"    🌐 Trying browser-based scraping (Playwright/Selenium)...")
                browser_result = scrape_with_browser(url, return_html=extract_profile_links)
                if browser_result:
                    # Handle both single Document and tuple (Document, html_content)
                    if isinstance(browser_result, tuple):
                        browser_doc, browser_html = browser_result
                    else:
                        browser_doc = browser_result
                        browser_html = None
                    
                    # Check if we got real content (not Cloudflare challenge)
                    if browser_doc and len(browser_doc.page_content.strip()) > 200:
                        content_len = len(browser_doc.page_content.strip())
                        print(f"    ✅ Browser scraping succeeded! ({content_len} chars)")
                    else:
                        if browser_doc:
                            content_preview = browser_doc.page_content[:100] if browser_doc.page_content else ""
                            print(f"    ⚠️  Browser scraping returned short content ({len(browser_doc.page_content) if browser_doc.page_content else 0} chars)")
                            if "Just a moment" in content_preview:
                                print(f"    ⚠️  Still hitting Cloudflare challenge page")
                        browser_doc = None
                        browser_html = None
                    
                    # If we need to extract profile links and got HTML, extract and scrape them now
                    if extract_profile_links and browser_html:
                        html_content_for_links = browser_html
                        # Extract and scrape profile links using browser HTML
                        docs = [browser_doc]
                        profile_links = extract_staff_profile_links(html_content_for_links, url)
                        if profile_links:
                            print(f"    📋 Scraping {len(profile_links)} staff profile links (no limit)...")
                            scraped_count = 0
                            failed_count = 0
                            for i, profile_url in enumerate(profile_links, 1):
                                try:
                                    print(f"      [{i}/{len(profile_links)}] Scraping: {profile_url}")
                                    profile_docs = scrape_with_fallback(profile_url, extract_profile_links=False)
                                    if profile_docs and len(profile_docs) > 0:
                                        for pdoc in profile_docs:
                                            pdoc.metadata["type"] = "staff_profile"
                                            pdoc.metadata["parent_page"] = url
                                        docs.extend(profile_docs)
                                        scraped_count += len(profile_docs)
                                        print(f"        ✅ Successfully scraped profile")
                                        time.sleep(0.3)
                                    else:
                                        print(f"        ⚠️  Failed to scrape profile (no content)")
                                        failed_count += 1
                                except Exception as e:
                                    print(f"        ❌ Error scraping profile: {str(e)[:100]}")
                                    failed_count += 1
                                    continue
                            
                            print(f"    📊 Profile scraping summary:")
                            print(f"       ✅ Successfully scraped: {scraped_count} profiles")
                            if failed_count > 0:
                                print(f"       ❌ Failed: {failed_count} profiles")
                        return docs
                    elif extract_profile_links:
                        # No HTML available from browser, need to fall back to requests
                        print(f"    ℹ️  Browser scraping succeeded but HTML not available, trying requests for link extraction...")
                        html_content_for_links = None  # Will try requests method
                    else:
                        # No need for HTML, just return the document
                        return [browser_doc]
            except Exception as e:
                print(f"    ⚠️  Browser scraping failed: {e}")
                browser_doc = None
                browser_html = None
                html_content_for_links = None
        
        # Fallback to WebBaseLoader
        web_docs_from_loader = None
        try:
            web_loader = WebBaseLoader(
                web_paths=[url],
                header_template={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            )
            web_docs_from_loader = web_loader.load()
            if web_docs_from_loader and len(web_docs_from_loader) > 0:
                content = web_docs_from_loader[0].page_content.strip()
                
                # Check if it's Cloudflare challenge page
                if "Just a moment" in content or "Enable JavaScript" in content:
                    is_cloudflare_challenge = True
                    print(f"    ⚠️  Cloudflare challenge page detected!")
                    print(f"    💡 Install Playwright for better scraping: pip install playwright && playwright install chromium")
                
                # Clean up WebBaseLoader content
                lines = [line.strip() for line in content.split('\n') if line.strip() and len(line.strip()) > 3]
                cleaned_content = '\n'.join(lines)
                
                if len(cleaned_content) > 200 and not is_cloudflare_challenge:
                    # Update the document with cleaned content
                    web_docs_from_loader[0].page_content = cleaned_content
                    return web_docs_from_loader
                else:
                    if is_cloudflare_challenge:
                        print(f"    ❌ Cannot scrape: Cloudflare protection blocks automated access")
                        return None
                    else:
                        print(f"    ⚠️  WebBaseLoader got short content ({len(cleaned_content)} chars)")
                        web_docs_from_loader[0].page_content = cleaned_content
        except Exception as e:
            print(f"    ⚠️  WebBaseLoader failed: {e}")
        
        # Try requests with session to handle cookies/redirects (might help with 403)
        if HAS_FALLBACK:
            try:
                session = requests.Session()
                # First visit main page to get cookies
                session.get("https://fiek.uni-pr.edu/", timeout=10)
                
                # More complete headers to avoid 403
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9,sq;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "same-origin",
                    "Sec-Fetch-User": "?1",
                    "Cache-Control": "max-age=0",
                    "Referer": "https://fiek.uni-pr.edu/",
                }
                response = session.get(url, headers=headers, timeout=15, allow_redirects=True)
                response.raise_for_status()
                
                # Handle encoding properly
                if not response.encoding or response.encoding == 'ISO-8859-1':
                    response.encoding = response.apparent_encoding or 'utf-8'
                
                html_content_for_links = response.text  # Save for profile link extraction
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(["script", "style", "nav", "footer", "header", "iframe", "noscript"]):
                    element.decompose()
                
                # Try to find main content area (common patterns)
                main_content = None
                content_selectors = [
                    soup.find('main'),
                    soup.find('article'),
                    soup.find(id='content'),
                    soup.find(class_='content'),
                    soup.find(id='main-content'),
                    soup.find(class_='main-content'),
                    soup.find('div', {'id': 'ctl00_ContentPlaceHolder1'}),  # ASP.NET pattern
                ]
                
                for selector in content_selectors:
                    if selector:
                        main_content = selector
                        break
                
                # Extract text from main content or whole page
                if main_content:
                    text = main_content.get_text(separator='\n', strip=True)
                else:
                    text = soup.get_text(separator='\n', strip=True)
                
                # Clean up text - remove excessive whitespace
                lines = [line.strip() for line in text.split('\n') if line.strip() and len(line.strip()) > 3]
                cleaned_text = '\n'.join(lines)
                
                # Get title
                title = "No title"
                if soup.title:
                    title = soup.title.string.strip() if soup.title.string else "No title"
                elif main_content:
                    h1 = main_content.find('h1')
                    if h1:
                        title = h1.get_text(strip=True)
                
                if len(cleaned_text.strip()) > 200:  # Require at least 200 chars
                    docs = [Document(
                        page_content=cleaned_text,
                        metadata={
                            "source": url,
                            "type": "website",
                            "url": url,
                            "title": title
                        }
                    )]
                    
                    # If this is a staff page, extract and scrape profile links
                    if extract_profile_links and html_content_for_links:
                        profile_links = extract_staff_profile_links(html_content_for_links, url)
                        if profile_links:
                            print(f"    📋 Scraping {len(profile_links)} staff profile links (no limit)...")
                            scraped_count = 0
                            failed_count = 0
                            for i, profile_url in enumerate(profile_links, 1):  # No limit - scrape all profiles
                                try:
                                    print(f"      [{i}/{len(profile_links)}] Scraping: {profile_url}")
                                    # Recursively scrape the profile page (but don't extract more links)
                                    profile_docs = scrape_with_fallback(profile_url, extract_profile_links=False)
                                    if profile_docs and len(profile_docs) > 0:
                                        # Update metadata to indicate it's a profile
                                        for pdoc in profile_docs:
                                            pdoc.metadata["type"] = "staff_profile"
                                            pdoc.metadata["parent_page"] = url
                                        docs.extend(profile_docs)
                                        scraped_count += len(profile_docs)
                                        print(f"        ✅ Successfully scraped profile")
                                        time.sleep(0.3)  # Be polite
                                    else:
                                        print(f"        ⚠️  Failed to scrape profile (no content)")
                                        failed_count += 1
                                except Exception as e:
                                    print(f"        ❌ Error scraping profile: {str(e)[:100]}")
                                    failed_count += 1
                                    continue
                            
                            print(f"    📊 Profile scraping summary:")
                            print(f"       ✅ Successfully scraped: {scraped_count} profiles")
                            if failed_count > 0:
                                print(f"       ❌ Failed: {failed_count} profiles")
                    
                    return docs
                else:
                    print(f"    ⚠️  Requests content too short ({len(cleaned_text)} chars)")
            except Exception as e:
                print(f"    ⚠️  Requests method failed: {e}")
        
        # If we got something from WebBaseLoader (even if short), use it
        if web_docs_from_loader:
            print(f"    ℹ️  Using WebBaseLoader result (may be limited)")
            return web_docs_from_loader
        
        return None
    
    # Track statistics for better reporting
    successful_urls = 0
    failed_urls = 0
    failed_url_list = []
    
    for url in URLS:
        try:
            print(f"\n  📡 Loading: {url}")
            # Check if this is a staff page that needs profile link extraction
            is_staff_page = url in STAFF_PAGES
            if is_staff_page:
                print(f"    ℹ️  Staff page detected - will extract and scrape profile links")
            
            # Retry logic for failed scrapes (more robust)
            max_retries = 2
            web_docs = None
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        print(f"    🔄 Retry attempt {attempt + 1}/{max_retries}...")
                        time.sleep(2)  # Wait longer before retry
                    
                    web_docs = scrape_with_fallback(url, extract_profile_links=is_staff_page)
                    
                    if web_docs and len(web_docs) > 0:
                        break  # Success, exit retry loop
                    else:
                        last_error = "No content extracted"
                        
                except Exception as e:
                    last_error = str(e)
                    if attempt < max_retries - 1:
                        print(f"    ⚠️  Attempt {attempt + 1} failed: {last_error[:100]}")
                        continue
                    else:
                        # On final attempt, don't suppress the error
                        raise
            
            if web_docs and len(web_docs) > 0:
                for doc in web_docs:
                    # Ensure metadata is properly set for website documents
                    # Create new metadata dict to ensure all fields are set
                    doc.metadata = doc.metadata.copy() if doc.metadata else {}
                    doc.metadata["source"] = url
                    # Don't override type if it's already set (e.g., staff_profile, text_file)
                    if doc.metadata.get("type") not in ["staff_profile", "scanned_pdf", "text_file"]:
                        doc.metadata["type"] = "website"
                    doc.metadata["url"] = url
                    # Add title if available
                    if "title" not in doc.metadata or doc.metadata.get("title") == "No title":
                        # Try to extract title from content if not set
                        title = doc.metadata.get("title", "No title")
                        doc.metadata["title"] = title
                    
                    # Ensure source URL is in content for better context (but don't duplicate)
                    if not doc.page_content.startswith(f"[Source: {url}]"):
                        doc.page_content = f"[Source: {url}]\n\n{doc.page_content}"
                
                all_docs.extend(web_docs)
                web_docs_count += len(web_docs)
                total_chars = sum(len(d.page_content) for d in web_docs)
                successful_urls += 1
                print(f"  ✅ Successfully loaded {len(web_docs)} document(s) from {url} (content length: {total_chars} chars)")
                
                # Warn if content is suspiciously short
                if total_chars < 200:
                    print(f"    ⚠️  Warning: Content seems short. Preview: {web_docs[0].page_content[:150]}...")
            else:
                failed_urls += 1
                failed_url_list.append(url)
                error_msg = last_error if last_error else "No content extracted"
                print(f"  ❌ Failed to load {url}: {error_msg}")
            
            time.sleep(0.5)  # Be polite between requests
            
        except Exception as e:
            failed_urls += 1
            failed_url_list.append(url)
            error_msg = str(e)[:200]  # Limit error message length
            print(f"  ❌ Failed to load {url}: {error_msg}")
            # Only print full traceback for debugging if it's an unexpected error
            if "Cloudflare" not in error_msg and "403" not in error_msg:
                import traceback
                print(f"    Traceback: {traceback.format_exc()[:500]}")
            continue
    
    # Print summary statistics
    print(f"\n📊 URL Scraping Summary:")
    print(f"   ✅ Successful: {successful_urls}/{len(URLS)} URLs")
    print(f"   ❌ Failed: {failed_urls}/{len(URLS)} URLs")
    if failed_url_list:
        print(f"   Failed URLs:")
        for failed_url in failed_url_list:
            print(f"      - {failed_url}")
        print(f"\n   💡 Tips for failed URLs:")
        print(f"      - Install Playwright: pip install playwright && playwright install chromium")
        print(f"      - Check internet connection")
        print(f"      - Some URLs may require authentication or have changed")
    
    print(f"🌐 Total web documents loaded: {web_docs_count}")
    return all_docs

def main():
    raw_docs = load_documents()
    
    if not raw_docs:
        print("❌ No documents loaded. Check if 'fiek_documents' folder is empty or URLs are correct.")
        return

    print(f"✅ Total raw documents loaded: {len(raw_docs)}")
    
    # Count by type
    pdf_count = sum(1 for doc in raw_docs if doc.metadata.get("type") in ["scanned_pdf", "pdf"])
    text_count = sum(1 for doc in raw_docs if doc.metadata.get("type") == "text_file")
    web_count = sum(1 for doc in raw_docs if doc.metadata.get("type") == "website")
    staff_profile_count = sum(1 for doc in raw_docs if doc.metadata.get("type") == "staff_profile")
    other_count = len(raw_docs) - pdf_count - text_count - web_count - staff_profile_count
    
    print(f"   📄 PDF documents: {pdf_count}")
    print(f"   📝 Text files: {text_count}")
    print(f"   🌐 Web documents: {web_count}")
    if staff_profile_count > 0:
        print(f"   👤 Staff profiles: {staff_profile_count}")
    if other_count > 0:
        print(f"   📋 Other documents: {other_count}")

    print("\n✂️  Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    splits = text_splitter.split_documents(raw_docs)
    
    # Ensure metadata is preserved after splitting (especially for website chunks)
    for split in splits:
        if not split.metadata.get("type"):
            # If type is missing, infer from source
            source = split.metadata.get("source", "")
            if source.startswith("http"):
                split.metadata["type"] = "website"
                split.metadata["url"] = source
            else:
                split.metadata["type"] = "pdf"
    print(f"✂️  Split into {len(splits)} chunks.")
    
    web_chunks = sum(1 for split in splits if split.metadata.get("type") == "website")
    staff_profile_chunks = sum(1 for split in splits if split.metadata.get("type") == "staff_profile")
    pdf_chunks = sum(1 for split in splits if split.metadata.get("type") in ["scanned_pdf", "pdf"])
    text_chunks = sum(1 for split in splits if split.metadata.get("type") == "text_file")
    other_chunks = len(splits) - web_chunks - staff_profile_chunks - pdf_chunks - text_chunks
    
    print(f"   📄 PDF chunks: {pdf_chunks}")
    print(f"   📝 Text file chunks: {text_chunks}")
    print(f"   🌐 Web chunks: {web_chunks}")
    if staff_profile_chunks > 0:
        print(f"   👤 Staff profile chunks: {staff_profile_chunks}")
    if other_chunks > 0:
        print(f"   📋 Other chunks: {other_chunks}")

    print("\n💾 Saving to Vector Database (ChromaDB)...")
    embedding = OpenAIEmbeddings(model="text-embedding-3-small")
    
    if os.path.exists("./fiek_db"):
        print("  🗑️  Clearing existing database...")
        shutil.rmtree("./fiek_db")
    
    vectorstore = Chroma.from_documents(
        documents=splits, 
        embedding=embedding, 
        persist_directory="./fiek_db"
    )
    
    # Verify what was actually stored
    print("\n🔍 Verifying database contents...")
    
    # Test with multiple queries that should match website content
    test_queries = ["FIEK", "vizioni", "dekan", "programet akademike"]
    all_website_results = []
    all_pdf_results = []
    
    for query in test_queries:
        test_results = vectorstore.similarity_search(query, k=min(10, len(splits)))
        website_results = [r for r in test_results if r.metadata.get("type") == "website"]
        pdf_results = [r for r in test_results if r.metadata.get("type") != "website"]
        all_website_results.extend(website_results)
        all_pdf_results.extend(pdf_results)
    
    # Remove duplicates
    seen_sources = set()
    unique_website_results = []
    for r in all_website_results:
        source = r.metadata.get("source", "")
        if source not in seen_sources:
            seen_sources.add(source)
            unique_website_results.append(r)
    
    print(f"   Sample retrieval test (multiple queries):")
    print(f"   - Total unique website chunks retrieved: {len(unique_website_results)}")
    print(f"   - PDF chunks retrieved: {len(set(r.metadata.get('source') for r in all_pdf_results))}")
    
    if unique_website_results:
        print(f"\n   ✅ Website data IS retrievable from database!")
        print(f"   Sample website sources found:")
        for i, result in enumerate(unique_website_results[:3], 1):
            source = result.metadata.get('source', 'Unknown')
            content_preview = result.page_content[:150].replace('\n', ' ')
            print(f"   {i}. {source}")
            print(f"      Content: {content_preview}...")
    else:
        print(f"\n   ⚠️  Warning: No website chunks found in retrieval!")
        print(f"   Checking what's actually in the database...")
        
        # Try to get all documents and check metadata
        try:
            # Get a larger sample
            all_results = vectorstore.similarity_search("FIEK", k=min(50, len(splits)))
            website_in_db = [r for r in all_results if r.metadata.get("type") == "website"]
            print(f"   Found {len(website_in_db)} website chunks in larger sample of {len(all_results)}")
            
            if website_in_db:
                print(f"   ✅ Website chunks ARE in database, but not ranking high in similarity search")
                print(f"   This might be due to short content or embedding quality")
                print(f"   Sample: {website_in_db[0].metadata.get('source')} ({len(website_in_db[0].page_content)} chars)")
            else:
                print(f"   ❌ No website chunks found even in larger sample")
                print(f"   This suggests website data may not have been stored correctly")
        except Exception as e:
            print(f"   Error checking database: {e}")
    
    print("\n🚀 Success! Database built at ./fiek_db")

if __name__ == "__main__":
    main()