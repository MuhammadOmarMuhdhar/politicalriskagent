import logging
import json
import time
from agents.base_model import GeminiModel
from agents.prompts import header

logger = logging.getLogger(__name__)

class agent:
    def __init__(self, api_key, model_name="gemini-2.0-flash"):
        """Initialize the keyword generator agent with API key and model."""
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
    
    def _build_keyword_prompt(self, user_data, risk_type, risk_definition, scenario):
        """Build prompt for generating keywords based on scenarios."""
        # Join the scenario questions into a coherent text
        scenario_text = " ".join(scenario)

        # Format the header with user data
        heading = header.prompt_header(user_data=user_data)
        
        return f"""

        {heading}

        You are now analyzing the client's scenario to extract key political or business risk indicators. Your goal is to distill the scenario into actionable insight by identifying core risk-related keywords.

        ### Client Scenario  
        {scenario_text}

        This scenario falls under the following risk category: **{risk_type}**

        **Definition of Risk Type:**  
        {risk_definition}

        ---

        **Your Task:**  
        Generate **five targeted keywords** that capture the most relevant risk-related factors in this scenario. Each keyword should:

        - Be **highly specific** to the client's context  
        - Be **strictly 1–2 words** in length  
        - Be useful for querying structured sources like the **GDELTdocs API**  
        - Focus on **key actors, triggers, or indicators** — such as policies, sectors, institutions, or events

        Please respond in the following JSON format:
        {{
            "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
        }}

        ---

        ### Example

        **Scenario**:  
        The client, a mid-sized renewable energy company headquartered in Germany, is planning to expand its solar panel manufacturing operations into Southeast Asia, specifically Vietnam. The company intends to form a joint venture with a local partner and begin operations within 18 months. The investment is considered strategic, with the goal of capturing emerging green energy markets in the region. However, the client is concerned about changing environmental regulations, import/export restrictions, and government subsidies for local competitors.

        **Risk Type**: Regulatory Risk  
        **Definition**: Regulatory risk refers to the potential impact of changes in laws, regulations, or policies that could adversely affect a business's operations or profitability.

        **Response**:
        {{
            "keywords": [
                "environmental policy",
                "import tariffs",
                "joint ventures",
                "energy subsidies",
                "regulatory shifts"
            ]
        }}
        """

    def generate_keywords(self, user_data, scenarios, risk_type=None):
        """Generate keywords based on scenarios for specific or all risk types."""
        results = {}
        
        # If risk_type is specified, only generate for that type
        if risk_type and risk_type in self.risk_types and risk_type in scenarios:
            try:
                scenario_data = scenarios[risk_type]['scenario']
                if not scenario_data:
                    logger.warning(f"No scenario data found for {risk_type}")
                    return {risk_type: {"keywords": []}}
                
                logger.info(f"Generating keywords for: {risk_type}")
                prompt = self._build_keyword_prompt(user_data=user_data, 
                                                    risk_type=risk_type, 
                                                    risk_definition=self.risk_types[risk_type], 
                                                    scenario=scenario_data)
                response = self.gemini.generate(prompt)
                results[risk_type] = response
            except Exception as e:
                logger.error(f"Error generating keywords for {risk_type}: {e}")
                results[risk_type] = {"keywords": []}
                self._handle_retry(e)
            return results
        
        # Generate for all risk types with available scenarios
        for risk_type, risk_definition in self.risk_types.items():
            if risk_type not in scenarios:
                logger.warning(f"No scenario data found for {risk_type}")
                results[risk_type] = {"keywords": []}
                continue
                
            scenario_data = scenarios[risk_type]
            if not scenario_data:
                logger.warning(f"Empty scenario data for {risk_type}")
                results[risk_type] = {"keywords": []}
                continue
                
            try:
                logger.info(f"Generating keywords for: {risk_type}")
                prompt = self._build_keyword_prompt(user_data=user_data, 
                                                    risk_type=risk_type, 
                                                    risk_definition=self.risk_types[risk_type], 
                                                    scenario=scenario_data)
                response = self.gemini.generate(prompt)
                results[risk_type] = response
            except Exception as e:
                logger.error(f"Error generating keywords for {risk_type}: {e}")
                results[risk_type] = {"keywords": []}
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