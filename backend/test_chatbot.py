"""
Simple test script to verify the chatbot is working.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from models.chatbot_model import FIEKChatbot

def test_chatbot():
    """Test the chatbot with sample queries."""
    print("Testing FIEK Chatbot")
    print("=" * 60)
    
    try:
        # Initialize chatbot
        print("\nInitializing chatbot...")
        chatbot = FIEKChatbot()
        
        if not chatbot.knowledge_base:
            print("\n⚠️  Warning: Knowledge base is empty!")
            print("Please run: python setup.py")
            return
        
        # Test queries
        test_queries = [
            "What is FIEK?",
            "What are the academic programs?",
            "Who is the dean?",
            "Cilat janë programet akademike?",
            "What is the vision of FIEK?",
        ]
        
        print(f"\nTesting {len(test_queries)} queries...\n")
        
        for i, query in enumerate(test_queries, 1):
            print(f"Query {i}: {query}")
            print("-" * 60)
            
            try:
                result = chatbot.answer(query)
                print(f"Response: {result['response'][:200]}...")
                print(f"Sources: {result['sources']}")
                print(f"Confidence: {result['confidence']:.3f}")
            except Exception as e:
                print(f"Error: {e}")
            
            print("\n")
        
        print("=" * 60)
        print("Test completed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_chatbot()

