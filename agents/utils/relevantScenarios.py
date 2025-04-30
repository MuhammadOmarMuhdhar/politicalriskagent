from collections import defaultdict

def extract(scenarios, top_subcategories):
    """
    Extract scenarios for the top subcategories from the nested scenarios dictionary.
    
    Parameters:
    -----------
    scenarios : dict
        Nested dictionary containing all scenarios
    top_subcategories : list or set
        List or set of subcategory keys to extract
        
    Returns:
    --------
    dict
        Dictionary containing only scenarios from the specified top subcategories
    """
    top_subcategories_scenarios = defaultdict(dict)
    
    for key, value in scenarios.items():
        for key2, value2 in value.items():
            if key2 in top_subcategories:
                for key3, value3 in value2.items():
                    top_subcategories_scenarios[key2][key3] = value3['scenario']
    
    return top_subcategories_scenarios