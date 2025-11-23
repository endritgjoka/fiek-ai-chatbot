# FIEK AI Chatbot

An AI-powered chatbot for the Faculty of Electrical and Computer Engineering (FIEK) that provides instant information about academic programs, staff, schedules, and institutional details in both English and Albanian.

## Features

- 🌍 **Bilingual Support**: Understands and responds in both English and Albanian
- 🤖 **Natural Language Understanding**: Advanced NLP for intent recognition
- 📚 **Comprehensive Knowledge Base**: Information on:
  - Academic programs (BSc, MSc, PhD)
  - Faculty staff and professors
  - Course schedules
  - Regulations and policies
  - Projects and collaborations
  - Infrastructure and facilities
  - Notices and announcements
  - Scholarships and mobility programs
- 🎨 **Modern UI/UX**: Beautiful, responsive chat interface
- ⚡ **Fast Retrieval**: Semantic search using FAISS

## Project Structure

```
NLP-Projekti/
├── backend/
│   ├── app.py                      # Main Flask application
│   ├── setup.py                    # Setup script
│   ├── data_collection/            # Data scraping scripts
│   │   ├── scrape_data.py          # Web scraping and PDF extraction
│   │   └── prepare_data.py         # Data merging
│   ├── models/                     # NLP models
│   │   └── chatbot_model.py        # RAG-based chatbot
│   ├── knowledge_base/             # Processed knowledge base
│   │   ├── collected_data.json     # Merged knowledge base
│   │   └── custom_data.json        # Custom data (Student Council, etc.)
│   └── requirements.txt
├── frontend/
│   ├── index.html                  # Main HTML file
│   ├── styles.css                  # Styling
│   └── script.js                   # Frontend logic
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser

### Installation Steps

1. **Create and activate virtual environment (recommended):**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# On Windows: venv\Scripts\activate
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Collect and prepare data:**
```bash
# Option 1: Run automated setup (recommended)
python setup.py

# Option 2: Manual setup
python data_collection/scrape_data.py
python data_collection/prepare_data.py
```

**Note:** Data collection may take 10-15 minutes as it scrapes multiple web pages and PDFs. Be patient!

3. **Start the backend server:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # On macOS/Linux
python app.py
```

The server will start on `http://localhost:5001`

4. **Open the frontend:**
   - Open `frontend/index.html` in your web browser
   - Or use a local server (recommended):
   ```bash
   # Using Python
   cd frontend
   python -m http.server 8000
   # Then open http://localhost:8000
   ```

## Usage

1. **Ask questions in English or Albanian:**
   - "What are the academic programs?"
   - "Who is the dean?"
   - "What is the vision of FIEK?"
   - "Show me the course schedule"
   - "Cilat janë programet akademike?"
   - "Kush është dekani?"

2. **Use suggestion chips** for quick queries

3. **Switch languages** using the EN/SQ toggle

## Technologies

- **Backend:**
  - Flask (Web framework)
  - Sentence Transformers (Multilingual embeddings)
  - FAISS (Vector search)
  - BeautifulSoup4 (Web scraping)
  - pdfplumber (PDF extraction)

- **Frontend:**
  - HTML5, CSS3, JavaScript
  - Modern responsive design

- **NLP Approach:**
  - RAG (Retrieval Augmented Generation)
  - Semantic search with multilingual embeddings
  - Document chunking and indexing

## Data Sources

The chatbot uses data from:
- FIEK official website
- Academic program PDFs
- Course schedules
- Regulations and policies
- Custom data (Student Council, etc.)

## Troubleshooting

### Chatbot not responding
- Ensure the backend server is running
- Check that `knowledge_base/collected_data.json` exists
- Verify data collection completed successfully

### No data found
- Run `python backend/setup.py` to collect data
- Check your internet connection (needed for initial data collection)
- Verify the FIEK website URLs are accessible

### Import errors
- Ensure all dependencies are installed: `pip install -r backend/requirements.txt`
- Use Python 3.8 or higher

## Development

### Adding Custom Data

Edit `backend/knowledge_base/custom_data.json` to add custom information:

```json
[
  {
    "title": "Your Title",
    "url": "Optional URL",
    "content": "Your content here...",
    "type": "custom"
  }
]
```

Then run `python backend/data_collection/prepare_data.py` to merge.

### Improving Responses

Modify `backend/models/chatbot_model.py` to adjust:
- Chunk size and overlap
- Relevance thresholds
- Response generation logic

## License

This project is developed for educational purposes as part of the Natural Language Processing course.

## Contact

For questions or issues, please contact the development team.

