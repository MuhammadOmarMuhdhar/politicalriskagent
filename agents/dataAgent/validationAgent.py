import logging
import json
from typing import List, Dict, Any
from agents.base_model import GeminiModel
from agents.prompts import header
from collections import defaultdict

logger = logging.getLogger(__name__)

class agent:
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        """
        Initialize the validator agent with API key and model.
        """
        self.gemini = GeminiModel(api_key=api_key, model_name=model_name)
        
    def _build_prompt(self, user_data: Dict[str, Any], titles: List[str]) -> str:
        """
        Build prompt for evaluating the relevance of news articles.
        """
        # Format the header with user data
        heading = header.prompt_header(user_data=user_data)
        
        return f"""
            {heading}

            TASK: Evaluate the relevance of news articles for political risk analysis.

            INSTRUCTIONS:
            You are evaluating whether the following articles from GDELT API contain relevant political risk signals. For each article title:
            1. Identify if it relates to political developments, policy changes, or geopolitical events 
            2. Determine if it contains early warning signals for emerging political risks
            3. Assess if it mentions political actors, institutions, or movements 
            4. Evaluate if it describes political trends 

            ARTICLES TO EVALUATE:
            {titles}
        
            Please respond in the following JSON format with no additional text:

            Please return your response in the following JSON format:
            {{
                "relevant": ["article title 1", "article title 2", "article title 3"],
            }}

            """
    
    def validate(self, user_data: Dict[str, Any], articles_dict) -> Dict[str, Any]:
        """
        Validate articles relevancy.
        """
        try:
            # Validate input
            if not isinstance(articles_dict, dict):
                raise ValueError("articles_dict must be a dictionary")
            
            if not articles_dict:
                raise ValueError("articles_dict list cannot be empty")
            
            # Process all titles at once
            results = defaultdict(lambda: defaultdict(dict))

            for broad_risk, item in articles_dict.items():
                for specific_risk, sub_item in item.items():
                    for keyword, data_frame in sub_item.items():
                        titles = data_frame['title'].tolist()
                        # Generate prompt for all titles
                        prompt = self._build_prompt(user_data=user_data, titles=titles)
                        # Call Gemini API
                        response = self.gemini.generate(prompt)
                        # Add response to results dictionary
                        results[broad_risk][specific_risk][keyword] = response
            
            return results
            
        except Exception as e:
            logger.error(f"Error validating articles: {e}")
            raise e