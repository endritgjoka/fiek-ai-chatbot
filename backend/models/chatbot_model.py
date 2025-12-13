"""
Chatbot model using RAG (Retrieval Augmented Generation) approach.
Supports bilingual queries in English and Albanian.
"""

import json
import os
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Dict, Tuple
import re

class FIEKChatbot:
    def __init__(self, knowledge_base_path: str = None):
        """Initialize the chatbot with knowledge base."""
        # Load multilingual model for Albanian and English
        print("Loading language model...")
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        # Load knowledge base
        if knowledge_base_path is None:
            kb_path = Path(__file__).parent.parent / "knowledge_base" / "collected_data.json"
        else:
            kb_path = Path(knowledge_base_path)
        
        self.knowledge_base = self._load_knowledge_base(kb_path)
        
        # Build search index
        print("Building search index...")
        self.index, self.documents = self._build_index()
        
        print("Chatbot initialized successfully!")
    
    def _load_knowledge_base(self, path: Path) -> List[Dict]:
        """Load knowledge base from JSON file."""
        if not path.exists():
            print(f"Knowledge base not found at {path}")
            print("Please run data collection first.")
            return []
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        
        return chunks
    
    def _build_index(self) -> Tuple[faiss.Index, List[Dict]]:
        """Build FAISS index for semantic search."""
        if not self.knowledge_base:
            # Create empty index
            dimension = 384  # Dimension for multilingual-MiniLM
            index = faiss.IndexFlatL2(dimension)
            return index, []
        
        documents = []
        texts = []
        
        for doc in self.knowledge_base:
            # Split document into chunks
            chunks = self._chunk_text(doc['content'])
            
            for i, chunk in enumerate(chunks):
                documents.append({
                    'title': doc['title'],
                    'url': doc.get('url', ''),
                    'chunk_index': i,
                    'text': chunk,
                    'type': doc.get('type', 'web_page')
                })
                texts.append(chunk)
        
        if not texts:
            dimension = 384
            index = faiss.IndexFlatL2(dimension)
            return index, []
        
        # Generate embeddings
        print(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        index.add(embeddings.astype('float32'))
        
        return index, documents
    
    def _search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search for relevant documents."""
        if not self.documents:
            return []
        
        # Encode query
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                results.append({
                    'document': self.documents[idx],
                    'score': float(distances[0][i])
                })
        
        return results
    
    def _generate_response(self, query: str, context: List[Dict]) -> str:
        """Generate response based on query and context."""
        if not context:
            return "I'm sorry, I couldn't find relevant information to answer your question. Please try rephrasing your query or ask about FIEK's programs, staff, schedules, or other institutional information."
        
        # Filter results by relevance (score > 0.3)
        relevant_context = [r for r in context if r['score'] > 0.3]
        
        if not relevant_context:
            return "I couldn't find highly relevant information. Could you please rephrase your question or ask about a specific topic like academic programs, staff, schedules, or regulations?"
        
        # Get the most relevant document
        top_result = relevant_context[0]
        top_text = top_result['document']['text']
        
        # Clean and format the response
        # Remove excessive whitespace
        top_text = ' '.join(top_text.split())
        
        # Limit response length for better readability
        max_length = 800
        if len(top_text) > max_length:
            # Try to cut at sentence boundary
            truncated = top_text[:max_length]
            last_period = truncated.rfind('.')
            last_newline = truncated.rfind('\n')
            cut_point = max(last_period, last_newline)
            if cut_point > max_length * 0.7:  # Only if we found a good break point
                top_text = truncated[:cut_point + 1]
            else:
                top_text = truncated + "..."
        
        # Build natural response
        response = top_text
        
        # Add additional context if available and relevant
        if len(relevant_context) > 1:
            second_result = relevant_context[1]
            if second_result['score'] > 0.4:  # Only if highly relevant
                second_text = second_result['document']['text']
                second_text = ' '.join(second_text.split())
                if len(second_text) < 300:  # Only add if it's concise
                    response += f"\n\nAdditional information:\n{second_text[:300]}"
        
        return response
    
    def answer(self, query: str, top_k: int = 3) -> Dict:
        """Answer a user query."""
        # Search for relevant information
        results = self._search(query, top_k)
        
        # Generate response
        response = self._generate_response(query, results)
        
        # Get unique sources
        sources = list(set([r['document']['title'] for r in results if r['score'] > 0.3]))
        
        return {
            'response': response,
            'sources': sources,
            'confidence': float(results[0]['score']) if results else 0.0
        }
    
    def add_custom_data(self, title: str, content: str, url: str = "", doc_type: str = "custom"):
        """Add custom data to knowledge base (e.g., Student Council info)."""
        new_doc = {
            "title": title,
            "url": url,
            "content": content,
            "type": doc_type
        }
        
        self.knowledge_base.append(new_doc)
        
        # Rebuild index
        self.index, self.documents = self._build_index()

