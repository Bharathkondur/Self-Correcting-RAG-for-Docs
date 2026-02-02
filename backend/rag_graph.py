from typing import Dict, TypedDict, List
from langgraph.graph import StateGraph, END

from langchain_core.documents import Document
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
try:
    from langchain_ollama import ChatOllama
except ImportError:
    ChatOllama = None
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Graph State
class GraphState(TypedDict):
    """
    Represents the state of our graph.
    
    Attributes:
        keys: A dictionary where each key is a string.
    """
    question: str
    generation: str
    documents: List[str]
    try_count: int

def get_llm(model_type="reasoning"):
    """
    Factory to get the right LLM.
    model_type: 'reasoning' (standard) or 'grader' (smart/strict) or 'smart'
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if api_key:
        if model_type == "grader":
            return ChatOpenAI(model="gpt-4", temperature=0)
        else:
            return ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    else:
        # Fallback to Ollama
        # Ideally user should have 'mistral' or 'llama3' pulled
        if model_type == "grader":
             # Grader needs to be decent.
             return ChatOllama(model="mistral", temperature=0)
        else:
             return ChatOllama(model="mistral", temperature=0)

def build_graph(retriever):
    """
    Builds the Self-Correcting RAG Graph.
    """
    
    # --- Nodes ---
    
    def retrieve(state):
        print("---RETRIEVE---")
        question = state["question"]
        try:
            # Modern LangChain uses invoke
            documents = retriever.invoke(question)
        except AttributeError:
             # Fallback for older versions or different objects
            documents = retriever.get_relevant_documents(question)
            
        return {"documents": documents, "question": question}

    def generate(state):
        print("---GENERATE---")
        question = state["question"]
        documents = state["documents"]
        try_count = state.get("try_count", 0) + 1
        
        # Format documents as text
        context = "\n\n".join([doc.page_content if hasattr(doc, 'page_content') else str(doc) for doc in documents])
        
        # Simple generation chain
        llm = get_llm("reasoning")
        prompt = ChatPromptTemplate.from_template(
            "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.\nQuestion: {question} \nContext: {context} \nAnswer:"
        )
        chain = prompt | llm | StrOutputParser()
        generation = chain.invoke({"context": context, "question": question})
        return {"documents": documents, "question": question, "generation": generation, "try_count": try_count}

    def grade_documents(state):
        print("---CHECK RELEVANCE---")
        question = state["question"]
        documents = state["documents"]
        
        # LLM grader
        llm = get_llm("grader")
        
        # Grading prompt
        system = """You are a grader assessing relevance of a retrieved document to a user question. \n 
            If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
            Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
        
        grade_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
            ]
        )
        
        grader_chain = grade_prompt | llm
        
        # Filter relevant docs
        filtered_docs = []
        for d in documents:
            score = grader_chain.invoke({"question": question, "document": d.page_content})
            print(f"DEBUG: Grade result for doc: {score.content}")
            # Relaxed parsing: Check if 'yes' is anywhere in the response
            if "yes" in score.content.lower():
                filtered_docs.append(d)
        
        # Fallback: If no docs passed, keep all of them (avoid strict filtering locally)
        if not filtered_docs:
            print("WARNING: All documents filtered out. Keeping original retrieval for robustness.")
            filtered_docs = documents

        return {"documents": filtered_docs, "question": question}

    def transform_query(state):
        print("---TRANSFORM QUERY---")
        question = state["question"]
        documents = state["documents"]
        
        # Re-write question
        llm = get_llm("reasoning")
        system = """You a question re-writer that converts an input question to a better version that is optimized \n 
            for vectorstore retrieval. Look at the input and try to reason about the underlying semantic intent / meaning."""
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "Here is the initial question: \n\n {question} \n Formulate an improved question."),
            ]
        )
        chain = prompt | llm | StrOutputParser()
        better_question = chain.invoke({"question": question})
        
        return {"documents": documents, "question": better_question}

    # --- Edges ---
    
    def decide_to_generate(state):
        print("---DECIDE TO GENERATE---")
        filtered_documents = state["documents"]
        
        if not filtered_documents:
            # All documents have been filtered check_relevance
            # We will re-generate a new query
            return "transform_query"
        else:
            # We have relevant documents, so generate answer
            return "generate"

    
    def grade_generation_v_documents_and_question(state):
        print("---CHECK HALLUCINATIONS---")
        question = state["question"]
        documents = state["documents"]
        generation = state["generation"]
        try_count = state.get("try_count", 0)
        
        # Max retries hit?
        if try_count > 1:
            print("---DECISION: MAX RETRIES REACHED. RETURNING GENERATION---")
            return "useful"
        
        llm = get_llm("grader")
        
        # Hallucination Grader
        system_hallucination = """You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. \n 
            Give a binary score 'yes' or 'no'. 'Yes' means the answer is grounded in and supported by the set of facts."""
        hallucination_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_hallucination),
                ("human", "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"),
            ]
        )
        hallucination_chain = hallucination_prompt | llm
        
        # Answer Relevance Grader
        system_answer = """You are a grader assessing whether an answer addresses / resolves a question. \n 
            Give a binary score 'yes' or 'no'. 'Yes' means the answer resolves the question."""
        answer_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_answer),
                ("human", "User question: \n\n {question} \n\n LLM generation: {generation}"),
            ]
        )
        answer_chain = answer_prompt | llm
        
        hallucination_score = hallucination_chain.invoke({"documents": documents, "generation": generation})
        print(f"DEBUG: Hallucination Score: {hallucination_score.content}")
        
        # Relaxed check for local models
        is_grounded = "yes" in hallucination_score.content.lower()
        
        if is_grounded:
            print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
            # Check answer relevance
            answer_score = answer_chain.invoke({"question": question, "generation": generation})
            print(f"DEBUG: Answer Relevance Score: {answer_score.content}")
            
            if "yes" in answer_score.content.lower():
                print("---DECISION: GENERATION ADDRESSES QUESTION---")
                return "useful"
            else:
                print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
                return "not useful"
        else:
            print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
            return "not supported"

    # --- Build Graph ---
    workflow = StateGraph(GraphState)

    # Define the nodes
    workflow.add_node("retrieve", retrieve) 
    workflow.add_node("grade_documents", grade_documents) 
    workflow.add_node("generate", generate) 
    workflow.add_node("transform_query", transform_query) 

    # Build the edges
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {
            "transform_query": "transform_query",
            "generate": "generate",
        },
    )
    workflow.add_edge("transform_query", "retrieve")
    
    workflow.add_conditional_edges(
        "generate",
        grade_generation_v_documents_and_question,
        {
            "not supported": "generate",
            "useful": END,
            "not useful": "transform_query", 
        },
    )

    return workflow.compile()
