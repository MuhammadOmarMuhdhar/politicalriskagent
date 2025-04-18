import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_and_parse_json(input_data, field_to_clean=None, fallback=None):
    """
    Cleans and parses JSON strings from various input formats:
    1. Dictionary of JSON strings
    2. Single JSON string
    3. Already parsed JSON (dict/list)
    
    Can optionally clean values within a specified field.
    
    Parameters:
    -----------
    input_data : str, dict, or list
        The input data to clean and parse
    field_to_clean : str or None
        If specified, values in this field will be cleaned (e.g., strip whitespace)
    fallback : Any
        Value to return if parsing fails
        
    Returns:
    --------
    dict, list, or fallback
        Parsed and cleaned JSON data if successful, else fallback
    """
    # Define a nested function to handle the actual JSON parsing
    def parse_json_string(json_str):
        if not isinstance(json_str, str):
            return json_str  # Already parsed or not a string
            
        try:
            # Remove code block markers if present
            cleaned_str = json_str.strip()
            for marker in ['```json', '```', '`']:
                cleaned_str = cleaned_str.replace(marker, '')
            cleaned_str = cleaned_str.strip()
            
            # Parse the JSON
            return json.loads(cleaned_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing JSON: {e}")
            return None
    
    # Define a nested function to clean specific fields if needed
    def clean_field_values(data, field):
        if not field or field not in data:
            return data
            
        field_value = data[field]
        
        # Handle different field types
        if isinstance(field_value, list):
            # Clean each item in the list (e.g., stripping whitespace for strings)
            data[field] = [item.strip() if isinstance(item, str) else item for item in field_value]
        elif isinstance(field_value, str):
            # Clean a single string value
            data[field] = field_value.strip()
        elif isinstance(field_value, dict):
            # For dictionary values, we could implement recursive cleaning if needed
            pass
            
        return data
    
    # Handle special case: input is None
    if input_data is None:
        return fallback
        
    result = None
    
    # Case 1: Dictionary of JSON strings
    if isinstance(input_data, dict) and any(isinstance(v, str) for v in input_data.values()):
        result = {}
        for key, value in input_data.items():
            parsed_value = parse_json_string(value)
            if parsed_value is not None:
                result[key] = clean_field_values(parsed_value, field_to_clean)
            else:
                logger.warning(f"Failed to parse JSON for key '{key}'")
                result[key] = fallback
    
    # Case 2: Single JSON string
    elif isinstance(input_data, str):
        result = parse_json_string(input_data)
        if result is not None and isinstance(result, dict):
            result = clean_field_values(result, field_to_clean)
    
    # Case 3: Already parsed JSON (dict/list)
    elif isinstance(input_data, (dict, list)):
        result = input_data
        # If it's a dictionary and has the field to clean, clean it
        if isinstance(result, dict):
            result = clean_field_values(result, field_to_clean)
    
    # Return the result or fallback
    return result if result is not None else fallback


# Example usage:
if __name__ == "__main__":
    # Case 1: Dictionary of JSON strings
    dict_example = {
        "risk1": '''```json
        {"keywords": ["political instability", "regime change ", "corruption"]}
        ```''',
        "risk2": '''```json
        {"keywords": ["tax policy", "tariffs ", "  regulatory framework"]}
        ```'''
    }
    
    # Clean the dictionary and specifically clean the "keywords" field
    cleaned_dict = clean_and_parse_json(dict_example, field_to_clean="keywords", fallback={})
    logger.info(f"Cleaned dictionary: {cleaned_dict}")
    