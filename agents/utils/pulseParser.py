import pandas as pd

def organize_risk_scores(risk_data):
    """
    Organize risk scores by category, subcategory, and keyword into sorted DataFrames.
    
    Args:
        risk_data (dict): Dictionary containing risk scores organized by date.
    
    Returns:
        tuple: DataFrames for category, subcategory, and keyword risk scores by date.
    """
    def build_risk_dataframe(risk_dict, level_name):
        records = [
            (date, level, score)
            for date, levels in risk_dict.items()
            for level, score in levels.items()
        ]
        df = pd.DataFrame(records, columns=["Date", level_name, "Score"])
        df["Date"] = pd.to_datetime(df["Date"])
        return df.sort_values(by=["Date", level_name])

    risk_df =risk_data["total_by_date"]
    risk_df = pd.DataFrame(risk_df.items(), columns=["Date", "Score"])
    risk_df["Date"] = pd.to_datetime(risk_df["Date"])
    risk_df = risk_df.sort_values(by=["Date"])
    category_df = build_risk_dataframe(risk_data["category_by_date"], "Category")
    subcategory_df = build_risk_dataframe(risk_data["subcategory_by_date"], "Subcategory")
    keyword_df = build_risk_dataframe(risk_data["keyword_by_date"], "Keyword")

    return risk_df, category_df, subcategory_df, keyword_df

