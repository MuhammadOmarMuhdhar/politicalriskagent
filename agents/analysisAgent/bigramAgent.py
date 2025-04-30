import logging
import json
import time
import numpy as np
from agents.base_model import GeminiModel
from agents.prompts import header
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class agent:
    def __init__(self, api_key, model_name="gemini-2.0-flash", embedding_model_name="all-MiniLM-L6-v2"):
        """Initialize the political risk agent with API key and models."""
        self.gemini = GeminiModel(api_key=api_key, model_name=model_name)
        self.risk_types = self._load_risk_types()
        # Load embedding model once at initialization
        self.embedding_model = SentenceTransformer(embedding_model_name)
        
    def _load_risk_types(self):
        """Load risk types from the JSON file."""
        try:
            with open('data/LLMcontext/risks.json', 'r') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error loading risk types: {e}")
            return {}
    
    def _build_bigram_prompt(self, risk_category, risk_subcategory, keyword, user_data):
        """Build prompt for generating political risk bigrams."""
        heading = header.prompt_header(user_data=user_data)
        prompt = f"""
                {heading}

                TASK: Generate investment-relevant political risk bigrams

                CONTEXT:
                - Risk Category: '{risk_category}'
                - Risk Subcategory: '{risk_subcategory}'
                - Focus Keyword: '{keyword}'
                - Client Investment Context: See header information

                INSTRUCTIONS:
                Generate 30 two-word combinations (bigrams) that would frequently appear in political discussions 
                related to the specified risk parameters. These bigrams should:

                1. Strongly indicate political discourse about this specific risk
                2. Be directly relevant to the client's investment context and sector
                3. Typically appear in news articles, policy documents, or political statements
                4. Function effectively as signals when found near other risk-related terms

                For each bigram, assign an importance weight (50-200) reflecting how strongly it indicates 
                discussion of this political risk (higher = stronger indicator).

                OUTPUT FORMAT:
                Return only a valid JSON object with this exact structure:
                {{
                "bigrams": [
                    {{"bigram": "example_term", "weight": 150}},
                    {{"bigram": "another_example", "weight": 120}},
                    ...
                ]
                }}
        """
        return prompt
    
    def generate_embeddings(self, texts):
        """Generate embeddings for a list of texts using the loaded model."""
        # Use the pre-loaded model to generate embeddings in batches
        return self.embedding_model.encode(texts, batch_size=64, show_progress_bar=False)
    
    def generate(self, user_data, retries=2, wait_time=3):
        """Generate political risk bigrams with flat structure and batch embedding."""
        # Flat structure to store all bigrams with metadata
        all_bigram_data = []
        
        # Dictionary to collect all unique bigrams before embedding
        unique_bigrams = set()
        bigram_metadata = {}
        
        # First pass: collect all unique bigrams and their metadata
        for broad_risk, subcategories in self.risk_types.items():
            for specific_risk, details in subcategories.items():
                for keyword in details.get('keywords', []):
                    logger.info(f"Generating bigrams for {broad_risk}/{specific_risk}/{keyword}")
                    
                    attempts = 0
                    success = False
                    
                    while attempts <= retries and not success:
                        try:
                            prompt = self._build_bigram_prompt(broad_risk, specific_risk, keyword, user_data)
                            response = self.gemini.generate(prompt)
                            
                            try:
                                # Parse JSON response
                                bigram_data = json.loads(response)
                            except json.JSONDecodeError:
                                # Extract JSON if parsing fails
                                start_idx = response.find('{')
                                end_idx = response.rfind('}') + 1
                                if start_idx >= 0 and end_idx > start_idx:
                                    json_str = response[start_idx:end_idx]
                                    bigram_data = json.loads(json_str)
                                else:
                                    raise ValueError("Could not extract valid JSON from response")
                            
                            # Process each bigram
                            for item in bigram_data.get("bigrams", []):
                                bigram = item["bigram"]
                                weight = item["weight"]
                                
                                # Add to set of unique bigrams
                                unique_bigrams.add(bigram)
                                
                                # Store metadata for this bigram
                                if bigram not in bigram_metadata:
                                    bigram_metadata[bigram] = []
                                
                                bigram_metadata[bigram].append({
                                    "weight": weight,
                                    "category": broad_risk,
                                    "subcategory": specific_risk,
                                    "keyword": keyword
                                })
                            
                            success = True
                            
                        except Exception as e:
                            attempts += 1
                            logger.warning(f"Attempt {attempts} failed for {keyword}: {e}")
                            
                            if attempts <= retries:
                                time.sleep(wait_time)
                            else:
                                logger.error(f"Failed to generate bigrams for {keyword} after {retries} retries")
        
        # Second pass: batch generate embeddings for all unique bigrams
        if unique_bigrams:
            logger.info(f"Generating embeddings for {len(unique_bigrams)} unique bigrams in one batch")
            
            # Convert set to list for indexing
            bigram_list = list(unique_bigrams)
            
            try:
                # Generate embeddings in one batch operation
                embeddings = self.generate_embeddings(bigram_list)
                
                # Create the final flat structure with all information
                for i, bigram in enumerate(bigram_list):
                    for metadata in bigram_metadata[bigram]:
                        all_bigram_data.append({
                            "bigram": bigram,
                            "embedding": embeddings[i].tolist(),  # Convert numpy array to list for JSON serialization
                            "weight": metadata["weight"],
                            "category": metadata["category"],
                            "subcategory": metadata["subcategory"],
                            "keyword": metadata["keyword"]
                        })
                
            except Exception as e:
                logger.error(f"Error generating batch embeddings: {e}")
        
        return all_bigram_data