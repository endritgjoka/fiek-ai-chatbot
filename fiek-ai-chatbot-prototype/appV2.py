import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="FIEK Assistant", layout="centered")
st.title("🤖 FIEK AI Assistant")

@st.cache_resource
def get_vectorstore():
    embedding = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(persist_directory="./fiek_db", embedding_function=embedding)
    return vectorstore

@st.cache_resource
def get_rag_chain():
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
        "- Answer in the ALBANIAN language unless the user explicitly asks in English.\n\n"
        "If the answer is not in the context, say 'Nuk kam informacion për këtë pyetje në dokumentet e mia.' (in Albanian) or 'I do not have that information in my documents' (in English).\n\n"
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

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Pyet rreth FIEK..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        chain = get_rag_chain()
        vectorstore = get_vectorstore()
        
        with st.spinner("Duke kërkuar në dokumente..."):
            chat_history = []
            for msg in st.session_state.messages[:-1]:
                if msg["role"] == "user":
                    chat_history.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    content = msg["content"]
                    if "---\n**Burimet:**" in content:
                        content = content.split("---\n**Burimet:**")[0].strip()
                    chat_history.append(AIMessage(content=content))
            
            answer = chain.invoke({
                "input": user_input,
                "chat_history": chat_history
            })
            
            docs = vectorstore.similarity_search(user_input, k=5)
            sources = list(set([doc.metadata.get("source", "Unknown") for doc in docs]))
            
            full_response = f"{answer}\n\n---\n**Burimet:**\n"
            for s in sources:
                full_response += f"- `{s}`\n"
            
            st.markdown(full_response)
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})