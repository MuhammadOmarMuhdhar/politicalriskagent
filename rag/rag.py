import os
from typing import List, Dict, Any, Optional, Union, Tuple

import numpy as np
from pymilvus import connections, Collection
from google import genai
from google.genai import types

from config import (
    MILVUS_URI,
    MILVUS_TOKEN,
    MILVUS_COLLECTION_NAME,
    GEMINI_EMBEDDING_MODEL,
    GEMINI_API_KEY
)


class VectorSearchEngine:
    """Manages vector search operations using Milvus and Gemini embeddings."""
    
    def __init__(
        self,
        collection_name: str = MILVUS_COLLECTION_NAME,
        uri: str = MILVUS_URI,
        token: str = MILVUS_TOKEN,
        embedding_model: str = GEMINI_EMBEDDING_MODEL,
        api_key: str = GEMINI_API_KEY
    ):
        """Initialize the search engine with connection parameters.
        
        Args:
            collection_name: Name of the Milvus collection to search
            uri: URI for the Milvus server
            token: Authentication token for Milvus
            embedding_model: Name of the Gemini embedding model
            api_key: API key for Gemini
        """
        self.collection_name = collection_name
        self.uri = uri
        self.token = token
        self.embedding_model = embedding_model
        self.gemini_client = genai.Client(api_key=api_key)
        self.collection = None
    
    def connect(self) -> Collection:
        """Establish connection to Milvus and load the collection.
        
        Returns:
            The loaded Milvus collection
        """
        try:
            connections.connect(
                alias="default",
                uri=self.uri,
                token=self.token
            )
            self.collection = Collection(self.collection_name)
            self.collection.load()
            return self.collection
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Milvus: {e}")
    
    def disconnect(self) -> None:
        """Disconnect from Milvus server."""
        try:
            connections.disconnect("default")
            self.collection = None
        except Exception as e:
            print(f"Warning: Error during disconnect: {e}")
    
    def generate_embedding(self, query_text: str) -> List[float]:
        """Generate an embedding vector for the query text.
        
        Args:
            query_text: The text to generate an embedding for
            
        Returns:
            List of embedding values
        """
        try:
            response = self.gemini_client.models.embed_content(
                model=self.embedding_model,
                contents={"parts": [{"text": query_text}]},
                config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
            )
            return response.embeddings[0].values
        except Exception as e:
            raise ValueError(f"Failed to generate embedding: {e}")
    
    def search(
        self, 
        query_text: str, 
        top_k: int = 5,
        output_fields: Optional[List[str]] = None,
        expression: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search the collection using semantic similarity.
        
        Args:
            query_text: Text query to search for
            top_k: Number of results to return
            output_fields: Fields to include in results
            expression: Optional filter expression
            
        Returns:
            List of search results with metadata
        """
        # Connect if not already connected
        if not self.collection:
            self.connect()
        
        # Default output fields if none provided
        if not output_fields:
            output_fields = ["text", "source_url", "date", "title"]
            
        # Generate embedding for query
        query_embedding = self.generate_embedding(query_text)
        
        # Define search parameters
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        # Execute search
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=expression,
            output_fields=output_fields
        )
        
        # Process and format results
        formatted_results = []
        for hits in results:
            for hit in hits:
                result = {"score": hit.score}
                # Add all available output fields
                for field in output_fields:
                    result[field] = hit.entity.get(field)
                formatted_results.append(result)
                
        return formatted_results
    
    def hybrid_search(
        self, 
        query_text: str, 
        top_k: int = 5,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining vector similarity and keyword matching.
        
        Args:
            query_text: Text query to search for
            top_k: Number of results to return
            vector_weight: Weight for vector similarity score (0-1)
            keyword_weight: Weight for keyword match score (0-1)
            
        Returns:
            List of search results with combined scores
        """
        # Get more results than needed for re-ranking
        vector_results = self.search(query_text, top_k=top_k*2)
        
        # Prepare query terms for keyword matching
        query_terms = set(query_text.lower().split())
        
        # Re-rank based on combined vector and keyword scores
        for result in vector_results:
            # Calculate keyword match score 
            doc_terms = set(result["text"].lower().split())
            keyword_match = len(query_terms.intersection(doc_terms)) / len(query_terms) if query_terms else 0
            
            # Store both scores for transparency
            result["vector_score"] = result["score"]
            result["keyword_score"] = keyword_match
            
            # Calculate combined score using weights
            result["combined_score"] = (vector_weight * result["score"]) + (keyword_weight * keyword_match)
        
        # Re-rank based on combined score
        vector_results.sort(key=lambda x: x["combined_score"], reverse=True)
        
        # Return top_k results
        return vector_results[:top_k]
    
    def filter_search(
        self,
        query_text: str,
        filters: Dict[str, Any],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search with metadata filters.
        
        Args:
            query_text: Text query to search for
            filters: Dictionary of field-value pairs to filter by
            top_k: Number of results to return
            
        Returns:
            List of filtered search results
        """
        # Build filter expression from filter dictionary
        expressions = []
        for field, value in filters.items():
            if isinstance(value, str):
                expressions.append(f'{field} == "{value}"')
            elif isinstance(value, (int, float)):
                expressions.append(f'{field} == {value}')
            elif isinstance(value, list):
                # Handle array contains operations
                values_str = ', '.join([f'"{v}"' if isinstance(v, str) else str(v) for v in value])
                expressions.append(f'{field} in [{values_str}]')
        
        # Combine expressions with AND operator
        expression = " && ".join(expressions) if expressions else None
        
        # Get output fields from filters plus the default text field
        output_fields = list(set(["text"] + list(filters.keys())))
        
        # Execute search with filter expression
        return self.search(
            query_text=query_text,
            top_k=top_k,
            output_fields=output_fields,
            expression=expression
        )


# example usage

# def main():
#     """Example usage of the vector search engine."""
#     # Create search engine instance
#     search_engine = VectorSearchEngine()
    
#     try:
#         # Basic semantic search
#         print("Performing basic vector search...")
#         results = search_engine.search("political instability in South America", top_k=3)
        
#         print("\nSearch Results:")
#         for i, result in enumerate(results):
#             print(f"\nResult {i+1} - Score: {result['score']:.4f}")
#             print(f"Title: {result.get('title', 'N/A')}")
#             print(f"Source: {result.get('source_url', 'N/A')}")
#             print(f"Date: {result.get('date', 'N/A')}")
#             print(f"Excerpt: {result.get('text', 'N/A')[:150]}...")
        
#         # Hybrid search example
#         print("\n\nPerforming hybrid search...")
#         hybrid_results = search_engine.hybrid_search(
#             "economic sanctions impact on civilian population", 
#             top_k=3
#         )
        
#         print("\nHybrid Search Results:")
#         for i, result in enumerate(hybrid_results):
#             print(f"\nResult {i+1}")
#             print(f"Combined Score: {result.get('combined_score', 0):.4f}")
#             print(f"Vector Score: {result.get('vector_score', 0):.4f}")
#             print(f"Keyword Score: {result.get('keyword_score', 0):.4f}")
#             print(f"Title: {result.get('title', 'N/A')}")
#             print(f"Excerpt: {result.get('text', 'N/A')[:150]}...")
            
#     finally:
#         # Ensure connection is closed
#         search_engine.disconnect()


# if __name__ == "__main__":
#     main()