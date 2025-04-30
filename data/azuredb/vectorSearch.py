from sentence_transformers import SentenceTransformer

def search_documents(container, query_text, model_name="all-MiniLM-L6-v2", 
                     similarity_threshold=0.7, top_k=5, batch_size=64):
    """
    Search for documents in Cosmos DB using vector similarity.
    
    Parameters:
    -----------
    container : CosmosContainer
        The Cosmos DB container to search in
    query_text : str
        The text query to search for
    model_name : str, optional
        The name of the embedding model to use (default: "all-MiniLM-L6-v2")
    similarity_threshold : float, optional
        The maximum distance threshold for matches (default: 0.7)
    top_k : int, optional
        The maximum number of results to return (default: 5)
    batch_size : int, optional
        Batch size for processing embeddings (default: 64)
        
    Returns:
    --------
    list
        List of dictionaries containing search results
    """
    # Load the model
    embedding_model = SentenceTransformer(model_name)
    
    # Generate embedding for the query text
    query_embedding = embedding_model.encode(query_text, batch_size=batch_size, 
                                            show_progress_bar=False).tolist()
    
    # Query using SQL syntax with the VectorDistance function
    results = container.query_items(
        query='''
        SELECT TOP @num_results c.id, c.original_title, c.content,
        VectorDistance(c.embedding, @embedding) as similarity_score
        FROM c
        WHERE VectorDistance(c.embedding, @embedding) < @similarity_threshold
        ORDER BY VectorDistance(c.embedding, @embedding)
        ''',
        parameters=[
            {"name": "@embedding", "value": query_embedding},
            {"name": "@num_results", "value": top_k},
            {"name": "@similarity_threshold", "value": similarity_threshold}
        ],
        enable_cross_partition_query=True,
        populate_query_metrics=True
    )
    
    # Convert results to list and format
    results = list(results)
    
    # Format the results to include title and content as requested
    formatted_results = [
        {
            "title": result["original_title"],
            "content": result["content"],
            "similarity_score": result["similarity_score"],
            "id": result["id"]
        }
        for result in results
    ]
    
    return formatted_results