from azure.cosmos import CosmosClient, PartitionKey

def initialize_cosmos_client(endpoint, key, database_name, container_name, dimensions=384):
    """
    Initialize Azure Cosmos DB client with vector search capabilities.
    
    Parameters:
    -----------
    endpoint : str
        The Cosmos DB endpoint URL
    key : str
        The access key for the Cosmos DB account
    database_name : str
        The name of the database to create or use
    container_name : str
        The name of the container to create or use
    dimensions : int, optional
        The dimensions of the vector embeddings (default: 384)
    
    Returns:
    --------
    tuple
        (client, database, container) - The initialized Cosmos client, database and container
    """
    # Initialize the Cosmos client
    client = CosmosClient(endpoint, key)
    
    # Create or get a database
    database = client.create_database_if_not_exists(id=database_name)
    
    # Define vector policy for the embedding field
    vector_policy = {
        "vectorEmbeddings": [
            {
                "path": "/embedding",
                "dataType": "float32",
                "distanceFunction": "cosine",
                "dimensions": dimensions
            }
        ]
    }
    
    # Create container with vector search capabilities
    container = database.create_container_if_not_exists(
        id=container_name,
        partition_key=PartitionKey(path="/id"),
        vector_embedding_policy=vector_policy
    )
    
    return client, database, container