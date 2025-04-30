import re
import uuid

def insert_articles_to_cosmos(container, articles_dict):
    """
    Insert articles from a DataFrame into a Cosmos DB container.
    
    Parameters:
    -----------
    container : CosmosContainer
        The Cosmos DB container to insert documents into
    articles_df : dict
        Dictionary containing article data with keys as article titles/ids
        
    Returns:
    --------
    list
        List of inserted document IDs
    """
    
    # Function to create a valid ID
    def create_valid_id(original_id):
        # Option 1: Clean the original ID by removing illegal characters
        valid_id = re.sub(r'[/\\?#]', '_', original_id)
        valid_id = valid_id.rstrip(' \n')
        
        # If the ID is still problematic or empty, use option 2
        if not valid_id or len(valid_id) > 255:
            # Option 2: Create a UUID-based ID
            valid_id = str(uuid.uuid4())
        
        return valid_id
    
    inserted_ids = []
    
    # When inserting documents
    for key, value in articles_dict.items():
        # Create a safe ID from the key
        safe_id = create_valid_id(key)
        
        # Create a document with the dictionary structure
        document = {
            "id": safe_id,
            "original_title": key,  # Store the original title as a separate field
            "url": value["url"],
            "domain": value["domain"],
            "embedding": value["embedding"].tolist(),
            'content': value["content"]
        }
        
        # Insert into Cosmos DB
        container.upsert_item(document)
        inserted_ids.append(safe_id)
    
    return inserted_ids