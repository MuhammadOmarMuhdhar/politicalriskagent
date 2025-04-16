import logging
import json
from base_models import GeminiModel
from utils import clean_and_parse_json

logger = logging.getLogger(__name__)

class agent:
    def __init__(self, api_key, model_name="gemini-1.5-flash"):
        """Initialize the risk keyword generator with API key and model."""
        self.gemini = GeminiModel(api_key=api_key, model_name=model_name)
        self.gdelt_themes = self._load_gdelt_themes()
        self.risk_types = self._load_risk_types()
        
    def _load_gdelt_themes(self):
        """Load GDELT themes from the lookup file."""
        try:
            with open('data/gdeltthemes/LOOKUP-GKGTHEMES.TXT', 'r') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error loading GDELT themes: {e}")
            return ""
            
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
            You are a political risk analyst, currently interacting with a client.
            The client has just filled out a survey providing you with their business profile and planned activities in a specific country.
            Here is that information:

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
            - **Primary Concerns**: {", ".join(user_data['primary_concerns']) if user_data['primary_concerns'] else "None specified"}

            At this stage you are working to source data from GDELT.
            You will be using the GDELTdocs API to source this data.
            At this point you are working to identify the most relevant GDELT themes and key words in relation to 
            this particular case for this {risk_type} type of risk.

            This risk is defined as: {risk_definition}

            The GDELT themes are as follows:
            {self.gdelt_themes}

            Please provide a JSON output with the following structure:
            {{
                "relevant_themes": ["THEME1", "THEME2", "THEME3"],
                "keywords": ["keyword1", "keyword2", "keyword3"]
            }}
            """

    def generate_keywords_for_all_risks(self, user_data):
        """Generate keywords for all risk types based on user data."""
        results = {}
        
        for risk_type, risk_definition in self.risk_types.items():
            try:
                logger.info(f"Generating keywords for risk type: {risk_type}")
                prompt = self._build_prompt(user_data, risk_type, risk_definition)
                output = self.gemini.generate(prompt)
                parsed_output = clean_and_parse_json(output, fallback={
                    "relevant_themes": [],
                    "keywords": [],
                    "justification": f"Failed to parse output for {risk_type}"
                })
                results[risk_type] = parsed_output
            except Exception as e:
                logger.error(f"Error generating keywords for {risk_type}: {e}")
                results[risk_type] = {
                    "relevant_themes": [],
                    "keywords": [],
                    "justification": f"Error occurred: {str(e)}"
                }
        
        return results
        
    def generate_keywords_for_risk_type(self, user_data, risk_type):
        """Generate keywords for a specific risk type based on user data."""
        if risk_type not in self.risk_types:
            logger.error(f"Risk type '{risk_type}' not found in risk definitions")
            return None
            
        try:
            risk_definition = self.risk_types[risk_type]
            prompt = self._build_prompt(user_data, risk_type, risk_definition)
            output = self.gemini.generate(prompt)
            return clean_and_parse_json(output, fallback=None)
        except Exception as e:
            logger.error(f"Error generating keywords for {risk_type}: {e}")
            return None

# Example usage:
# generator = RiskKeywordGenerator(api_key="your_api_key")
# 
# # Generate keywords for all risk types
# all_results = generator.generate_keywords_for_all_risks(user_data)
# 
# # Or generate keywords for a specific risk type
# specific_result = generator.generate_keywords_for_risk_type(user_data, "political_instability")