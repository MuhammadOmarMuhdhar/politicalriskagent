import logging
from agents.utils.cleanJson import parse
import pandas as pd
from rag import embeddingsGenerator
from agents.analysisAgent import bigramAgent
from agents.analysisAgent import pulse

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    Orchestrates bigram generation and risk score calculation.
    """
    def __init__(self, api_key, model_name="gemini-2.0-flash", user_data=None, keywords=None, articles_dict=None):
        """
        Initialize the orchestrator with API key, model name, and user data.
        """
        self.api_key = api_key
        self.model_name = model_name
        self.user_data = user_data
        self.keywords = keywords  # Remove trailing comma
        self.bigram_agent = bigramAgent.agent(api_key=api_key)
        self.articles_dict = articles_dict  # This should be a dictionary of articles


    def run(self):
        """
        Run the full data extraction and feature engineering process.
        """
        # Step 1: Create bigrams
        logger.info("Generating bigrams")
        bigrams = self.bigram_agent.generate(user_data=self.user_data)

        # Step 2: Calculate risk scores
        logger.info("Calculating risk scores")
        risk_calculator = pulse.Calculator(bigrams)
        risk_scores = risk_calculator.calculate(self.articles_dict)

        return bigrams, risk_scores









