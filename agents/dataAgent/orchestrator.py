import logging
from agents.dataAgent import scenarioAgent
from agents.dataAgent import keywordAgent
from agents.utils.cleanJson import parse
from scraper import gdelt
from datetime import datetime, timedelta
from agents.dataAgent import validationAgent
import pandas as pd
from agents.utils.extractArticles import extract
from rag import embeddingsGenerator

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    This class coordinates a multi-step risk analysis process:
    1. Generate risk scenarios based on the provided user survey data
    2. Extract relevant keywords from the generated scenarios
    3. Query the GDELT database for news articles related to these keywords
    
    The results are cleaned and structured into two dictionaries:
    - One mapping each risk to its associated scenario and keywords
    - Another containing the retrieved GDELT articles for each risk
    
    Args:
        api_key (str): API key for the language model services
        model_name (str, optional): The LLM to use. Defaults to "gemini-2.0-flash"
        user_data (dict, optional): User data for scenario generation and scraping. Defaults to None
        domains (list, optional): List of domains to scrape. Defaults to None
        response (dict, optional): Existing keyword dictionary. Defaults to None
        
    Returns in run():
        tuple: (results, gdelt_results) where:
            - results: Dict mapping each risk to scenario and keywords
            - gdelt_results: Dict mapping each risk to related news articles
    """
    def __init__(self, api_key, model_name="gemini-2.0-flash", user_data=None, domains=None, response=None):
        """Initialize the orchestrator with user data and both agents."""
        self.api_key = api_key
        self.model_name = model_name
        self.user_data = user_data
        self.domains = domains
        
        self.scenario_agent = scenarioAgent.agent(api_key=api_key, model_name=model_name)
        self.keyword_agent = keywordAgent.agent(api_key=api_key, model_name=model_name)
        self.validation_agent = validationAgent.agent(api_key=api_key)
        self.gdelt = gdelt.Scraper(
            keyword_dict=response,
            user_data=user_data,
            domains=domains
        )
        
    def _gdelt_query(self, risk_keywords, start_date, end_date, language, process_limit):
        """Query GDELT for articles related to the specified keywords."""
        return self.gdelt.run(
            risk_keywords=risk_keywords,
            start_date=start_date,
            end_date=end_date,
            language=language,
            process_limit=process_limit
        )
        
    def run(self, risk_type=None, end_date=None, start_date=None, user_data=None):
        """
        Run the full data extraction and feature engineering process.
        """
        # Use user_data from initialization if not provided in method call
        if user_data is None:
            user_data = self.user_data
            
        if user_data is None:
            raise ValueError("User data must be provided either at initialization or in the run method")
            
        # Set default dates if not provided
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=365)
            
        # Step 1: Generate scenarios from user survey data
        logger.info("Starting scenario generation")
        scenarios = self.scenario_agent.generate(user_data, risk_type)
        # Clean scenarios
        scenarios_cleaned = parse(scenarios, field_to_clean="scenario", fallback={})
        
        # Step 2: Generate keywords from scenarios
        logger.info("Starting keyword generation from scenarios")
        keywords = self.keyword_agent.generate(user_data=user_data, scenarios=scenarios_cleaned, risk_type=risk_type)
        # Clean keywords
        keywords_cleaned = parse(keywords, field_to_clean="keywords", fallback={})
        
        # Combine results for easier consumption
        results = {}
        for risk in scenarios_cleaned:
            if risk in keywords_cleaned and 'keywords' in keywords_cleaned[risk]:
                results[risk] = {
                    "scenario": scenarios_cleaned[risk],
                    "keywords": keywords_cleaned[risk]['keywords']
                }
                
        # Step 3: Query GDELT for articles related to the keywords
        logger.info("Starting GDELT query for articles")
        
        # Create a new scraper with the updated keywords
        gdelt_scraper = gdelt.Scraper(
            keyword_dict=keywords_cleaned,
            user_data=user_data,
            domains=self.domains
        )
        
        # Run the scraper once to get all results
        gdelt_results = gdelt_scraper.run(
            start_date=start_date,
            end_date=end_date,
            language="eng"
        )
        # Combine the GDELT results 
        all_gdelt_articles = []
        for broad_risk, item in gdelt_results.items(): 
                    for specific_risk, sub_item in item.items():
                        for keyword, data_frame in sub_item.items():
                            all_gdelt_articles.append(data_frame)
        all_gdelt_articles = pd.concat(all_gdelt_articles, ignore_index=True)
        all_gdelt_articles = all_gdelt_articles.drop_duplicates(subset=['title'])

        logger.info("GDELT query completed")
        logger.info(f"Number of articles retrieved: {len(all_gdelt_articles)}")

        # Step 4: Validate the GDELT results
        logger.info("Starting validation of GDELT results")
        # Validate the GDELT results
        valid_results = self.validation_agent.validate(user_data=user_data, articles_dict=gdelt_results)
        # Clean the validation results
        valid_results_cleaned = parse(valid_results, field_to_clean="relevant", fallback={})
        # extract relevant articles
        relevant_articles_titles = []
        for broad_risk, item in valid_results_cleaned.items():
            for specific_risk, sub_item in item.items():
                for keyword, data_frame in sub_item.items():
                    if isinstance(data_frame, dict) and 'relevant' in data_frame:
                        relevant_articles_titles.extend(data_frame['relevant'])

       
        # Filter the articles based on the validation results
        relevant_articles_df = all_gdelt_articles[all_gdelt_articles['title'].isin(relevant_articles_titles)]

        logger.info(f"Number of relevant articles: {len(relevant_articles_df)}")

        # Step 5: extract article content
        logger.info("Starting article content extraction")
        relevant_articles_df.reset_index(drop=True, inplace=True)
        relevant_articles_df['content'] = relevant_articles_df['url'].apply(
                                            lambda x: extract(x)[0]  # Extract only the content
                                        )
       
        # step 6: generate embeddings
        relevant_articles_df_embedded = embeddingsGenerator.generate(relevant_articles_df, text_column='content')

        # step 7: save as a json file
        relevant_articles_df_embedded['date'] = pd.to_datetime(relevant_articles_df_embedded['seendate'])
        relevant_articles_df_embedded['date'] = relevant_articles_df_embedded['date'].dt.date

        final_output_dict = {
                row['title']: {
                    'url' : row['url'],
                    'domain': row['domain'],
                    'embedding': row['embedding'],
                    'content': row['content'],
                    'date': row['date'],
                }
                for _, row in relevant_articles_df_embedded.iterrows() 
            }

        return scenarios_cleaned, final_output_dict

# # Example usage for corrected Orchestrator
# if __name__ == "__main__":
#     import os
#     from pprint import pprint
    
#     # Set up API key (typically from environment variables)
#     api_key = os.environ.get("GEMINI_API_KEY")
    
#     # Sample user data
#     user_data = {
#         "company_name": "TechInnovate Inc.",
#         "industry": "Technology",
#         "risk_concerns": ["cybersecurity", "supply_chain", "regulatory"],
#         "business_description": "We develop cloud-based software solutions for enterprise customers.",
#         "location": "United States",
#         "company_size": "Medium (100-500 employees)"
#     }
    
#     # List of preferred news domains to scrape (optional)
#     domains = [
#         "reuters.com",
#         "bloomberg.com",
#         "wsj.com",
#         "techcrunch.com"
#     ]
    
#     # Initialize the orchestrator with user data
#     orchestrator = Orchestrator(
#         api_key=api_key, 
#         user_data=user_data,
#         domains=domains
#     )
    
#     # Set time range for GDELT queries (last 90 days)
#     end_date = datetime.now()
#     start_date = end_date - timedelta(days=90)
    
#     # Run the orchestration process
#     # No need to pass user_data again
#     results, gdelt_results = orchestrator.run(
#         risk_type=None,  # Process all risk types
#         end_date=end_date,
#         start_date=start_date
#     )
    
#     # Print the results
#     print("\n=== RISK SCENARIOS AND KEYWORDS ===")
#     pprint(results)
    
#     print("\n=== GDELT ARTICLE RESULTS ===")
#     # Assume gdelt_results is now a dictionary with risk types as keys
#     for risk_type, articles in gdelt_results.items():
#         print(f"\nRisk: {risk_type}")
#         print(f"Number of articles: {len(articles)}")
#         if articles:
#             print("Sample article titles:")
#             for article in articles[:3]:  # Print first 3 article titles
#                 print(f"- {article.get('title', 'No title')}")