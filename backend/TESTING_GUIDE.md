# Testing Guide for ingest.py and appV2.py

This guide will walk you through testing both `ingest.py` (data ingestion) and `appV2.py` (Streamlit chatbot app).

## Prerequisites

Before testing, ensure you have:

1. ✅ Virtual environment set up and activated
2. ✅ All dependencies installed (`pip install -r requirements.txt`)
3. ✅ `.env` file with `OPENAI_API_KEY` set
4. ✅ (Optional) Tesseract OCR installed for scanned PDF support

### Quick Setup Check

```bash
# Make sure you're in the backend directory
cd backend

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Verify dependencies
pip list | grep langchain
pip list | grep streamlit

# Check .env file exists and has API key
# Windows:
type .env
# macOS/Linux:
cat .env
```

---

## Part 1: Testing ingest.py

The `ingest.py` script:

- Loads PDFs from `./fiek_documents/` folder
- Scrapes web pages from FIEK website
- Processes and chunks the documents
- Creates a ChromaDB vector database at `./fiek_db`

### Step 1: Prepare Test Environment

```bash
# Make sure you're in the backend directory
cd backend

# Create fiek_documents folder if it doesn't exist (optional - for PDFs)
mkdir -p fiek_documents

# You can add PDF files here if you have any, but it's not required
# The script will also scrape web pages automatically
```

### Step 2: Run ingest.py

```bash
# Make sure virtual environment is activated
python models/ingest.py
```

### Step 3: What to Expect

You should see output like:

```
⚠️  Tesseract OCR not found. OCR functionality will be disabled.
   (This is OK if you don't have Tesseract installed)

🌐 Scraping URLs...
  📡 Loading: https://fiek.uni-pr.edu/page.aspx?id=1,8
  ✅ Successfully loaded 1 document(s) from https://fiek.uni-pr.edu/page.aspx?id=1,8
  📡 Loading: https://fiek.uni-pr.edu/page.aspx?id=1,9
  ✅ Successfully loaded 1 document(s) from https://fiek.uni-pr.edu/page.aspx?id=1,9
  ...

✅ Total raw documents loaded: 15
   📄 PDF documents: 0
   🌐 Web documents: 15

✂️  Splitting documents into chunks...
✂️  Split into 45 chunks.
   📄 PDF chunks: 0
   🌐 Web chunks: 45

💾 Saving to Vector Database (ChromaDB)...
🚀 Success! Database built at ./fiek_db
```

### Step 4: Verify Success

Check that the database was created:

```bash
# Check if fiek_db directory exists
# Windows:
dir fiek_db
# macOS/Linux:
ls -la fiek_db
```

You should see files like:

- `chroma.sqlite3`
- Various subdirectories with data files

### Troubleshooting ingest.py

**Error: "OPENAI_API_KEY not found"**

- Solution: Make sure `.env` file exists in `backend/` directory
- Check: `OPENAI_API_KEY=your_actual_key_here` (no quotes, no spaces around `=`)

**Error: "No documents loaded"**

- This is OK if `fiek_documents/` folder is empty
- The script should still scrape web pages from URLs
- If web scraping fails, check your internet connection

**Warning: "Tesseract OCR not found"**

- This is optional - the script will work without it
- OCR is only needed for scanned PDFs
- Digital PDFs will work fine without Tesseract

**Import errors**

- Make sure virtual environment is activated
- Run: `pip install -r requirements.txt`

---

## Part 2: Testing appV2.py

The `appV2.py` is a Streamlit web application that:

- Loads the vector database created by `ingest.py`
- Provides a chat interface
- Answers questions using RAG (Retrieval Augmented Generation)

### Step 1: Ensure Database Exists

**IMPORTANT:** You must run `ingest.py` first to create the `./fiek_db` database!

```bash
# Verify database exists
# Windows:
dir fiek_db
# macOS/Linux:
ls -la fiek_db
```

If it doesn't exist, go back to Part 1 and run `ingest.py` first.

### Step 2: Run appV2.py

```bash
# Make sure you're in the backend directory
cd backend

# Make sure virtual environment is activated
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Run Streamlit app
streamlit run appV2.py
```

### Step 3: What to Expect

You should see:

```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

Your default browser should automatically open to `http://localhost:8501`

### Step 4: Test the Chat Interface

1. **You should see:**

   - Title: "🤖 FIEK AI Assistant"
   - A chat input box with placeholder: "Pyet rreth FIEK..."

2. **Try asking questions:**

   - In Albanian: "Cili është vizioni i FIEK?"
   - In English: "What is the vision of FIEK?"
   - "Kush është dekani?" (Who is the dean?)
   - "Cilat janë programet akademike?" (What are the academic programs?)

3. **Expected behavior:**
   - You type a question and press Enter
   - You see a spinner: "Duke kërkuar në dokumente..." (Searching in documents...)
   - The assistant responds with an answer
   - Sources are listed at the bottom

### Step 5: Verify It's Working

**Good signs:**

- ✅ App loads without errors
- ✅ You can type questions
- ✅ You get responses (even if they say "I don't have that information")
- ✅ Sources are listed at the bottom of responses

**Bad signs:**

- ❌ Error message about missing database
- ❌ Error about OPENAI_API_KEY
- ❌ Import errors
- ❌ App crashes when you ask a question

### Troubleshooting appV2.py

**Error: "ChromaDB database not found" or similar**

- Solution: Run `python models/ingest.py` first to create the database
- Make sure you're running from the `backend/` directory

**Error: "OPENAI_API_KEY not found"**

- Solution: Check `.env` file exists and has the correct API key
- Make sure `.env` is in the `backend/` directory

**Error: "ModuleNotFoundError" or import errors**

- Solution: Make sure virtual environment is activated
- Run: `pip install -r requirements.txt`

**App loads but gives no response or errors**

- Check the terminal/console for error messages
- Verify the database was created successfully (check `fiek_db/` folder)
- Make sure your OpenAI API key is valid and has credits

**Streamlit command not found**

- Solution: `pip install streamlit`
- Make sure virtual environment is activated

---

## Quick Test Script

Here's a quick test to verify everything works:

```bash
# 1. Test ingest.py
cd backend
python models/ingest.py
# Should complete without errors and create ./fiek_db

# 2. Test appV2.py
streamlit run appV2.py
# Should open in browser, try asking a question
```

---

## Expected File Structure After Testing

```
backend/
├── .env                    # Your API keys
├── fiek_db/               # Vector database (created by ingest.py)
│   ├── chroma.sqlite3
│   └── [other files]
├── fiek_documents/        # Optional: PDF files go here
├── models/
│   └── ingest.py          # ✅ Tested
├── appV2.py               # ✅ Tested
└── requirements.txt
```

---

## Next Steps

Once both are working:

- Add more PDFs to `fiek_documents/` folder
- Customize the system prompt in `appV2.py`
- Adjust chunk size and overlap in `ingest.py`
- Deploy the Streamlit app (Streamlit Cloud, Heroku, etc.)

---

## Getting Help

If you encounter issues:

1. Check the error messages in the terminal
2. Verify all prerequisites are met
3. Check that `.env` file has correct `OPENAI_API_KEY`
4. Make sure virtual environment is activated
5. Ensure `fiek_db` exists before running `appV2.py`
