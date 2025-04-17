import os
import sys
from datetime import datetime
from typing import List, Dict, Optional, Any, Set, Tuple
from urllib.parse import urlparse, quote

import pandas as pd
from gdeltdoc import GdeltDoc, Filters, near
from pymilvus import connections

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our refactored classes
from scraper import connector, processor
from config import (
    MILVUS_URI,
    MILVUS_TOKEN,
    MILVUS_COLLECTION_NAME,
    GEMINI_EMBEDDING_DIMENSION,
    MILVUS_MAX_VARCHAR_LENGTH,
    GKG_URL_FETCH_LIMIT
)

connector = connector.MilvusConnector
processorfunction = processor.DocumentProcessor


class GdeltQueryProcessor:
    """Handles querying GDELT API and processing results through the document pipeline."""
    
    def __init__(self, collection_name: str = MILVUS_COLLECTION_NAME):
        """Initialize with collection name for storing results.
        
        Args:
            collection_name: Name of the Milvus collection to use
        """
        self.collection_name = collection_name
        self.gdelt_client = GdeltDoc()
        
    def process_query(
        self,
        risk_keywords: List[str],
        target_country_code: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        domain_filter: Optional[List[str]] = None,
        language: str = "eng",
        near_params: Optional[Tuple] = None,
        process_limit: int = 25
    ) -> int:
        """Process a GDELT query and store results in Milvus.
        
        Args:
            risk_keywords: List of keywords for the GDELT search
            target_country_code: Optional country code to filter articles
            start_date: Optional start date for article search
            end_date: Optional end date for article search
            domain_filter: Optional list of domains to include
            language: Language code (default: "eng" for English)
            near_params: Optional tuple of (distance, keyword1, keyword2, ...)
                         for proximity search
            process_limit: Maximum number of articles to process
            
        Returns:
            Total number of chunks successfully processed and stored
        """
        if not risk_keywords:
            print("Error: Risk keywords are required for GDELT query")
            return 0

        # Log query parameters
        self._log_query_parameters(
            risk_keywords, target_country_code, start_date, end_date,
            domain_filter, language, near_params, process_limit
        )
        
        # Fetch articles from GDELT
        articles_df = self._fetch_articles(
            risk_keywords, target_country_code, start_date, end_date,
            domain_filter, language, near_params
        )
        
        if articles_df.empty:
            print("No articles retrieved from GDELT based on the filters")
            return 0
            
        print(f"Retrieved {len(articles_df)} articles from GDELT")
        
        # Apply processing limit
        articles_to_process = articles_df.head(process_limit).to_dict('records')
        print(f"Processing up to {len(articles_to_process)} articles (limit: {process_limit})")
        
        # Process articles
        total_chunks = self._process_articles(articles_to_process)
        
        # Summarize results
        self._log_processing_summary(len(articles_df), len(articles_to_process), total_chunks)
        
        return total_chunks
        
    def _log_query_parameters(
        self, 
        risk_keywords: List[str],
        target_country_code: Optional[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        domain_filter: Optional[List[str]],
        language: str,
        near_params: Optional[Tuple],
        process_limit: int
    ) -> None:
        """Log the query parameters for debugging and monitoring."""
        print(f"\n===== Processing GDELT Query =====")
        print(f"Risk Keywords: {risk_keywords}")
        print(f"Target Country Code: {target_country_code or 'None'}")
        print(f"Start Date: {start_date.strftime('%Y-%m-%d') if start_date else 'None'}")
        print(f"End Date: {end_date.strftime('%Y-%m-%d') if end_date else 'None'}")
        print(f"Domain Filter: {domain_filter if domain_filter else 'All'}")
        print(f"Language: {language}")
        print(f"Near Parameters: {near_params if near_params else 'None'}")
        print(f"Processing Limit: {process_limit}")
        print(f"================================")
        
    def _fetch_articles(
        self,
        risk_keywords: List[str],
        target_country_code: Optional[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        domain_filter: Optional[List[str]],
        language: str,
        near_params: Optional[Tuple]
    ) -> pd.DataFrame:
        """Fetch articles from GDELT based on filters.
        
        Returns:
            DataFrame containing article metadata
        """
        # Create GDELT filters
        filters = Filters(
            start_date=start_date.strftime('%Y-%m-%d') if start_date else None,
            end_date=end_date.strftime('%Y-%m-%d') if end_date else None,
            num_records=250,  # Fixed at 250 as per requirements
            keyword=risk_keywords,
            domain=domain_filter,
            country=target_country_code,
            language=language,
            near=near(*near_params) if near_params else None
        )
        
        print("Querying GDELT API...")
        try:
            return self.gdelt_client.article_search(filters)
        except Exception as e:
            print(f"Error querying GDELT: {e}")
            return pd.DataFrame()  # Return empty DataFrame on error
            
    def _process_articles(self, articles: List[Dict[str, Any]]) -> int:
        """Process articles through the document pipeline.
        
        Args:
            articles: List of article metadata dictionaries
            
        Returns:
            Total number of chunks processed
        """
        # Connect to Milvus
        if not connector.connect():
            print("Failed to connect to Milvus. Aborting.")
            return 0
            
        try:
            # Create or load collection
            collection = connector.create_or_load_collection(self.collection_name)
            if not collection:
                print("Failed to create/load Milvus collection")
                return 0
                
            # Create document processor
            processor = processorfunction(collection)
            
            # Process each article
            total_chunks_processed = 0
            for i, article_meta in enumerate(articles):
                print(f"\n>>> Processing article {i+1}/{len(articles)}")
                try:
                    chunks_inserted = processor.process_article(article_meta)
                    total_chunks_processed += chunks_inserted
                    print(f"Processed {chunks_inserted} chunks for article {i+1}")
                except Exception as e:
                    print(f"Error processing article {i+1} ({article_meta.get('url', 'unknown')}): {e}")
                    
            return total_chunks_processed
            
        except Exception as e:
            print(f"Error in processing pipeline: {e}")
            return 0
        finally:
            # Ensure connection is closed
            connections.disconnect("default")
            print("Disconnected from Milvus")
            
    def _log_processing_summary(
        self, 
        total_retrieved: int, 
        total_processed: int, 
        total_chunks: int
    ) -> None:
        """Log processing summary statistics."""
        print(f"\n===== Processing Summary =====")
        print(f"Articles retrieved from GDELT: {total_retrieved}")
        print(f"Articles processed (limit applied): {total_processed}")
        print(f"Total chunks successfully inserted: {total_chunks}")
        print(f"==============================")
        


# Example usage of the GDELT query processor 

# def main():
#     # Example query parameters
#     risk_keywords = ["political instability", "civil unrest"]
    
#     # Create processor and run query
#     processor = GdeltQueryProcessor()
#     total_chunks = processor.process_query(
#         risk_keywords=risk_keywords,
#         target_country_code="US",
#         start_date=datetime(2025, 3, 1),
#         end_date=datetime(2025, 4, 15),
#         process_limit=10
#     )
    
#     print(f"Finished processing with {total_chunks} total chunks")
    

# if __name__ == "__main__":
#     main()