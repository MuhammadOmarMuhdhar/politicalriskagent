import json
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse(input_data, field_to_clean=None, fallback=None, recursive=True):
    """
    Cleans and parses JSON strings from various input formats:
    1. Dictionary of JSON strings (including nested dictionaries)
    2. Single JSON string
    3. Already parsed JSON (dict/list)
    4. Nested defaultdict structures with JSON string values
    
    Can optionally clean values within a specified field.
    
    Parameters:
    -----------
    input_data : str, dict, list, or defaultdict
        The input data to clean and parse
    field_to_clean : str or None
        If specified, values in this field will be cleaned (e.g., strip whitespace)
    fallback : Any
        Value to return if parsing fails
    recursive : bool
        Whether to recursively process nested dictionaries/defaultdicts
        
    Returns:
    --------
    dict, list, defaultdict, or fallback
        Parsed and cleaned JSON data if successful, else fallback. 
        Maintains the original structure but with parsed JSON objects.
    """
    # Define a nested function to handle the actual JSON parsing
    def parse_json_string(json_str):
        if not isinstance(json_str, str):
            return json_str  # Already parsed or not a string
            
        try:
            # Check if it's a JSON string with code block markers
            if '```json' in json_str:
                # Remove code block markers if present
                cleaned_str = json_str.strip()
                # Remove the starting ```json and ending ``` tags
                cleaned_str = cleaned_str.replace('```json\n', '').replace('\n```', '')
                cleaned_str = cleaned_str.strip()
                
                # Parse the JSON
                return json.loads(cleaned_str)
            else:
                # Try regular JSON parsing for other JSON strings
                cleaned_str = json_str.strip()
                for marker in ['```', '`']:
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
        
    # Handle defaultdict with specific default_factory types
    if isinstance(input_data, defaultdict):
        # Create a new defaultdict with the same default_factory
        result = defaultdict(input_data.default_factory)
        
        # Process each key-value pair
        for key, value in input_data.items():
            if isinstance(value, (dict, defaultdict)) and recursive:
                # Recursively process nested dictionaries/defaultdicts
                result[key] = parse(value, field_to_clean, fallback, recursive)
            elif isinstance(value, str) and ('```json' in value or value.strip().startswith('{')):
                # This is a JSON string
                parsed_value = parse_json_string(value)
                if parsed_value is not None:
                    result[key] = clean_field_values(parsed_value, field_to_clean)
                else:
                    logger.warning(f"Failed to parse JSON for key '{key}'")
                    result[key] = fallback
            else:
                # Keep other values as is
                result[key] = value
                
        return result
        
    # Case 1: Regular dictionary with potentially nested structures
    elif isinstance(input_data, dict):
        result = {}
        
        for key, value in input_data.items():
            if isinstance(value, (dict, defaultdict)) and recursive:
                # Recursively process nested dictionaries
                result[key] = parse(value, field_to_clean, fallback, recursive)
            elif isinstance(value, str) and ('```json' in value or value.strip().startswith('{')):
                # This is a JSON string
                parsed_value = parse_json_string(value)
                if parsed_value is not None:
                    result[key] = clean_field_values(parsed_value, field_to_clean)
                else:
                    logger.warning(f"Failed to parse JSON for key '{key}'")
                    result[key] = fallback
            else:
                # Keep other values as is
                result[key] = value
                
        return result
    
    # Case 2: Single JSON string
    elif isinstance(input_data, str):
        if '```json' in input_data or input_data.strip().startswith('{'):
            result = parse_json_string(input_data)
            if result is not None and isinstance(result, dict):
                result = clean_field_values(result, field_to_clean)
            return result if result is not None else fallback
        else:
            # Not a JSON string
            return input_data
    
    # Case 3: Already parsed JSON (list)
    elif isinstance(input_data, list):
        return input_data
    
    # Return fallback for unsupported types
    return fallback
    
    
def process_scenario_data(data):
    """
    A specialized function to process the specific scenario data structure from paste-2.txt.
    This function extracts and parses all the scenario JSON strings from the nested defaultdict structure.
    
    Parameters:
    -----------
    data : defaultdict
        The nested defaultdict structure containing JSON strings with scenarios
        
    Returns:
    --------
    defaultdict
        The same structure but with parsed JSON objects instead of JSON strings
    """
    logger.info("Processing scenario data...")
    
    # Use the generic function with specific settings for this data structure
    processed_data = parse(
        data, 
        field_to_clean="scenario",  # Clean the scenario field values if needed
        fallback={},                # Use empty dict as fallback for parsing errors
        recursive=True              # Process the structure recursively
    )
    
    logger.info("Scenario data processing completed")
    return processed_data

