# FIEK Chatbot - Detailed Setup Guide

## Step-by-Step Installation

### 1. Prerequisites Check

Ensure you have:
- Python 3.8 or higher (`python --version`)
- pip installed (`pip --version`)
- Internet connection (for initial data collection)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### 2. Create Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# On Windows: venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt, indicating the virtual environment is active.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** This will install:
- Flask and Flask-CORS for the API
- Sentence Transformers for NLP
- FAISS for vector search
- BeautifulSoup4 and pdfplumber for data collection
- Other required libraries

**Installation time:** 5-10 minutes depending on your internet speed.

### 4. Collect Data

The chatbot needs data from FIEK's website. Run:

```bash
python setup.py
```

This will:
1. Scrape web pages from FIEK website
2. Extract text from PDF documents
3. Merge with custom data
4. Save everything to `knowledge_base/collected_data.json`

**Time required:** 10-15 minutes (depends on website response times)

**What if data collection fails?**
- Check your internet connection
- Some PDFs might be large - be patient
- You can manually edit `knowledge_base/custom_data.json` and run `python data_collection/prepare_data.py`

### 5. Verify Setup

Test the chatbot:

```bash
python test_chatbot.py
```

You should see test queries and responses. If you see errors, check:
- Is `knowledge_base/collected_data.json` present?
- Are all dependencies installed?

### 6. Start the Backend

**Important:** Make sure your virtual environment is activated (you should see `(venv)` in your prompt).

```bash
python app.py
```

You should see:
```
Initializing FIEK Chatbot...
Loading language model...
Building search index...
Generating embeddings for X chunks...
Chatbot initialized successfully!
 * Running on http://0.0.0.0:5000
```

**Keep this terminal window open!**

### 7. Open the Frontend

**Option A: Direct file open**
- Navigate to `frontend/` folder
- Double-click `index.html`
- It will open in your default browser

**Option B: Local server (recommended)**
```bash
cd frontend
python -m http.server 8000
```
Then open: http://localhost:8000

### 8. Start Chatting!

- Type questions in English or Albanian
- Use suggestion chips for quick queries
- Switch languages with EN/SQ toggle

## Troubleshooting

### "Chatbot not initialized"

**Solution:**
1. Check if `knowledge_base/collected_data.json` exists
2. If not, run `python setup.py`
3. Restart the backend: `python app.py`

### "Cannot connect to server"

**Solution:**
1. Make sure backend is running (`python app.py`)
2. Check if port 5000 is available
3. Try changing port in `app.py`: `app.run(port=5001)`
4. Update `frontend/script.js`: Change `API_URL` to `http://localhost:5001/api`

### "No data found" or empty responses

**Solution:**
1. Verify data collection completed: Check `knowledge_base/collected_data.json` file size
2. Re-run data collection: `python setup.py`
3. Check internet connection (needed for initial scraping)

### Import errors

**Solution:**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# If specific package fails, install manually:
pip install sentence-transformers faiss-cpu flask flask-cors
```

### PDF extraction fails

**Solution:**
- Some PDFs might be corrupted or password-protected
- The script will skip failed PDFs and continue
- You can manually add content to `custom_data.json`

## Adding Custom Data

Edit `backend/knowledge_base/custom_data.json`:

```json
[
  {
    "title": "Keshilli i Studenteve",
    "url": "",
    "content": "Your detailed content here...",
    "type": "custom"
  },
  {
    "title": "New Topic",
    "url": "https://example.com",
    "content": "More content...",
    "type": "custom"
  }
]
```

Then run:
```bash
python data_collection/prepare_data.py
```

Restart the backend to load new data.

## Performance Tips

1. **First query is slow:** The model loads on first use. Subsequent queries are faster.

2. **Large knowledge base:** If you have many documents, indexing takes time. Be patient during initialization.

3. **Memory usage:** The chatbot uses ~500MB-1GB RAM. Close other applications if needed.

## Next Steps

- Customize the UI in `frontend/styles.css`
- Improve responses in `backend/models/chatbot_model.py`
- Add more data sources
- Deploy to a server (see deployment section in README)

## Getting Help

If you encounter issues:
1. Check error messages in the terminal
2. Review the logs
3. Verify all steps in this guide
4. Check that all files are in the correct locations

