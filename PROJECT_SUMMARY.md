# FIEK AI Chatbot - Project Summary

## Project Overview

This project implements an AI-powered chatbot for the Faculty of Electrical and Computer Engineering (FIEK) at the University of Prishtina. The chatbot provides instant, accurate information to students, staff, and visitors in both English and Albanian languages.

## Key Features Implemented

### 1. Bilingual Support
- ✅ Natural language understanding in English
- ✅ Natural language understanding in Albanian
- ✅ Language toggle in UI
- ✅ Multilingual embedding model (paraphrase-multilingual-MiniLM-L12-v2)

### 2. Data Collection System
- ✅ Web scraping for FIEK website pages
- ✅ PDF text extraction from academic documents
- ✅ Custom data integration (Student Council, SEMS, etc.)
- ✅ Data merging and preparation pipeline

### 3. Knowledge Base Coverage
The chatbot can answer questions about:
- ✅ General FIEK information (Vision, Mission, Objectives)
- ✅ Dean's office and management
- ✅ Academic staff
- ✅ Administrative staff
- ✅ Student Council
- ✅ Academic programs (BSc, MSc, PhD)
- ✅ Course schedules (BSc and MSc)
- ✅ Regulations (Bachelor, Master, PhD, Mobility)
- ✅ Projects
- ✅ Collaborations (Industry, Universities, Public Institutions)
- ✅ Advisory bodies
- ✅ Infrastructure
- ✅ Notices and announcements
- ✅ Scholarships and mobility programs
- ✅ SEMS access information

### 4. NLP Architecture
- ✅ RAG (Retrieval Augmented Generation) approach
- ✅ Semantic search using FAISS vector database
- ✅ Document chunking with overlap
- ✅ Relevance scoring and filtering
- ✅ Multilingual sentence embeddings

### 5. User Interface
- ✅ Modern, responsive design
- ✅ Beautiful gradient styling
- ✅ Real-time chat interface
- ✅ Suggestion chips for quick queries
- ✅ Loading indicators
- ✅ Source attribution
- ✅ Mobile-friendly layout

### 6. Backend API
- ✅ Flask REST API
- ✅ CORS enabled for frontend
- ✅ Health check endpoint
- ✅ Chat endpoint with error handling
- ✅ Initialization endpoint

## Technical Stack

### Backend
- **Framework:** Flask 3.0.0
- **NLP:** Sentence Transformers 2.2.2
- **Vector Search:** FAISS 1.7.4
- **Web Scraping:** BeautifulSoup4 4.12.2
- **PDF Processing:** pdfplumber 0.10.3
- **HTTP Requests:** requests 2.31.0

### Frontend
- **HTML5** with semantic markup
- **CSS3** with modern features (Flexbox, Grid, Animations)
- **Vanilla JavaScript** (no frameworks for simplicity)

### NLP Model
- **Model:** paraphrase-multilingual-MiniLM-L12-v2
- **Embedding Dimension:** 384
- **Similarity Metric:** Cosine similarity (via inner product)

## Project Structure

```
NLP-Projekti/
├── backend/
│   ├── app.py                      # Flask API server
│   ├── setup.py                    # Automated setup script
│   ├── test_chatbot.py             # Testing script
│   ├── run.sh                      # Quick start script
│   ├── requirements.txt            # Python dependencies
│   ├── data_collection/
│   │   ├── scrape_data.py          # Web & PDF scraping
│   │   └── prepare_data.py         # Data merging
│   ├── models/
│   │   └── chatbot_model.py        # RAG chatbot implementation
│   └── knowledge_base/
│       ├── collected_data.json     # Merged knowledge base
│       └── custom_data.json        # Custom data entries
├── frontend/
│   ├── index.html                  # Main HTML file
│   ├── styles.css                  # Styling
│   └── script.js                   # Frontend logic
├── README.md                       # Main documentation
├── SETUP_GUIDE.md                  # Detailed setup instructions
└── PROJECT_SUMMARY.md              # This file
```

## How It Works

1. **Data Collection Phase:**
   - Scrapes web pages from FIEK website
   - Extracts text from PDF documents
   - Merges with custom data
   - Saves to JSON format

2. **Indexing Phase:**
   - Loads knowledge base from JSON
   - Splits documents into chunks (500 words, 100 word overlap)
   - Generates embeddings for each chunk
   - Builds FAISS index for fast similarity search

3. **Query Processing:**
   - User sends query (English or Albanian)
   - Query is embedded using multilingual model
   - Semantic search finds top-k relevant chunks
   - Response is generated from most relevant content
   - Sources are attributed

4. **Response Generation:**
   - Filters results by relevance threshold (0.3)
   - Uses top result for primary response
   - Adds supplementary info if highly relevant
   - Formats text for readability
   - Includes source attribution

## Usage Examples

### English Queries
- "What are the academic programs?"
- "Who is the dean of FIEK?"
- "What is the vision of FIEK?"
- "Show me the course schedule"
- "What are the regulations for Bachelor studies?"

### Albanian Queries
- "Cilat janë programet akademike?"
- "Kush është dekani i FIEK?"
- "Cili është vizioni i FIEK?"
- "Më trego orarin e lëndëve"
- "Cilat janë rregulloret për studimet Bachelor?"

## Performance Characteristics

- **Initialization:** 30-60 seconds (depends on knowledge base size)
- **Query Response Time:** 0.5-2 seconds (after initialization)
- **Memory Usage:** ~500MB-1GB
- **Knowledge Base:** Supports thousands of documents
- **Concurrent Users:** Limited by Flask (use production server for scale)

## Future Enhancements

Potential improvements:
1. Use larger language models for better response generation
2. Add conversation history and context
3. Implement user feedback mechanism
4. Add analytics and usage tracking
5. Deploy to cloud (Heroku, AWS, etc.)
6. Add authentication for sensitive queries
7. Implement caching for frequent queries
8. Add support for file uploads (PDFs, documents)
9. Integrate with FIEK's database systems
10. Add voice input/output capabilities

## Testing

Run the test script:
```bash
cd backend
python test_chatbot.py
```

This will test the chatbot with sample queries and verify functionality.

## Deployment Considerations

For production deployment:
1. Use production WSGI server (Gunicorn, uWSGI)
2. Set up proper error logging
3. Implement rate limiting
4. Use environment variables for configuration
5. Set up HTTPS
6. Use production-grade vector database if needed
7. Implement monitoring and alerting

## License

Educational project for Natural Language Processing course.

## Credits

Developed for FIEK (Faculty of Electrical and Computer Engineering), University of Prishtina.

