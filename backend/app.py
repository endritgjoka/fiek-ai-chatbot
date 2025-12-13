"""
Flask API for FIEK Chatbot using LangChain RAG
"""

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import os
import json
from pathlib import Path
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize chatbot components
print("Initializing FIEK Chatbot...")
vectorstore = None
rag_chain = None

def get_vectorstore():
    """Get or initialize the Chroma vectorstore."""
    global vectorstore
    if vectorstore is None:
        embedding = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = Chroma(persist_directory="./fiek_db", embedding_function=embedding)
    return vectorstore

def get_rag_chain():
    """Get or initialize the RAG chain."""
    global rag_chain
    if rag_chain is None:
        vectorstore = get_vectorstore()
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        system_prompt = (
            "You are a helpful assistant for the Faculty of Electrical and Computer Engineering (FIEK). "
            "Use the provided context to answer the student's question accurately. "
            "You have access to the conversation history, so you can understand references to previous questions and answers. "
            "\n\n"
            "IMPORTANT INSTRUCTIONS:\n"
            "- When the user asks about FIEK (e.g., 'who is the dean of fiek', 'fiek dean', 'dean'), understand that they are asking about FIEK specifically. "
            "- Be flexible with question variations: 'dean of fiek', 'fiek dean', 'who is the dean', 'the dean' all refer to the same thing. "
            "- When the user uses similar terms (like 'schedule' and 'timetable', 'program' and 'programme'), understand they refer to the same concept. "
            "- Extract the core question from the user's query, ignoring redundant words or variations in phrasing. "
            "- If the context contains relevant information even if the exact wording doesn't match, use it to answer. "
            "- CRITICAL: Always answer in the SAME LANGUAGE as the user's question. If the user asks in English, answer in English. If the user asks in Albanian, answer in Albanian.\n\n"
            "If the answer is not in the context, say 'Nuk kam informacion për këtë pyetje në dokumentet e mia.' (in Albanian) or 'I do not have that information in my documents' (in English), matching the language of the question.\n\n"
            "Context:\n{context}"
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        def retrieve_context(input_data):
            query = input_data["input"]
            docs = retriever.invoke(query)
            return {
                "context": format_docs(docs),
                "input": query,
                "chat_history": input_data["chat_history"]
            }
        
        rag_chain = (
            RunnableLambda(retrieve_context)
            | prompt
            | llm
            | StrOutputParser()
        )
    
    return rag_chain

def initialize_chatbot():
    """Initialize the chatbot components."""
    try:
        get_vectorstore()
        get_rag_chain()
        return True
    except Exception as e:
        print(f"Error initializing chatbot: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'chatbot_initialized': vectorstore is not None and rag_chain is not None
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with conversation history."""
    # Try to initialize if not already done
    global vectorstore, rag_chain
    if vectorstore is None or rag_chain is None:
        if not initialize_chatbot():
            return jsonify({
                'error': 'Chatbot not initialized. Please check your .env file and ensure the vectorstore is set up.'
            }), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Invalid request. JSON body required.'
            }), 400
        
        # Get user message - support both 'message' and 'messages' format
        if 'messages' in data:
            # Extract the last user message from the messages array
            messages = data.get('messages', [])
            user_messages = [msg for msg in messages if msg.get('role') == 'user']
            if not user_messages:
                return jsonify({
                    'error': 'No user message found in messages array'
                }), 400
            query = user_messages[-1].get('content', '').strip()
            
            # Build chat history from previous messages (excluding system and last user message)
            chat_history = []
            for msg in messages[:-1]:  # Exclude the last user message
                role = msg.get('role', '')
                content = msg.get('content', '')
                if role == 'user':
                    chat_history.append(HumanMessage(content=content))
                elif role == 'assistant':
                    # Remove sources section if present
                    if "---\n**Burimet:**" in content:
                        content = content.split("---\n**Burimet:**")[0].strip()
                    chat_history.append(AIMessage(content=content))
        else:
            # Legacy format: single message
            query = data.get('message', '').strip()
            chat_history = []
        
        if not query:
            return jsonify({
                'error': 'Message is required'
            }), 400
        
        # Get RAG chain and vectorstore
        chain = get_rag_chain()
        vs = get_vectorstore()
        
        # Invoke the chain with query and chat history
        answer = chain.invoke({
            "input": query,
            "chat_history": chat_history
        })
        
        # Get sources
        docs = vs.similarity_search(query, k=5)
        sources = list(set([doc.metadata.get("source", "Unknown") for doc in docs]))
        
        # Format response with sources (matching appV2.py format)
        full_response = f"{answer}\n\n---\n**Burimet:**\n"
        for s in sources:
            full_response += f"- `{s}`\n"
        
        # Return response in format expected by frontend
        return jsonify({
            'reply': full_response,  # Frontend expects 'reply' or 'content'
            'content': full_response,  # Alternative field name
            'response': answer,  # Just the answer without sources
            'sources': sources
        })
    
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """Handle chat messages with streaming response."""
    # Try to initialize if not already done
    global vectorstore, rag_chain
    if vectorstore is None or rag_chain is None:
        if not initialize_chatbot():
            return jsonify({
                'error': 'Chatbot not initialized. Please check your .env file and ensure the vectorstore is set up.'
            }), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Invalid request. JSON body required.'
            }), 400
        
        # Get user message - support both 'message' and 'messages' format
        if 'messages' in data:
            # Extract the last user message from the messages array
            messages = data.get('messages', [])
            user_messages = [msg for msg in messages if msg.get('role') == 'user']
            if not user_messages:
                return jsonify({
                    'error': 'No user message found in messages array'
                }), 400
            query = user_messages[-1].get('content', '').strip()
            
            # Build chat history from previous messages (excluding system and last user message)
            chat_history = []
            for msg in messages[:-1]:  # Exclude the last user message
                role = msg.get('role', '')
                content = msg.get('content', '')
                if role == 'user':
                    chat_history.append(HumanMessage(content=content))
                elif role == 'assistant':
                    # Remove sources section if present
                    if "---\n**Burimet:**" in content:
                        content = content.split("---\n**Burimet:**")[0].strip()
                    chat_history.append(AIMessage(content=content))
        else:
            # Legacy format: single message
            query = data.get('message', '').strip()
            chat_history = []
        
        if not query:
            return jsonify({
                'error': 'Message is required'
            }), 400
        
        # Get RAG chain and vectorstore
        chain = get_rag_chain()
        vs = get_vectorstore()
        
        # Get sources first (before streaming)
        docs = vs.similarity_search(query, k=5)
        sources = list(set([doc.metadata.get("source", "Unknown") for doc in docs]))
        
        def generate():
            """Generator function for streaming response."""
            try:
                # Get the chain components for direct LLM streaming
                vectorstore = get_vectorstore()
                retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
                
                system_prompt = (
                    "You are a helpful assistant for the Faculty of Electrical and Computer Engineering (FIEK). "
                    "Use the provided context to answer the student's question accurately. "
                    "You have access to the conversation history, so you can understand references to previous questions and answers. "
                    "\n\n"
                    "IMPORTANT INSTRUCTIONS:\n"
                    "- When the user asks about FIEK (e.g., 'who is the dean of fiek', 'fiek dean', 'dean'), understand that they are asking about FIEK specifically. "
                    "- Be flexible with question variations: 'dean of fiek', 'fiek dean', 'who is the dean', 'the dean' all refer to the same thing. "
                    "- When the user uses similar terms (like 'schedule' and 'timetable', 'program' and 'programme'), understand they refer to the same concept. "
                    "- Extract the core question from the user's query, ignoring redundant words or variations in phrasing. "
                    "- If the context contains relevant information even if the exact wording doesn't match, use it to answer. "
                    "- CRITICAL: Always answer in the SAME LANGUAGE as the user's question. If the user asks in English, answer in English. If the user asks in Albanian, answer in Albanian.\n\n"
                    "If the answer is not in the context, say 'Nuk kam informacion për këtë pyetje në dokumentet e mia.' (in Albanian) or 'I do not have that information in my documents' (in English), matching the language of the question.\n\n"
                    "Context:\n{context}"
                )
                
                prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{input}"),
                ])
                
                # Retrieve context
                docs = retriever.invoke(query)
                context = "\n\n".join(doc.page_content for doc in docs)
                
                # Create the prompt with context
                formatted_prompt = prompt.format_messages(
                    context=context,
                    chat_history=chat_history,
                    input=query
                )
                
                # Stream directly from LLM
                full_answer = ""
                for chunk in llm.stream(formatted_prompt):
                    if hasattr(chunk, 'content') and chunk.content:
                        content = chunk.content
                        full_answer += content
                        # Send each chunk as JSON
                        yield f"data: {json.dumps({'type': 'chunk', 'content': content})}\n\n"
                
                # Send sources section
                sources_text = "\n\n---\n**Burimet:**\n"
                for s in sources:
                    sources_text += f"- `{s}`\n"
                
                yield f"data: {json.dumps({'type': 'sources', 'content': sources_text})}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                
            except Exception as e:
                error_msg = f"Error during streaming: {str(e)}"
                print(error_msg)
                import traceback
                traceback.print_exc()
                yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
    
    except Exception as e:
        print(f"Error in chat_stream endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500

@app.route('/api/initialize', methods=['POST'])
def initialize():
    """Manually initialize chatbot."""
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

