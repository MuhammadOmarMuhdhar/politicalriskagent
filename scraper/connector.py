import os
import sys
from typing import Optional
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from config import (
    MILVUS_URI, 
    MILVUS_TOKEN, 
    GEMINI_EMBEDDING_DIMENSION, 
    MILVUS_MAX_VARCHAR_LENGTH
)

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apisecrets.geminapi import api_key
from config import (
    MILVUS_URI, 
    MILVUS_TOKEN, 
    GEMINI_EMBEDDING_DIMENSION, 
    MILVUS_COLLECTION_NAME,
    MILVUS_MAX_VARCHAR_LENGTH,
    GKG_URL_FETCH_LIMIT
)


class MilvusConnector:
    """Handles connections and operations with Milvus vector database."""
    
    @staticmethod
    def connect() -> bool:
        """Establish connection to Milvus database.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            connections.connect(alias="default", uri=MILVUS_URI, token=MILVUS_TOKEN)
            print(f"Connected to Milvus: {MILVUS_URI}")
            return True
        except Exception as e:
            print(f"Error connecting to Milvus: {e}")
            return False

    @staticmethod
    def create_or_load_collection(collection_name: str) -> Optional[Collection]:
        """Create a new collection if it doesn't exist, or load an existing one.
        
        Args:
            collection_name: Name of the collection to create or load
            
        Returns:
            Collection object or None if operation fails
        """
        try:
            if not utility.has_collection(collection_name):
                print(f"Collection '{collection_name}' not found. Creating...")
                
                # Define schema fields
                fields = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
                    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=MILVUS_MAX_VARCHAR_LENGTH),
                    FieldSchema(name="source_url", dtype=DataType.VARCHAR, max_length=1024),
                    FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=1024),
                    FieldSchema(name="date", dtype=DataType.VARCHAR, max_length=8),
                    FieldSchema(name="gdelt_id", dtype=DataType.VARCHAR, max_length=100),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=GEMINI_EMBEDDING_DIMENSION)
                ]
                
                # Create collection with schema
                schema = CollectionSchema(
                    fields=fields, 
                    description="Chunks from GDELT political risk articles"
                )
                collection = Collection(name=collection_name, schema=schema)
                
                # Create vector index
                print("Creating index on 'embedding' field...")
                index_params = {
                    "metric_type": "COSINE", 
                    "index_type": "AUTOINDEX", 
                    "params": {}
                }
                collection.create_index(field_name="embedding", index_params=index_params)
                
            else:
                print(f"Collection '{collection_name}' already exists. Loading...")
                collection = Collection(collection_name)
                
            # Load collection into memory
            collection.load()
            print(f"Collection '{collection_name}' loaded.")
            return collection
            
        except Exception as e:
            print(f"Error creating/loading collection: {e}")
            return None


