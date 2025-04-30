from sentence_transformers import SentenceTransformer
import numpy as np

def generate(df, text_column='content'):
    """
    Process a DataFrame to add embeddings for a text column.
    Loads the model only ONCE and processes all rows together.
    
    Args:
        df: DataFrame containing the text data
        text_column: Name of the column containing text to embed
        
    Returns:
        DataFrame with 'embedding' column added
    """
    # Force CPU to avoid MPS memory issues
    device = 'cpu'
    
    # Extract all texts into a list
    texts = df[text_column].tolist()
    
    print(f"Processing {len(texts)} texts")
    
    # Load model ONCE (outside the apply function)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    model.to(device)  # Move to CPU
    
    # Process in reasonable batch sizes to avoid memory issues
    batch_size = 32
    all_embeddings = []
    
    # Process in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
        batch_embeddings = model.encode(batch, convert_to_numpy=True)
        all_embeddings.extend(batch_embeddings)
    
    # Assign embeddings back to DataFrame
    df['embedding'] = all_embeddings
    
    return df