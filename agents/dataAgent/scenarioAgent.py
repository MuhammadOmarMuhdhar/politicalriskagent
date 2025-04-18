import logging
import json
import time
from agents.base_model import GeminiModel

logger = logging.getLogger(__name__)

class agent:
    def __init__(self, api_key, model_name="gemini-2.0-flash"):
        """Initialize the scenario generator agent with API key and model."""
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
        
    def _build_scenario_prompt(self, user_data, risk_type, risk_definition):
        """Build prompt for generating scenarios based on user survey data."""
        return f"""
        You are a risk intelligence agent specializing in identifying political and business risks. Your role is to take a user's survey response and transform it into a set of three well-structured, context-specific questions that help assess potential risks, based on the selected risk category.

        Below is the information provided by the user:

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

        Your task is to generate **three targeted questions** that surface the most critical risks related to the specified risk category: **{risk_type}**.

        **Definition of this risk type**:  
        {risk_definition}

        The questions should:
        - Be tailored to the user's business profile and planned activity
        - Reflect a deep understanding of the risk category
        - Help uncover meaningful insights or vulnerabilities

        Please return your response in the following JSON format:
        {{
            "scenario": ["question1", "question2", "question3"]
        }}

        ---

        ### Example

        **User Information:**
        - **Industry Sector**: Renewable Energy  
        - **Headquarters Location**: Germany  
        - **Company Size**: Mid-sized  
        - **Business Maturity**: Growth stage  
        - **Business Model**: Manufacturing and Export  
        - **International Exposure**: High  
        - **Type of Business Activity**: Expansion of solar panel manufacturing  
        - **Target Country/Region**: Vietnam  
        - **Planned Timeline**: 18 months  
        - **Investment Size**: $30M  
        - **Strategic Importance**: High  
        - **Local Partnerships**: Joint venture planned  
        - **Primary Concerns**: Environmental regulations, foreign investment restrictions  
        - **Other Relevant Information**: Aims to benefit from local green energy incentives

        **Risk Type**: Regulatory Risk  
        **Definition**: Regulatory risk refers to the potential for losses or operational disruption due to changes in laws, policies, or enforcement practices in a specific jurisdiction.

        **Response**:
        {{
            "scenario": [
                "How might upcoming changes in Vietnam's environmental or energy regulations affect solar manufacturing operations?",
                "Are there any restrictions or approval processes for foreign joint ventures in the renewable energy sector?",
                "What is the risk of policy shifts that could reduce or eliminate green energy subsidies currently offered in Vietnam?"
            ]
        }}
        """
    
    def generate_scenarios(self, user_data, risk_type=None):
        """Generate scenarios for specific or all risk types based on user data."""
        results = {}
        
        # If risk_type is specified, only generate for that type
        if risk_type and risk_type in self.risk_types:
            try:
                logger.info(f"Generating scenario for: {risk_type}")
                prompt = self._build_scenario_prompt(user_data, risk_type, self.risk_types[risk_type])
                response = self.gemini.generate(prompt)
                results[risk_type] = response
            except Exception as e:
                logger.error(f"Error generating scenario for {risk_type}: {e}")
                results[risk_type] = {"scenario": []}
                self._handle_retry(e)
            return results
        
        # Generate for all risk types
        for risk_type, risk_definition in self.risk_types.items():
            try:
                logger.info(f"Generating scenario for: {risk_type}")
                prompt = self._build_scenario_prompt(user_data, risk_type, risk_definition)
                response = self.gemini.generate(prompt)
                results[risk_type] = response
            except Exception as e:
                logger.error(f"Error generating scenario for {risk_type}: {e}")
                results[risk_type] = {"scenario": []}
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

