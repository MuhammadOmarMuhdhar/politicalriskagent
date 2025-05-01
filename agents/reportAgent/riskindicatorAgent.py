import logging
import json
from agents.base_model import GeminiModel
from agents.prompts import header

logger = logging.getLogger(__name__)

class agent:
    def __init__(self, api_key, subcategories, subcategories_scores, user_data, model_name="gemini-2.0-flash"):
        """Initialize the scenario generator agent with API key and model."""
        self.gemini = GeminiModel(api_key=api_key, model_name=model_name)
        self.subcategories = subcategories
        self.user_data = user_data
        self.risk_factors = []  # Initialize the risk_factors attribute
        self.subcategories_scores = subcategories_scores
        

    
    def build_scenario_prompt(self, risk_type, indicators, context_dict):
        """Build prompt for generating comprehensive risk analysis based on indicators and content."""
        heading = header.prompt_header(user_data=self.user_data)
        
        # Format indicators as a bulleted list for better readability
        formatted_indicators = "\n".join([f"• {indicator}" for indicator in indicators[:4]])
        
        prompt = f"""
                
        INPUT DATA:
        Risk Type: {risk_type}
        Key Indicators:
        {formatted_indicators}
        Relevant Content: {json.dumps(context_dict)}

        {heading}

        TASK:
        Create a concise, evidence-based political risk assessment tailored specifically to the client's context. 

        DELIVERABLES:
        1. Risk Description (2-3 sentences): Explain what this risk entails and why it matters specifically to the client's use case

        2. Impact Analysis (3-4 sentences): Provide concrete examples of how this risk impacts the client's specific operations, including but not limited to:
        - Specific financial implications (e.g., costs, market restrictions, supply chain issues) that would affect the cleint's business
        - Regulatory and operational consequences most relevant to your industry position
        - Should be narative like but still concise and professional

        3. Indicator Analysis: For each of the provided key indicators, provide a focused sentence that:
        - References specific events/policies from the content with direct relevance to your business model
        - Explains quantifiable business impacts on your operations or holdings

        STYLE REQUIREMENTS:
        - Note what type of client this is, and always keep in mind why this is relevant to them
        - Use direct address ("you"/"your") without using "I," "we," or "our" 
        - Focus on business implications rather than general observations
        - Maintain a professional, confident tone
        - Ground all statements in the specific risk factor data provided
        - Never refer to "provided documents," "provided content," or use phrases like "based on the information provided" - instead, speak directly about the facts and their implications
        - Avoid meta-commentary about information sources or your own analysis process
        - Communicate with authority as if you are the expert who originally discovered these insights
        - Write in a direct, declarative style without hedging language

        FORMAT YOUR RESPONSE AS A JSON OBJECT WITH THIS EXACT STRUCTURE:
        {{
        "risk": "{risk_type}",
        "description": "Your client-specific risk description here",
        "impact_analysis": "Your impact analysis tailored to the client's business",
        "indicator_ranking": "Prioritized list of indicators by severity for this client's business with explanation",
        "indicator1": "Your analysis of indicator 1 specific to client operations",
        "indicator2": "Your analysis of indicator 2 specific to client operations",
        "indicator3": "Your analysis of indicator 3 specific to client operations",
        "indicator4": "Your analysis of indicator 4 specific to client operations"
        }}

        Your analysis must be factual, balanced, and directly applicable to the client's specific needs, avoiding speculation while highlighting genuine concerns relevant to their specific business context.
        Ensure every statement draws from the provided content with specific examples, figures, and implications that matter to this particular client.
        """
        return prompt
    
    def generate_risk_analysis(self):
        """Generate risk analysis based on indicators and content."""
        try:
            # Clear existing risk factors before generating new ones
            self.risk_factors = []
            
            for risk_type, context_dict in self.subcategories.items():
                try:
                    indicators = list(context_dict.keys())  # Get up to 4 indicators
                    
                    # Build prompt for this specific risk type
                    prompt = self.build_scenario_prompt(risk_type, indicators, context_dict)
                    logger.info(f"Generating risk analysis for {risk_type}")
                    
                    # Generate response using the model
                    response = self.gemini.generate(prompt)
                    
                    # Parse JSON response
                    try:
                        # Try to parse JSON directly
                        risk_analysis = json.loads(response)
                    except json.JSONDecodeError:
                        # Extract JSON if parsing fails
                        start_idx = response.find('{')
                        end_idx = response.rfind('}') + 1
                        if start_idx >= 0 and end_idx > start_idx:
                            json_str = response[start_idx:end_idx]
                            risk_analysis = json.loads(json_str)
                        else:
                            logger.error(f"Could not extract valid JSON from response for {risk_type}")
                            continue  # Skip this risk type and move to the next
                    
                    # Handle the case where fewer than 4 indicators might be available
                    indicator_count = min(len(indicators), 4)
                    indicator_values = []
                    
                    for i in range(1, 5):
                        key = f"indicator{i}"
                        if key in risk_analysis and i <= indicator_count:
                            indicator_values.append(risk_analysis[key])
                        elif i <= indicator_count:
                            # If the model didn't provide an analysis for this indicator
                            indicator_values.append(f"Analysis for {indicators[i-1]} not available")
                    
                    # Ensure we have exactly the number of indicators we need
                    while len(indicator_values) < indicator_count:
                        indicator_values.append("Indicator analysis not available")
                    
                    # Convert the flat JSON structure to the format expected by generate_risk_factors
                    risk_factor = {
                        "title": risk_analysis["risk"],
                        "risk_level": "medium",  # Default risk level
                        "description": risk_analysis["description"],
                        "impact_analysis": risk_analysis["impact_analysis"],
                        "indicators": indicator_values
                    }
                    
                    # Add this risk factor to the list
                    self.risk_factors.append(risk_factor)
                    
                except Exception as inner_e:
                    # Log error but continue processing other risk types
                    logger.error(f"Error processing risk type {risk_type}: {inner_e}")
                    continue
            
            # Return all generated risk factors
            return self.risk_factors
                
        except Exception as e:
            logger.error(f"Error in generate_risk_analysis: {e}")
            return None
    
    def generate_risk_factors(self) -> str:
        """Generate the HTML for all risk factors"""

        scores = self.subcategories_scores
        # Determine risk levels based on scores

        for risk_factor in self.risk_factors:
            risk_factor["risk_level"] = "low" if scores[risk_factor["title"]] < 33 else "medium" if scores[risk_factor["title"]] < 66 else "high"
           
      
        risk_factors_html = ""
        
        for i, factor in enumerate(self.risk_factors, 1):
            indicators_html = ""
            for j, indicator in enumerate(factor["indicators"], 1):
                indicators_html += f"""
                <div class="indicator-item">
                    <div class="indicator-number">{j}.</div>
                    <div class="indicator-text">{indicator}</div>
                </div>
                """
            
            risk_factors_html += f"""
            <div class="risk-factor-card">
                <div class="risk-factor-header">
                    <div class="risk-factor-title">{factor["title"]}</div>
                    <div class="risk-badge badge-{factor["risk_level"]}">{factor["risk_level"].capitalize()} Risk</div>
                </div>
                <div class="risk-factor-content">
                    <div class="risk-description">
                        <p>{factor["description"]}</p>
                    </div>
                    
                    <div class="impact-analysis">
                        <h3>Impact Analysis</h3>
                        <div class="impact-content">
                            <p>{factor["impact_analysis"]}</p>
                        </div>
                    </div>
                    
                    <div class="indicators">
                        <h3>Key Risk Indicators</h3>
                        <div class="indicator-list">
                            {indicators_html}
                        </div>
                    </div>
                </div>
            </div>
            """
        
        return risk_factors_html