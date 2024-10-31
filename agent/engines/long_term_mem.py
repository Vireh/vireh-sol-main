from typing import List, Dict
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from openai import OpenAI

Base = declarative_base()

class LongTermMemory(Base):
    __tablename__ = "long_term_memories"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    embedding = Column(String, nullable=False)  # Store as JSON string
    significance_score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

def create_embedding(text: str, openai_api_key: str) -> List[float]:
    client = OpenAI(api_key=openai_api_key)
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def store_memory(db: Session, content: str, embedding: List[float], significance_score: float):
    new_memory = LongTermMemory(
        content=content,
        embedding=str(embedding),  # Convert to string for storage.
        significance_score=significance_score
    )
    db.add(new_memory)
    db.commit()

def format_long_term_memories(memories: List[Dict[str, Any]]) -> str:
    if not memories:
        return "No relevant memories found."

    # Sort memories by significance score for better organization.
    sorted_memories = sorted(memories, key=lambda x: x.get('significance_score', 0), reverse=True)

    formatted_parts = ["Past memories and thoughts:"]
    
    for memory in sorted_memories:
        content = memory.get('content', '').strip()
        if content:
            formatted_parts.append(f"- {content}")

    return "\n".join(formatted_parts)

def retrieve_relevant_memories(db: Session, query_embedding: List[float], top_k: int = 5) -> str:
    all_memories = db.query(LongTermMemory).all()

    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate the cosine similarity between two vectors."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    similarities = [
        (memory, cosine_similarity(query_embedding, eval(memory.embedding)))
        for memory in all_memories
    ]

    # Sort memories based on similarity and get the top_k
    sorted_memories = sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]

    # Prepare the list of memories for formatting
    memories_list = [
        {"content": memory.content, "significance_score": memory.significance_score}
        for memory, _ in sorted_memories
    ]

    return format_long_term_memories(memories_list)
