import logging
import json
from agents.base_models import GeminiModel
import time

logger = logging.getLogger(__name__)

class agent:
    def __init__(self, api_key, model_name="gemini-2.0-flash"):
        """Initialize the risk keyword generator with API key and model."""
        self.gemini = GeminiModel(api_key=api_key, model_name=model_name)
        self.risk_types = self._load_risk_types()
            
    def _load_risk_types(self):
        """Load risk types from the JSON file."""
        try:
            with open('data/risktypes/risks.json', 'r') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error loading risk types: {e}")
            return {}
    
    def _build_prompt(self, user_data, risk_type, risk_definition):
        """Build prompt for the AI model based on user data and risk type."""
        return f"""
        You are a political risk analyst currently advising a client. The client has completed a survey outlining their business profile and planned activities in a specific country. Below is the information they provided:

        ### Business Profile
        - **Industry Sector**: {user_data['industry']}
        - **Headquarters Location**: {user_data['location_business']}
        - **Company Size**: {user_data['company_size']}
        - **Business Maturity**: {user_data['business_maturity']}
        - **Business Model**: {user_data['business_model']}
        - **International Exposure**: {user_data['international_exposure']}

        ### Planned Activity
        - **Type of Business Activity**: {user_data['activity_type']}
        - **Target Country/Region**: {user_data['target_location']}
        - **Planned Timeline**: {user_data['timeline']}
        - **Investment Size**: {user_data['investment_size']}
        - **Strategic Importance**: {user_data['strategic_importance']}
        - **Local Partnerships**: {user_data['local_partnerships']}
        - **Primary Concerns**: {", ".join(user_data['primary_concerns']) if user_data['primary_concerns'] else "None specified"}
        - **Other Relevant Information**: {user_data['other_relevant_info']}

       
        Your current task is to assess potential **{risk_type}** risk for this client, as defined below:

        **{risk_definition}**

        You will be using the GDELTdocs API to identify:
        1. that you generate based on the client's context and the nature of the risk. These keywords should guide data sourcing and highlight specific concerns, actors, or indicators relevant to the scenario.


        Please respond in the following JSON format:
        {{
            "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
        }}

        ### Here is an example of how you would respond to the client: 

        For a client in the agriculture sector, the following information was provided:

        - **Industry Sector**: Agriculture
        - **Headquarters Location**: United States
        - **Company Size**: Medium
        - **Business Maturity**: Established
        - **Business Model**: B2B
        - **International Exposure**: High
        - **Type of Business Activity**: Investment
        - **Target Country/Region**: Russia
        - **Planned Timeline**: Short-term
        - **Investment Size**: Medium
        - **Strategic Importance**: High
        - **Local Partnerships**: Yes
        - **Primary Concerns**: None
        - **Other Relevant Information**: None
        
        You would provide the following response:
        
        ### Response
        {{"keywords": ["Tariffs", "Sanctions", "Trade Agreements", "Political Stability", "Regulatory Changes"]}}


        """


    def generate_keywords_for_all_risks(self, user_data):
        """Generate keywords for all risk types based on user data."""
        results = {}
        
        for risk_type, risk_definition in self.risk_types.items():
            try:
                logger.info(f"Generating keywords for risk type: {risk_type}")
                prompt = self._build_prompt(user_data, risk_type, risk_definition)
                output = self.gemini.generate(prompt)
                
                results[risk_type] = output

            except Exception as e:
                logger.error(f"Error generating keywords for {risk_type}: {e}")
                results[risk_type] = {
                    "relevant_themes": [],
                    "keywords": []
                }

                retry_delay = getattr(e, 'retry_delay', None)
                if retry_delay:
                    logger.info(f"Retrying after {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.info("Retrying after default delay...")
                    time.sleep(10)
        
        return results

# Example usage:
# generator = agent(api_key="your_api_key")
# 
# # Generate keywords for all risk types
# all_results = generator.generate_keywords_for_all_risks(user_data)
# 
# # Or generate keywords for a specific risk type
# specific_result = generator.generate_keywords_for_risk_type(user_data, "political_instability")