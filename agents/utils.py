import json
import logging

logger = logging.getLogger(__name__)

def clean_and_parse_json(output, fallback=None):
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
    if not isinstance(output, str):
        return fallback

    try:
        cleaned = output.strip().lstrip('```json').rstrip('```').strip()
        parsed = json.loads(cleaned)
        return parsed.get("title", fallback)
    except Exception as e:
        logger.error(f"Error parsing JSON output: {str(e)}\nRaw output: {output}")
        return fallback or output
