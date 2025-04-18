import logging
from agents.dataAgent import scenarioAgent
from agents.dataAgent import keywordAgent
from agents.utils import clean_and_parse_json

logger = logging.getLogger(__name__)

class Orchestrator:
    """Orchestrator to manage the tandem operation of the two agents."""
    
    def __init__(self, api_key, model_name="gemini-2.0-flash"):
        """Initialize the orchestrator with both agents."""
        self.scenario_agent = scenarioAgent.agent(api_key=api_key, model_name=model_name)
        self.keyword_agent = keywordAgent.agent(api_key=api_key, model_name=model_name)
    
    def run(self, user_data, risk_type=None):
        """Run the full risk analysis process."""
        # Step 1: Generate scenarios from user survey data
        logger.info("Starting scenario generation")
        scenarios = self.scenario_agent.generate_scenarios(user_data, risk_type)
        # Clean scenarios
        scenarios_cleaned = clean_and_parse_json(scenarios, field_to_clean="scenario", fallback={})
        
        # Step 2: Generate keywords from scenarios
        logger.info("Starting keyword generation from scenarios")
        keywords = self.keyword_agent.generate_keywords(scenarios_cleaned, risk_type)
        # Clean keywords
        keywords_cleaned = clean_and_parse_json(keywords, field_to_clean="keywords", fallback={})
        
        # Combine results for easier consumption
        results = {}
        for risk in scenarios:
            results[risk] = {
                "scenario": scenarios_cleaned[risk]['scenario'],
                "keywords": keywords_cleaned[risk]['keywords']
            }
        
        return results
    
    

# Example usage:
if __name__ == "__main__":
    # Sample user data structure
    user_data = {
        "industry": "Technology",
        "location_business": "United States",
        "company_size": "Mid-sized",
        "business_maturity": "Growth stage",
        "business_model": "SaaS",
        "international_exposure": "Medium",
        "activity_type": "Market Expansion",
        "target_location": "Brazil",
        "timeline": "12 months",
        "investment_size": "$5M",
        "strategic_importance": "High",
        "local_partnerships": "Seeking",
        "primary_concerns": ["regulatory compliance", "market acceptance"],
        "other_relevant_info": "First expansion into South America"
    }
    
    # Create the orchestrator with your API key
    orchestrator = Orchestrator(api_key="your_api_key")
    
    # Run the analysis for all risk types
    # all_results = orchestrator.analyze_risks(user_data)
    
    # Or run the analysis for a specific risk type
    # specific_result = orchestrator.analyze_risks(user_data, "political_instability")