import os
import shutil
import time
import pytesseract
from pdf2image import convert_from_path
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document 
from dotenv import load_dotenv

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_FALLBACK = True
except ImportError:
    HAS_FALLBACK = False
    print("⚠️  requests/BeautifulSoup not available. Install with: pip install requests beautifulsoup4")
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


load_dotenv()

os.environ["USER_AGENT"] = "FIEK_Student_Project/1.0"


if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found. Please check your .env file.")

FOLDER_PATH = "./fiek_documents/"
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
    "https://fiek.uni-pr.edu/page.aspx?id=1,90",  # Trupa Keshilldhenese

    "https://fiek.uni-pr.edu/page.aspx?id=1,37",  # Njoftime
    "https://fiek.uni-pr.edu/page.aspx?id=1,38",  # Bursa dhe Mobilitete

    "https://fiek.uni-pr.edu/page.aspx?id=1,64",  # Projekte (Main Page)
    "https://fiek.uni-pr.edu/page.aspx?id=1,80",  # Bashkëpunime me Industrinë
    "https://fiek.uni-pr.edu/page.aspx?id=1,81",  # Bashkëpunime me Universitete
    "https://fiek.uni-pr.edu/page.aspx?id=1,82",  # Bashkëpunime me Institucione Publike
]

def extract_text_from_scanned_pdf(pdf_path):
    """
    Converts PDF pages to images, then runs OCR to get text.
    """
    print(f"🔍 Running OCR on scanned doc: {pdf_path}...")
    try:
        images = convert_from_path(pdf_path)
        text = ""
        for i, image in enumerate(images):
            # Extract text from image
            page_text = pytesseract.image_to_string(image, lang='eng+sqi') # Tries English and Albanian
            text += f"\n[Page {i+1}]\n{page_text}"
        return text
    except Exception as e:
        print(f"OCR Failed for {pdf_path}: {e}")
        return ""

def load_documents():
    all_docs = []

    if not os.path.exists(FOLDER_PATH):
        os.makedirs(FOLDER_PATH)
        print(f"⚠️ Created folder '{FOLDER_PATH}'. Please put your PDFs inside it!")
        return []

    for filename in os.listdir(FOLDER_PATH):
        file_path = os.path.join(FOLDER_PATH, filename)
        
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

    print("🌐 Scraping URLs...")
    web_docs_count = 0
    
    def scrape_with_fallback(url):
        """Try WebBaseLoader first, fallback to requests+BeautifulSoup if needed"""
        try:
            web_loader = WebBaseLoader(
                web_paths=[url],
                header_template={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            web_docs = web_loader.load()
            if web_docs and len(web_docs) > 0 and len(web_docs[0].page_content.strip()) > 50:
                return web_docs
        except Exception as e:
            print(f"    ⚠️  WebBaseLoader failed: {e}")
        
        if HAS_FALLBACK:
            try:
                print(f"    🔄 Trying fallback method...")
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                text = soup.get_text(separator='\n', strip=True)
                
                if len(text.strip()) > 50:
                    doc = Document(
                        page_content=text,
                        metadata={
                            "source": url,
                            "type": "website",
                            "url": url,
                            "title": soup.title.string if soup.title else "No title"
                        }
                    )
                    return [doc]
            except Exception as e:
                print(f"    ❌ Fallback method also failed: {e}")
        
        return None
    
    for url in URLS:
        try:
            print(f"  📡 Loading: {url}")
            web_docs = scrape_with_fallback(url)
            
            if web_docs:
                for doc in web_docs:
                    if not doc.metadata.get("source"):
                        doc.metadata["source"] = url
                    doc.metadata["type"] = "website"
                    doc.metadata["url"] = url
                    if not doc.page_content.startswith(f"[Source: {url}]"):
                        doc.page_content = f"[Source: {url}]\n\n{doc.page_content}"
                
                all_docs.extend(web_docs)
                web_docs_count += len(web_docs)
                print(f"  ✅ Successfully loaded {len(web_docs)} document(s) from {url} (content length: {sum(len(d.page_content) for d in web_docs)} chars)")
            else:
                print(f"  ❌ Failed to load {url}: No content extracted")
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ❌ Failed to load {url}: {e}")
            continue
    
    print(f"🌐 Total web documents loaded: {web_docs_count}")
    return all_docs

def main():
    raw_docs = load_documents()
    
    if not raw_docs:
        print("❌ No documents loaded. Check if 'fiek_documents' folder is empty or URLs are correct.")
        return

    print(f"✅ Total raw documents loaded: {len(raw_docs)}")
    
    pdf_count = sum(1 for doc in raw_docs if doc.metadata.get("type") != "website")
    web_count = sum(1 for doc in raw_docs if doc.metadata.get("type") == "website")
    print(f"   📄 PDF documents: {pdf_count}")
    print(f"   🌐 Web documents: {web_count}")

    print("\n✂️  Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    splits = text_splitter.split_documents(raw_docs)
    print(f"✂️  Split into {len(splits)} chunks.")
    
    web_chunks = sum(1 for split in splits if split.metadata.get("type") == "website")
    pdf_chunks = len(splits) - web_chunks
    print(f"   📄 PDF chunks: {pdf_chunks}")
    print(f"   🌐 Web chunks: {web_chunks}")

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
    print("🚀 Success! Database built at ./fiek_db")

if __name__ == "__main__":
    main()