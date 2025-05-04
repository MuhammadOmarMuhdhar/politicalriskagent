from dotenv import load_dotenv
import os
import json
import sys

# attach directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from agents.langgraphCombiner import orchestrator



load_dotenv()

api_key = os.getenv("gemini_api_key")
key = os.getenv("azure_db_key")

def main(user_data):
    orchestrator_agent = orchestrator.LangGraphOrchestrator(api_key=api_key, key=key)
    results = orchestrator_agent.run(user_data=user_data)
    print("Finished running agent.")
    return results


