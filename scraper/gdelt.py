from datetime import datetime
from typing import List, Optional, Dict, Union
import pandas as pd
from gdeltdoc import GdeltDoc, Filters
from utils import countrycode

# Import refactored classes
from scraper import connector, processor

from datetime import datetime
from typing import List, Optional, Dict, Union
import pandas as pd
from gdeltdoc import GdeltDoc, Filters
from utils import countrycode
import time
from collections import defaultdict

# Import refactored classes
from scraper import connector, processor

class Scraper:
    """Handles querying GDELT API and processing results through the document pipeline."""
    
    def __init__(self, keyword_dict: Dict, user_data: Dict, domains: List[str]):
        """
        Initialize the GDELT query processor.
        
        Args:
            keyword_dict: Dictionary of risk types and associated keywords
            user_data: User location and target location information
            domains: List of news domains to filter by
        """
        self.gdelt_client = GdeltDoc()
        self.keyword_dict = keyword_dict
        self.user_data = user_data
        self.domains = domains

    def _get_country_codes(self) -> List[str]:
        """
        Convert country names to ISO3 codes from user data.
        
        Returns:
            List of country codes including home and target countries
        """
        home_country = self.user_data.get("location", "")
        target_countries = self.user_data.get("target_locations", "")

        # Convert home country to code
        home_country_code = countrycode.convert(home_country) if home_country else None
        
        # Convert target countries to codes
        target_country_codes = []
        if target_countries:
            for country in target_countries.split(", "):
                code = countrycode.convert(country)
                if code:
                    target_country_codes.append(code)
        
        # Combine home and target country codes
        country_codes = [home_country_code] + target_country_codes

        # return string if only one country code
        if len(country_codes) == 1:
            country_codes = country_codes[0]
        else:
            country_codes = [code for code in country_codes if code]
            
        return home_country_code

    def run(
        self,
        risk_keywords: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        language: str = "eng",
        process_limit: int = 25
    ) -> Dict[str, pd.DataFrame]:
        """
        Process GDELT queries for each risk type and keyword.
        
        Args:
            risk_keywords: Optional additional keywords for the GDELT search
            start_date: Optional start date for article search
            end_date: Optional end date for article search
            language: Language code (default: "eng" for English)
            process_limit: Maximum number of articles to process
            
        Returns:
            Dictionary mapping risk types to DataFrames of articles
        """
        # Get country codes from user data
        country_codes = self._get_country_codes()
        
        # Log query parameters
        self._log_query_parameters(
            risk_keywords, country_codes, start_date, end_date,
            self.domains, language, process_limit
        )

        # Dictionary to store results by risk type
        results = defaultdict(lambda: defaultdict(dict))

        for broad_risk, item in self.keyword_dict.items(): 
            for specific_risk, sub_item in item.items():
    
                risk_articles = []
                for broad_keyword, sub_item in sub_item.items():
                    keywords_list = sub_item['keywords']
            
                    for keyword in keywords_list:
                        # Ensure keyword is a string
                        if not isinstance(keyword, str):
                            print(f"Skipping non-string keyword: {keyword}")
                            continue
                        
                        print(f"Processing keyword: {keyword}")
                        
                        # Fetch articles for this keyword
                        articles_df = self._fetch_articles(
                            risk_keywords=keyword,  # Pass as a list
                            target_country_code=country_codes,
                            start_date=start_date,
                            end_date=end_date,
                            domain_filter=self.domains,
                            language=language
                        )
                        
                        # Check if we got valid results
                        if isinstance(articles_df, pd.DataFrame) and not articles_df.empty:
                            # Add metadata
                            articles_df['keyword'] = keyword
                            articles_df['broad_keyword'] = broad_keyword
                            articles_df['risk_type'] = specific_risk
                            articles_df['broad_risk'] = broad_risk
                            results[broad_risk][specific_risk][keyword] = articles_df

                        time.sleep(1)  # Rate limiting

                        
        
        # Count total articles processed
        # total_articles = sum(len(df) for df in results.values())
        # print(f"Total articles retrieved: {total_articles}")
        
        return results
        
    def _log_query_parameters(
        self, 
        risk_keywords: Optional[List[str]],
        target_country_code: Optional[List[str]],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        domain_filter: Optional[List[str]],
        language: str,
        process_limit: int
    ) -> None:
        """Log the query parameters for debugging and monitoring."""
        print("\n===== Processing GDELT Query =====")
        print(f"Risk Keywords: {risk_keywords or 'None'}")
        print(f"Target Country Codes: {target_country_code or 'None'}")
        print(f"Start Date: {start_date.strftime('%Y-%m-%d') if start_date else 'None'}")
        print(f"End Date: {end_date.strftime('%Y-%m-%d') if end_date else 'None'}")
        print(f"Domain Filter: {domain_filter if domain_filter else 'All'}")
        print(f"Language: {language}")
        print(f"Processing Limit: {process_limit}")
        print("================================")
        
    def _fetch_articles(
        self,
        risk_keywords: List[str],
        target_country_code: Optional[List[str]],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        domain_filter: Optional[List[str]],
        language: str
    ) -> pd.DataFrame:
        """
        Fetch articles from GDELT based on filters.
        
        Args:
            risk_keywords: List of keywords for the GDELT search
            target_country_code: Optional list of country codes to filter articles
            start_date: Optional start date for article search
            end_date: Optional end date for article search
            domain_filter: Optional list of domains to include
            language: Language code
            
        Returns:
            DataFrame containing article metadata
        """
        try:
            # Create GDELT filters
            filters = Filters(
                start_date=start_date.strftime('%Y-%m-%d') if start_date else None,
                end_date=end_date.strftime('%Y-%m-%d') if end_date else None,
                num_records=250,  # Fixed at 250 as per requirements
                keyword=risk_keywords,
                domain=domain_filter,
                country=target_country_code,
                language=language
            )
            
            print("Querying GDELT API...")
            result = self.gdelt_client.article_search(filters)
            
            if isinstance(result, pd.DataFrame):
                print(f"Retrieved {len(result)} articles from GDELT")
                return result
            else:
                print(f"Unexpected result type from GDELT: {type(result)}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error querying GDELT: {e}")
            return pd.DataFrame()  # Return empty DataFrame on error