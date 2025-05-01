import logging
import json
import re
from typing import List, Dict, Any
from agents.base_model import GeminiModel
from agents.prompts import header

logger = logging.getLogger(__name__)

class agent:
    def __init__(self, api_key, user_data, model_name="gemini-2.0-flash"):
        """Initialize the executive summary agent with API key and model."""
        self.gemini = GeminiModel(api_key=api_key, model_name=model_name)
        self.executive_summary = ""  # Initialize executive summary attribute
        self.user_data = user_data

    def extract_risk_factors_from_html(self, html: str) -> List[Dict[str, Any]]:
        """
        Extract risk factor data from the HTML
        
        Args:
            html (str): HTML content containing risk factor cards
            
        Returns:
            List[Dict]: List of risk factor dictionaries
        """
        risk_factors = []
        
        # Find all risk factor cards using regex
        card_pattern = r'<div class="risk-factor-card">(.*?)</div>\s*</div>\s*</div>'
        cards = re.findall(card_pattern, html, re.DOTALL)
        
        for card in cards:
            try:
                # Extract title
                title_match = re.search(r'<div class="risk-factor-title">(.*?)</div>', card)
                title = title_match.group(1) if title_match else "Unknown Risk"
                
                # Extract risk level
                risk_level_match = re.search(r'<div class="risk-badge badge-(.*?)">(.*?)</div>', card)
                risk_level = risk_level_match.group(1) if risk_level_match else "medium"
                
                # Extract description
                description_match = re.search(r'<div class="risk-description">\s*<p>(.*?)</p>', card, re.DOTALL)
                description = description_match.group(1) if description_match else ""
                
                # Extract impact analysis
                impact_match = re.search(r'<div class="impact-content">\s*<p>(.*?)</p>', card, re.DOTALL)
                impact_analysis = impact_match.group(1) if impact_match else ""
                
                # Extract indicators
                indicator_pattern = r'<div class="indicator-text">(.*?)</div>'
                indicators = re.findall(indicator_pattern, card)
                
                # Create risk factor dictionary
                risk_factor = {
                    "title": title,
                    "risk_level": risk_level,
                    "description": description,
                    "impact_analysis": impact_analysis,
                    "indicators": indicators
                }
                
                risk_factors.append(risk_factor)
                
            except Exception as e:
                logger.error(f"Error extracting risk factor: {e}")
                continue
        
        return risk_factors

    def build_summary_prompt(self, risk_factors):
        """Build prompt for generating an executive summary based on risk factors."""
        # Convert risk factors to a JSON string for the prompt
        risk_factors_json = json.dumps(risk_factors)
        heading = header.prompt_header(user_data=self.user_data)
        
        prompt = f"""
        {heading}

        TASK:
        Create a concise, actionable executive summary (5-7 sentences only) based on the provided political risk assessment data. Address the client directly using "you" and "your" without using first-person pronouns.
        
        INPUT DATA:
        {risk_factors_json}
        
        STRUCTURE REQUIREMENTS:
        1. Opening sentence: Explain how this assessment uses news relevant to the client's business, analyzing political relevant factors to provide a comprehensive political risk landscape.
        2. Investor Context: Briefly characterize the investor profile and their specific investment scenario or portfolio exposure.
        3. Risk Identification: Specify the key political risks affecting investment returns, briefly describing each risk factor and its relevance to the client.
        4. State which risk category poses the greatest threat to portfolio value and why
        4. Impact Analysis: Highlight the most significant investment impacts across all identified risks, focusing on potential effects on asset valuations, market liquidity, and long-term returns.
        
        STYLE REQUIREMENTS:
        - Note what type of client this is, to make the summary relevant to them
        - Write exactly 5-7 complete sentences (no more, no less)
        - Use direct address ("you"/"your") without using "I," "we," or "our"
        - Focus on business implications rather than general observations
        - Maintain a professional, confident tone
        - Ground all statements in the specific risk factor data provided
        - Never refer to "provided documents," "provided content," or use phrases like "based on the information provided" - instead, speak directly about the facts and their implications
        - Avoid meta-commentary about information sources or your own analysis process
        - Communicate with authority as if you are the expert who originally discovered these insights
        - Write in a direct, declarative style without hedging language
        
        OUTPUT FORMAT:
        Return plain text only, not JSON. The summary must be exactly 4-5 complete sentences.
        """
        
        return prompt

    def create_executive_summary(self, html_content: str) -> str:
        """
        Create an executive summary from risk factor HTML using LLM.
        
        Args:
            html_content (str): HTML content containing risk factor cards
            
        Returns:
            str: Executive summary text
        """
        try:
            # Extract risk factors from HTML
            risk_factors = self.extract_risk_factors_from_html(html_content)
            
            if not risk_factors:
                logger.warning("No risk factors extracted from HTML")
                self.executive_summary = "No risk factors available to generate summary."
                return self.executive_summary
            
            # Build prompt for executive summary
            prompt = self.build_summary_prompt(risk_factors)
            
            # Generate summary using the model
            logger.info("Generating executive summary")
            response = self.gemini.generate(prompt)
            
            # Clean up response
            self.executive_summary = response.strip()
            return self.executive_summary
            
        except Exception as e:
            logger.error(f"Error creating executive summary: {e}")
            self.executive_summary = "Error generating executive summary. Please check the logs."
            return self.executive_summary

    def generate_executive_summary(self, html_content: str = None) -> str:
        """
        Generate the HTML for the executive summary
        
        Args:
            html_content (str, optional): HTML content containing risk factor cards.
                                         If provided, creates a new summary.
        
        Returns:
            str: HTML formatted executive summary
        """
        # Create a new summary if HTML content is provided
        if html_content:
            self.create_executive_summary(html_content)
            
        return f"""
        <div class="executive-summary">
        <h2 class="section-title">Executive Summary</h2>
        <p class="summary-content">
        {self.executive_summary}
        </p>
        </div>
        """