import uuid
import time
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from pymilvus import Collection
from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
from google import generativeai as genai
from config import (
    GEMINI_EMBEDDING_MODEL,
    MILVUS_MAX_VARCHAR_LENGTH,
)


class DocumentProcessor:
    """Processes documents: extracts, chunks, embeds, and stores content."""
    
    def __init__(self, collection: Collection):
        """Initialize with a Milvus collection."""
        self.collection = collection
        self.converter = DocumentConverter()
        self.chunker = HybridChunker(max_tokens=512, merge_peers=True)
        
    def parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to YYYYMMDD format.
        
        Args:
            date_str: Date string in ISO format
            
        Returns:
            Date in YYYYMMDD format or None if parsing fails
        """
        if not date_str:
            return None
            
        try:
            dt_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt_obj.strftime('%Y%m%d')
        except ValueError:
            print(f"Warning: Could not parse date '{date_str}'")
            return None
    
    def fetch_and_convert_document(self, url: str) -> Tuple[Optional[Any], Optional[str]]:
        """Fetch and convert document from URL using Docling.
        
        Args:
            url: URL of the document to fetch
            
        Returns:
            Tuple of (document object, extracted title)
        """
        try:
            print(f"    Fetching and converting document from URL...")
            result = self.converter.convert(source=url)
            document = result.document
            print(f"    Document conversion successful")
            
            # Extract title if available
            title = None
            if hasattr(document, 'meta') and hasattr(document.meta, 'title'):
                title = document.meta.title
                
            return document, title
        except Exception as e:
            print(f"Error fetching/converting document from {url}: {e}")
            return None, None
    
    def chunk_document(self, document) -> List[Any]:
        """Split document into chunks using Docling chunker.
        
        Args:
            document: Docling document object
            
        Returns:
            List of chunk objects
        """
        try:
            chunks = list(self.chunker.chunk(dl_doc=document))
            print(f"Generated {len(chunks)} chunks")
            return chunks
        except Exception as e:
            print(f"Error chunking document: {e}")
            return []
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using Gemini API.
        
        Args:
            text: Text to embed
            
        Returns:
            Vector embedding or None if generation fails
        """
        try:
            response = genai.embed_content(
                model=GEMINI_EMBEDDING_MODEL,
                content=text,
                task_type="retrieval_document"
            )
            return response['embedding']
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def insert_chunks_batch(self, batch_data: List[List]) -> int:
        """Insert a batch of chunks into Milvus.
        
        Args:
            batch_data: List of data columns to insert
            
        Returns:
            Number of successful insertions
        """
        if not batch_data or not batch_data[0]:
            return 0
            
        try:
            insert_result = self.collection.insert(batch_data)
            successful_count = len(insert_result.primary_keys)
            print(f"    Batch of {successful_count} chunks inserted successfully")
            self.collection.flush()
            return successful_count
        except Exception as e:
            print(f"    Error inserting batch: {e}")
            return 0
    
    def process_article(self, article_meta: Dict[str, Any]) -> int:
        """Process an article from metadata: extract, chunk, embed, and store.
        
        Args:
            article_meta: Dictionary containing article metadata with 'url',
                         'title', and 'seendate' keys
                         
        Returns:
            Number of chunks successfully inserted
        """
        # Extract required fields from metadata
        source_url = article_meta.get('url')
        api_title = article_meta.get('title', 'Untitled Article')
        date_yyyymmdd = self.parse_date(article_meta.get('seendate'))
        
        if not source_url:
            print("Error: No URL found in article metadata. Skipping.")
            return 0
        
        print(f"\n--- Processing Article: {api_title} ---")
        print(f"URL: {source_url}")
        print(f"Date: {date_yyyymmdd or 'Unknown'}")
        
        # Fetch and convert document
        document, docling_title = self.fetch_and_convert_document(source_url)
        if not document:
            return 0
        
        # Use docling title if available, otherwise use API title
        final_title = docling_title or api_title
        
        # Chunk the document
        chunks = self.chunk_document(document)
        if not chunks:
            return 0
        
        # Create unique base ID for this article
        article_base_id = f"api_{uuid.uuid5(uuid.NAMESPACE_URL, source_url)}"
        gdelt_id_placeholder = f"api_src_{date_yyyymmdd or 'nodate'}"
        
        # Process chunks in batches
        insert_batch_size = 50
        successful_inserts = 0
        batch_data = [[] for _ in range(7)]  # 7 columns in schema
        
        for i, chunk in enumerate(chunks):
            try:
                # Extract text from chunk
                chunk_text = getattr(chunk, 'text', str(chunk))
                if not chunk_text or not chunk_text.strip():
                    continue
                
                print(f"  Processing chunk {i+1}/{len(chunks)} ({len(chunk_text)} chars)")
                
                # Truncate if text exceeds max length
                if len(chunk_text) >= MILVUS_MAX_VARCHAR_LENGTH:
                    chunk_text = chunk_text[:MILVUS_MAX_VARCHAR_LENGTH - 20] + "... (truncated)"
                
                # Generate embedding
                embedding = self.generate_embedding(chunk_text)
                if not embedding:
                    continue
                
                # Create unique ID for this chunk
                chunk_id = f"{article_base_id}_chunk_{i}"
                
                # Add data to batch
                batch_data[0].append(chunk_id)
                batch_data[1].append(chunk_text)
                batch_data[2].append(source_url[:1024])
                batch_data[3].append(final_title[:1024])
                batch_data[4].append(date_yyyymmdd or "")
                batch_data[5].append(gdelt_id_placeholder)
                batch_data[6].append(embedding)
                
                # Insert batch if it reaches the size limit
                if len(batch_data[0]) >= insert_batch_size:
                    successful_inserts += self.insert_chunks_batch(batch_data)
                    batch_data = [[] for _ in range(7)]
                
                # Throttle to avoid API rate limits
                time.sleep(0.8)
                
            except Exception as e:
                print(f"  Error processing chunk {i+1}: {e}")
                continue
        
        # Insert remaining chunks
        if batch_data[0]:
            successful_inserts += self.insert_chunks_batch(batch_data)
        
        print(f"--- Finished Article: {successful_inserts}/{len(chunks)} chunks inserted ---")
        return successful_inserts
