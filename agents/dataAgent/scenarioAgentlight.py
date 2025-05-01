import logging
import json
import time
from agents.base_model import GeminiModel
from agents.prompts import header
from collections import defaultdict

logger = logging.getLogger(__name__)

class agent:
    def __init__(self, api_key, model_name="gemini-2.0-flash"):
        """Initialize the scenario generator agent with API key and model."""
        self.gemini = GeminiModel(api_key=api_key, model_name=model_name)
        self.risk_types = self._load_risk_types()

    def _load_risk_types(self):
        """Load risk types from the JSON file."""
        try:
            with open('data/LLMcontext/risks.json', 'r') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error loading risk types: {e}")
            return {}
        
        
    def _build_scenario_prompt(self, user_data, risk_type):
        """Build prompt for generating scenarios based on user survey data."""

        heading = header.prompt_header(user_data=user_data)
        
        prompt = f"""
        
        {heading}

        Your task is to generate **one targeted scenari** that surface the most critical risks related to the specified risk category: **{risk_type}** .

        The questions should:
        - Be tailored to the user's business profile and planned activity
        - Reflect a deep understanding of the risk category
        - Help uncover meaningful insights or vulnerabilities

        Please return your response in the following JSON format:
        {{
            "scenario": ["question1", "question2", "question3"]
        }}

        """
        return prompt
    
    def generate(self, user_data, risk_type=None):
        """Generate scenarios for specific or all risk types based on user data."""
        results = defaultdict(lambda: defaultdict(dict))        
        
        # Generate for all risk types
        for broad_risk, item in self.risk_types.items(): 
            for specific_risk, sub_item in item.items():
                try:
                    prompt = self._build_scenario_prompt(user_data, specific_risk)
                    response = self.gemini.generate(prompt)
                    results[broad_risk][specific_risk] = response
                    keywords_list = sub_item['keywords']

                except Exception as e:
                    logger.error(f"Error generating scenario for {specific_risk}: {e}")
                    results[broad_risk][specific_risk][specific_risk] = {"scenario": []}
                    self._handle_retry(e)

        return results
    
    def _handle_retry(self, exception):
        """Handle retries with appropriate delay."""
        retry_delay = getattr(exception, 'retry_delay', None)
        if retry_delay:
            logger.info(f"Retrying after {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            logger.info("Retrying after default delay...")
            time.sleep(10)
