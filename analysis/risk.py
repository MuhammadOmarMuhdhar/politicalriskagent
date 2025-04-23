from scipy import stats
import pandas as pd
import numpy as np
from textblob import TextBlob

class Calculator:
    """
    A class to analyze risk based on sentiment analysis of articles.
    
    This class provides functionality to:
    1. Analyze sentiment of article text
    2. Calculate risk scores based on sentiment and other metrics
    
    Attributes:
        None
    """
    
    def __init__(self):
        """Initialize the RiskAnalyzer class."""
        pass
        
    def analyze_sentiment(self, text):
        """
        Analyze the sentiment of the given text.
        
        Parameters:
        -----------
        text : str
            Text to analyze for sentiment
            
        Returns:
        --------
        float
            Sentiment polarity score (-1 to 1)
        """
        if not isinstance(text, str):
            return 0.0
            
        try:
            analysis = TextBlob(text)
            # Get the sentiment polarity
            return analysis.sentiment.polarity
        except Exception:
            return 0.0
            
    def add_sentiment_to_dataframe(self, dataframe, text_column='title'):
        """
        Add sentiment analysis scores to the dataframe.
        
        Parameters:
        -----------
        dataframe : pandas.DataFrame
            Input dataframe containing articles data
        text_column : str, optional
            Column name containing text to analyze, default is 'title'
            
        Returns:
        --------
        pandas.DataFrame
            Dataframe with added sentiment column
            
        Raises:
        -------
        TypeError
            If input is not a pandas DataFrame
        ValueError
            If the specified text column does not exist
        """
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")
            
        if text_column not in dataframe.columns:
            raise ValueError(f"Text column '{text_column}' not found in dataframe")
            
        df = dataframe.copy()
        df['sentiment'] = df[text_column].apply(self.analyze_sentiment)
        
        return df
        
    def calculate_risk_scores(self, dataframe, column, top_n=3):
        """
        Calculate risk score based on the sentiment of the articles.
        
        Parameters:
        -----------
        dataframe : pandas.DataFrame
            Input dataframe containing articles data
        column : str
            Column name to group by (e.g., 'risk_type')
        top_n : int, optional
            Number of top risk items to return, default is 3
            
        Returns:
        --------
        pandas.DataFrame
            Dataframe containing top risk scores
            
        Raises:
        -------
        ValueError
            If required columns are missing or if dataframe is empty
        TypeError
            If input is not a pandas DataFrame
        """
        # Input validation
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")
            
        if len(dataframe) == 0:
            raise ValueError("Input DataFrame is empty")
            
        required_columns = ['sentiment', 'title', column]
        missing_columns = [col for col in required_columns if col not in dataframe.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
            
        # Make a copy to avoid modifying the original dataframe
        df = dataframe.copy()
        
        try:
            # Calculate sentiment scores with proper handling of potential non-numeric values
            df['sentiment'] = pd.to_numeric(df['sentiment'], errors='coerce')
            df.dropna(subset=['sentiment'], inplace=True)
            
            if len(df) == 0:
                raise ValueError("No valid sentiment values found in the data")
                
            # Calculate sentiment scores
            df['sentiment_score'] = df['sentiment'].apply(
                lambda x: -2 if x > 0 else (2 if x < 0 else 0)  # More weight on negative
            )
            
            # For each risk type, calculate metrics
            risk_metrics = df.groupby(column).agg(
                avg_sentiment=('sentiment_score', 'mean'),  # Average sentiment score
                article_count=('title', 'count'),  # Total articles
                negative_ratio=('sentiment_score', lambda x: sum(x > 0) / max(len(x), 1))  # % negative with zero division protection
            )
            
            # Handle empty results after grouping
            if len(risk_metrics) == 0:
                return pd.DataFrame(columns=['avg_sentiment', 'article_count', 'negative_ratio',
                                           'norm_count', 'norm_sentiment', 'risk_score'])
                                           
            # Calculate normalized metrics (0-1 scale) with safeguards against division by zero
            max_count = risk_metrics['article_count'].max()
            risk_metrics['norm_count'] = risk_metrics['article_count'] / max(max_count, 1)
            
            # Use absolute value for sentiment normalization
            risk_metrics['norm_sentiment'] = abs(risk_metrics['avg_sentiment'])
            
            # Combined risk score (weighted)
            risk_metrics['risk_score'] = (
                0.33 * risk_metrics['norm_count'] +  # Volume component
                0.33 * risk_metrics['norm_sentiment'] +  # Sentiment severity
                0.33 * risk_metrics['negative_ratio']  # Proportion of negative coverage
            ) * 10
            
            # Handle potential NaN values in risk score
            risk_metrics['risk_score'] = risk_metrics['risk_score'].fillna(0)
            
            # Sort by risk score
            risk_metrics = risk_metrics.sort_values(by='risk_score', ascending=False)
            
            # Return top N results, or all if fewer than top_n are available
            return risk_metrics[['risk_score']].head(min(top_n, len(risk_metrics)))
            
        except Exception as e:
            # Catch any unexpected errors
            raise RuntimeError(f"Error calculating risk scores: {str(e)}")
            
    def run(self, dataframe, group_column, text_column='title', top_n=3):
        """
        End-to-end processing: add sentiment and calculate risk scores.
        
        Parameters:
        -----------
        dataframe : pandas.DataFrame
            Input dataframe containing articles data
        group_column : str
            Column name to group by for risk calculation (e.g., 'risk_type')
        text_column : str, optional
            Column containing text for sentiment analysis, default is 'title'
        top_n : int, optional
            Number of top risk items to return, default is 3
            
        Returns:
        --------
        pandas.DataFrame
            Dataframe containing top risk scores
        """
        # Add sentiment to the dataframe
        df_with_sentiment = self.add_sentiment_to_dataframe(dataframe, text_column)
        
        # Calculate and return risk scores
        return self.calculate_risk_scores(df_with_sentiment, group_column, top_n)
    


#     # Example usage
# if __name__ == "__main__":
#     # Create sample data
#     data = {
#         'title': [
#             "Company faces major security breach",
#             "New product launch receives positive feedback",
#             "Market volatility increases investor concerns",
#             "Industry regulations tighten following incidents",
#             "Competitors merge to challenge market position"
#         ],
#         'risk_type': [
#             "cybersecurity",
#             "product",
#             "market",
#             "regulatory",
#             "competitive"
#         ]
#     }
    
#     # Create DataFrame
#     articles_df = pd.DataFrame(data)
    
#     # Initialize the RiskAnalyzer
#     analyzer = Calculator()
    
#     # Process the articles and get risk scores
#     risk_scores = analyzer.run(articles_df, 'risk_type')
    
#     # Display results
#     print("Top risks by score:")
#     print(risk_scores)