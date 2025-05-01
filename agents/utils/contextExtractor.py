from collections import defaultdict
from data.azuredb import vectorSearch

def extract(scenarios, top_subcategories, container, similarity_threshold=0.1, top_k=5):
    content_extracted = defaultdict(dict)
    
    for key, value in scenarios.items():
        for key2, value2 in value.items():
            if key2 in top_subcategories:
                for key3, value3 in value2.items():
                    # First collect the scenarios
                    if key2 not in content_extracted:
                        content_extracted[key2] = {}
                    
                    if key3 not in content_extracted[key2]:
                        content_extracted[key2][key3] = []
                    
                    # Search for each scenario directly
                    scenario = value3['scenario'][0]
                    search_results = vectorSearch.search_documents(container, scenario, 
                                                     similarity_threshold=similarity_threshold, 
                                                     top_k=top_k)
                    content_extracted[key2][key3].append(search_results)
    
    return content_extracted