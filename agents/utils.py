import json 
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_and_parse_json(dictionary, fallback=None):
    """
    Cleans and parses a string output as a JSON object. Returns a value from the JSON
    or falls back if parsing fails.

    Parameters:
    -----------
    output : str
        The string output to clean and parse
    fallback : Any
        Value to return if parsing fails

    Returns:
    --------
    str or fallback
        Parsed JSON value from key `"title"` if successful, else fallback or raw output
    """

    cleaned_data = {}

    if not isinstance(dictionary, str):

        for key, value in dictionary.items():
            try:
                # Remove the ```json markers and extra whitespace
                cleaned_value = value.strip().lstrip('```json').rstrip('```').strip()
                
                # Parse the JSON content
                parsed_value = json.loads(cleaned_value)
                
                # clean the keywords (e.g., strip whitespace from each keyword)
                parsed_value['keywords'] = [keyword.strip() for keyword in parsed_value['keywords']]
                
                # Add the cleaned entry to the new dictionary
                cleaned_data[key] = parsed_value
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON for key '{key}': {e}")
            except Exception as e:
                print(f"Unexpected error for key '{key}': {e}")

    else:
        try:
            # Remove the ```json markers and extra whitespace
            cleaned_value = dictionary.strip().lstrip('```json').rstrip('```').strip()
            
            # Parse the JSON content
            parsed_value = json.loads(cleaned_value)
            
            # clean the keywords (e.g., strip whitespace from each keyword)
            parsed_value['keywords'] = [keyword.strip() for keyword in parsed_value['keywords']]
            
            # Add the cleaned entry to the new dictionary
            cleaned_data = parsed_value
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    return cleaned_data
