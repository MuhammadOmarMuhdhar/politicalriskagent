import logging
import json
import time
from agents.base_model import GeminiModel
from agents.prompts import header
from collections import defaultdict

logger = logging.getLogger(__name__)

class agent:
    def __init__(self, api_key, model_name="gemini-2.0-flash"):
        """Initialize the keyword generator agent with API key and model."""
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
    
    def _build_keyword_prompt(self, user_data, risk_type, scenario):
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

        ---

        **Your Task:**  
        Generate **3 targeted keywords** that capture the most relevant risk-related factors in this scenario. Each keyword should:

        - Be **highly specific** to the client's context
        - Do not use generic terms or phrases like ESG, Risk, Political, etc. 
        - Be **strictly 1 words** in length  
        - Be useful for querying structured sources like the **GDELTdocs API**  
        - Be **actionable** and relevant to the client's business objectives
        - Avoid generic terms or phrases

        Please respond in the following JSON format:
        {{
            "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6"]
        }}

        ---

        ### Example

        **Scenario**:  
        The client, a mid-sized renewable energy company headquartered in Germany, is planning to expand its solar panel manufacturing operations into Southeast Asia, specifically Vietnam. The company intends to form a joint venture with a local partner and begin operations within 18 months. The investment is considered strategic, with the goal of capturing emerging green energy markets in the region. However, the client is concerned about changing environmental regulations, import/export restrictions, and government subsidies for local competitors.

        **Risk Type**: Regulatory Risk  

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

    def generate(self, user_data, scenarios, risk_type=None):
        """Generate keywords based on scenarios for specific or all risk types."""
        results = defaultdict(lambda: defaultdict(dict))  
        
        # Generate for all risk types with available scenarios
        for broad_risk, item in self.risk_types.items(): 
            for specific_risk, sub_item in item.items():
                keywords_list = sub_item['keywords']
                for keyword in keywords_list:
                
                    scenario_data = scenarios[broad_risk][specific_risk]
                
                    if not scenario_data or keyword not in scenario_data:
                        logger.warning(f"Empty scenario data for {risk_type}")
                        results[broad_risk][specific_risk][keyword] = {"keywords": []}
                        continue
                        
                    try:
                        prompt = self._build_keyword_prompt(user_data=user_data, 
                                                            risk_type=keyword, 
                                                            scenario=scenario_data[keyword])
                        response = self.gemini.generate(prompt)
                        results[broad_risk][specific_risk][keyword] = response
                    except Exception as e:
                        logger.error(f"Error generating keywords for {keyword}: {e}")
                        results[broad_risk][specific_risk][keyword] = {"keywords": []}
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