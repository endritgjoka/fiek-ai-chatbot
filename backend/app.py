"""
Flask API for FIEK Chatbot
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from pathlib import Path
from models.chatbot_model import FIEKChatbot

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize chatbot
print("Initializing FIEK Chatbot...")
chatbot = None

def initialize_chatbot():
    """Initialize the chatbot instance."""
    global chatbot
    try:
        chatbot = FIEKChatbot()
        return True
    except Exception as e:
        print(f"Error initializing chatbot: {e}")
        return False

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'chatbot_initialized': chatbot is not None
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages."""
    if chatbot is None:
        # Try to initialize if not already done
        if not initialize_chatbot():
            return jsonify({
                'error': 'Chatbot not initialized. Please run data collection first using: python setup.py'
            }), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Invalid request. JSON body required.'
            }), 400
        
        query = data.get('message', '').strip()
        
        if not query:
            return jsonify({
                'error': 'Message is required'
            }), 400
        
        # Get answer from chatbot
        result = chatbot.answer(query)
        
        return jsonify({
            'response': result['response'],
            'sources': result['sources'],
            'confidence': result['confidence']
        })
    
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500

@app.route('/api/initialize', methods=['POST'])
def initialize():
    """Manually initialize chatbot."""
    global chatbot
    success = initialize_chatbot()
    
    if success:
        return jsonify({'status': 'initialized'})
    else:
        return jsonify({'error': 'Failed to initialize'}), 500

if __name__ == '__main__':
    # Try to initialize on startup
    initialize_chatbot()
    
    # Run Flask app
    # Use 5001 as default since 5000 is often used by macOS AirPlay
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)

