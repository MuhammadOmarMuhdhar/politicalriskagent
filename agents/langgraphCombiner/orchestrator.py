import sys
import os
import logging
import json
import datetime
import uuid
from typing import Dict, List, Any, TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage
from agents.dataAgent.orchestrator import Orchestrator as DataOrchestrator
from agents.analysisAgent.orchestrator import Orchestrator as AnalysisOrchestrator
from agents.utils import pulseParser, contextExtractor
from data.azuredb import createContainer, insertData
import pandas as pd
from utils import email


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# State definition for the workflow
class PoliticalRiskState(TypedDict):
    user_data: Dict[str, Any]       # Input from user

    scenarios: Dict[str, Any]        # Data collection outputs
    articles: Dict[str, Any]        # Articles collected
    bigrams: List[Dict[str, Any]]   # Analysis outputs
    risk_scores: Dict[str, Any]     # Risk assessment scores
    report: Dict[str, Any]          # Final result
    risk_df: List[Dict[str, Any]]   # Organized risk dataframe
    category_df: List[Dict[str, Any]]  # Category aggregated data
    subcategory_df: List[Dict[str, Any]]  # Subcategory aggregated data
    top_subcategories: Dict[str, Any]  # Top subcategories with scores
    context: List[Dict[str, Any]]   # Extracted context data
    cosmos_db_info: Dict[str, Any]  # Information about the Cosmos DB storage
    status: str                     # Current status
    error: str                      # Error message (if any)
    next: str                       # Next node to execute


class LangGraphOrchestrator:
    """
    Orchestrates a political risk analysis workflow using LangGraph.
    The workflow consists of:
    1. A supervisor node that coordinates the workflow
    2. A data extraction node that collects data
    3. An analysis node that processes the data
    4. A report generation node that creates the final output
    
    Args:
        api_key (str): API key for the Gemini language model
        model_name (str, optional): Model to use. Defaults to "gemini-2.0-flash"
    """
    
    def __init__(self, api_key, key, model_name="gemini-2.0-flash"):
        """Initialize the orchestrator with API key and LLM."""
        self.api_key = api_key
        self.model_name = model_name
        self.graph = self._build_graph()
        self.key = key
        
            
    def _build_graph(self):
        """Build the workflow graph with nodes and edges."""
        logger.info("Building workflow graph")
        
        # Create workflow graph with our state type
        workflow = StateGraph(PoliticalRiskState)
        
        # Add nodes for each component
        workflow.add_node("supervisor", self.supervisor)
        workflow.add_node("data_extraction", self.data_extraction)
        workflow.add_node("data_analysis", self.data_analysis)
        workflow.add_node("report_generation", self.report_generation)
        
        # Define the basic flow structure
        workflow.add_edge(START, "supervisor")
        
        # Add conditional edges based on the "next" field
        workflow.add_conditional_edges(
            "supervisor",
            lambda x: x["next"],
            {
                "data_extraction": "data_extraction",
                "data_analysis": "data_analysis",
                "report_generation": "report_generation",
                END: END
            }
        )
        
        # Add edges from processing nodes back to supervisor
        workflow.add_edge("data_extraction", "supervisor")
        workflow.add_edge("data_analysis", "supervisor")
        workflow.add_edge("report_generation", "supervisor")
        
        # Compile and return
        return workflow.compile()
    
    def supervisor(self, state: PoliticalRiskState) -> Dict[str, Any]:
        """
        Central coordination node that determines next steps in the workflow.
        Routes tasks to appropriate nodes based on current state.
        """
        logger.info("Supervisor: Evaluating current state")
        
        # Create a copy of the state to modify
        new_state = {
            "next": "",
            "status": state.get("status", "")
        }
        
        # Handle different states
        if state.get("status") == "initialized":
            # Initial state - route to data extraction
            logger.info("Supervisor: Routing to Data Extraction")
            new_state["next"] = "data_extraction"
            new_state["status"] = "extracting_data"
            
        elif state.get("status") == "data_extraction_complete":
            # Data extraction complete - route to analysis
            logger.info("Supervisor: Data extraction complete, routing to Analysis")
            new_state["next"] = "data_analysis"
            new_state["status"] = "analyzing_data"
            
        elif state.get("status") == "data_analysis_complete":
            # Analysis complete - route to report generation
            logger.info("Supervisor: Analysis complete, routing to Report Generation")
            new_state["next"] = "report_generation"
            new_state["status"] = "generating_report"
            
        elif state.get("status") == "report_generation_complete":
            # Report generation complete - workflow finished
            logger.info("Supervisor: Report generation complete, ending workflow")
            new_state["next"] = END
            new_state["status"] = "completed"
            
        elif state.get("status") == "error":
            # Error occurred - end workflow
            logger.error(f"Supervisor: Error encountered: {state.get('error')}")
            new_state["next"] = END
            
        else:
            # Default case - unhandled state
            logger.warning(f"Supervisor: Unhandled state: {state.get('status')}")
            new_state["next"] = END
            
        return new_state
    
    def data_extraction(self, state: PoliticalRiskState) -> Dict[str, Any]:
        """
        Data extraction node that collects articles and keywords.
        """
        logger.info("Data Extraction: Starting data collection process")
        logger.info(f"Processing user data: {json.dumps(state.get('user_data', {}), indent=2)}")
        
        # Create a focused state update
        new_state = {
            "status": "",
            "error": ""
        }
        
        try:
            user_data = state.get("user_data", {})
            
            # Collect data using the data agent
            logger.info("Data Extraction: Initializing data agent")
            data_agent = DataOrchestrator(
                api_key=self.api_key, 
                user_data=user_data,
                domains = [
                    "reuters.com",
                    "apnews.com",
                    "theguardian.com",
                    "aljazeera.com",
                    "france24.com",
                    "scmp.com",
                    "businessinsider.com"
                ]
            )
            
            logger.info("Data Extraction: Running data collection")
            scenarios, articles_dict = data_agent.run()
            
            # Log data collection results
            logger.info("Data Collection Results:")
            logger.info(f"Generated Keywords: {len(scenarios)} risk categories")
            logger.info(f"Number of articles found: {len(articles_dict)}")
            
            # Update state with results
            new_state["scenarios"] = scenarios
            new_state["articles"] = articles_dict
            new_state["status"] = "data_extraction_complete"
            
            logger.info("Data Extraction: Data collection completed successfully")
            
        except Exception as e:
            logger.error(f"Data Extraction: Error during data collection: {str(e)}")
            logger.error("Full error traceback:", exc_info=True)
            new_state["status"] = "error"
            new_state["error"] = f"Data extraction error: {str(e)}"
            
        return new_state
    
    def data_analysis(self, state: PoliticalRiskState) -> Dict[str, Any]:
        """
        Data analysis node that processes collected data and performs bigram analysis.
        """
        logger.info("Data Analysis: Starting analysis process")
        
        # Create a focused state update
        new_state = {
            "status": "",
            "error": ""
        }
        
        try:
            user_data = state.get("user_data", {})
            articles_dict = state.get("articles", {})
            
            # Verify we have the data needed
            if not articles_dict:
                raise ValueError("No articles available for analysis. Data extraction may have failed.")
            
            # Analyze the collected data
            logger.info("Data Analysis: Initializing analysis agent")
            analysis_agent = AnalysisOrchestrator(
                api_key=self.api_key, 
                user_data=user_data,
                articles_dict=articles_dict
            )
            
            logger.info("Data Analysis: Running analysis")
            bigrams, risk_scores  = analysis_agent.run()
            
            # Log analysis results
            logger.info("Analysis Results:")
            logger.info(f"Risk Scores: {len(risk_scores)} countries analyzed")
            
            # Organize risk scores using pulseParser utility
            logger.info("Data Analysis: Organizing risk scores with pulseParser")
            
            risk_df, category_df, subcategory_df, keyword_df = pulseParser.organize_risk_scores(risk_scores)
            
            # Aggregate by category and sort
            category_df_agg = category_df.groupby("Category").agg({"Score": "mean"}).sort_values(by="Score", ascending=False)
            
            # Aggregate by subcategory and sort
            subcategory_df_agg = subcategory_df.groupby("Subcategory").agg({"Score": "mean"}).sort_values(by="Score", ascending=False)
            
            # Get top subcategories
            top_subcategories = subcategory_df_agg.head(3)
            top_subcategories_scores = top_subcategories['Score'].to_dict()
            top_subcategories_list = top_subcategories.index.tolist()
            
            # Log the organized risk scores
            logger.info(f"Data Analysis: Organized Risk Scores: {len(risk_df)} entries")
            logger.info(f"Data Analysis: Top Risk Categories: {category_df_agg.head(3).index.tolist()}")
            logger.info(f"Data Analysis: Top Risk Subcategories: {top_subcategories_list}")
            
            # Store data in Azure Cosmos DB
            # Create a unique container name based on timestamp and UUID
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            container_name = f"risk_analysis_{timestamp}_{unique_id}"
            
            logger.info(f"Data Analysis: Initializing Cosmos DB connection with container: {container_name}")
            
            # Initialize the Cosmos client
            endpoint = "https://poli-sci-risk.documents.azure.com:443//"
            key = self.key
            database_name = "poli-sci-risk"
            
            # Create or get a database and container
            client, database, container = createContainer.initialize_cosmos_client(
                endpoint, key, database_name, container_name
            )
            
            # Insert articles into Cosmos DB
            logger.info("Data Analysis: Inserting articles into Cosmos DB")
            inserted_ids = insertData.insert_articles_to_cosmos(container, articles_dict)
            logger.info(f"Data Analysis: Inserted {len(inserted_ids)} articles into Cosmos DB")
            
            # # Insert risk scores into Cosmos DB
            # logger.info("Data Analysis: Inserting risk scores into Cosmos DB")
            # risk_items = []
            # for country, scores in risk_scores.items():
            #     item = {
            #         "id": f"risk_{country}_{timestamp}_{unique_id}",
            #         "country": country,
            #         "scores": scores,
            #         "timestamp": datetime.datetime.now().isoformat(),
            #         "analysis_id": unique_id
            #     }
            #     risk_items.append(item)
            
            # Using a helper function to insert risk scores
            # risk_score_ids = insertData.insert_articles_to_cosmos(container, risk_items)
            # logger.info(f"Data Analysis: Inserted {len(risk_score_ids)} risk score items into Cosmos DB")
            
            # Extract context using contextExtractor
            logger.info("Data Analysis: Extracting context for top subcategories")

            # Initialize context extractor
            scenarios = state.get("scenarios", {})
            
            # Extract context using contextExtractor
            context = contextExtractor.extract(scenarios, top_subcategories_list, container)
            logger.info(f"Data Analysis: Extracted {len(context)} context items")
            
            # Add organized data to state
            new_state["risk_df"] = risk_df.to_dict('records')
            new_state["category_df"] = category_df_agg.reset_index().to_dict('records')
            new_state["subcategory_df"] = subcategory_df.to_dict('records')
            new_state["top_subcategories"] = {
                "list": top_subcategories_list,
                "scores": top_subcategories_scores
            }
            new_state["context"] = context
            new_state["keyword_df"] = keyword_df.to_dict('records') if keyword_df is not None else []
            
            # Add database info to state
            new_state["cosmos_db_info"] = {
                "endpoint": endpoint,
                "database_name": database_name,
                "container_name": container_name,
                "articles_inserted": len(inserted_ids),
                # "risk_scores_inserted": len(risk_scores)
            }
            
            # Update state with results
            new_state["risk_scores"] = risk_scores
            new_state["status"] = "data_analysis_complete"
            
            logger.info("Data Analysis: Analysis process completed successfully")
            
        except Exception as e:
            logger.error(f"Data Analysis: Error during analysis: {str(e)}")
            logger.error("Full error traceback:", exc_info=True)
            new_state["status"] = "error"
            new_state["error"] = f"Data analysis error: {str(e)}"
            
        return new_state
    
    def report_generation(self, state: PoliticalRiskState) -> Dict[str, Any]:
        """
        Report generation node that creates the final political risk report.
        """
        logger.info("Report Generation: Starting report creation process")
        
        # Create a focused state update
        new_state = {
            "status": "",
            "error": ""
        }
        
        try:
            # Verify we have the necessary data
            user_data = state.get("user_data", {})
            context = state.get("context", [])
            top_subcategories = state.get("top_subcategories", {})
            
            if not context or not top_subcategories:
                raise ValueError("Missing required data for report generation.")
            
            logger.info("Report Generation: Generating final report")
            from agents.reportAgent import orchestrator

            subcategory_df_df = state.get("subcategory_df", [])
            subcategory_df_df = pd.DataFrame(subcategory_df_df)
            
            
            # Initialize the report agent
            report_agent = orchestrator.Orchestrator(
                api_key=self.api_key,
                subcategories=context,
                user_data=user_data,
                subcategories_scores=top_subcategories.get("scores", {}),
                visuals_df=subcategory_df_df,  
                column_visual="Subcategory",
            )
            
            # Set methodology information
            report_agent.set_methodology(
                description="This report uses a multi-factor analytical model that combines quantitative indices with qualitative assessment to evaluate political risk factors.",
                data_sources="Data sources include government publications, economic indicators, news media analysis, and expert interviews conducted between January and April 2025.",
                disclaimer="This assessment represents a forecast based on currently available information and should not be considered a guarantee of future political conditions."
            )
            
            # Set metadata
            report_agent.set_metadata(assessment_period="24-Month Forecast")
            
            # Generate the report
            logger.info("Report Generation: Creating HTML report")
            report_html = report_agent.create_report()
            logger.info(f"Report Generation: Generated report with {len(report_html)} characters")
            
            # Save the report to a file for reference (optional)
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            file_path = f"reports/risk_report_{timestamp}.html"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            new_state["report"] = {"html": report_html}
            logger.info("Report Generation: Report creation completed successfully")

            # Send the report via email (optional)
            recipient_email = user_data.get("email")
            if recipient_email:
                logger.info(f"Report Generation: Sending report to {recipient_email}")
                email_subject = "Political Risk Analysis Report"
                email_body = f"Please find attached your political risk analysis report.\n\nBest regards,\nPolitical Risk Analysis Team"
                
                # Send the email with the report
                email_sent = email.send(
                    subject=email_subject,
                    body=email_body,
                    recipient_email=recipient_email,
                    html_attachment=report_html
                )
                
                if email_sent:
                    logger.info("Report Generation: Email sent successfully")
                else:
                    logger.error("Report Generation: Failed to send email")

              # Update state with results
          
            new_state["status"] = "report_generation_complete"


            
        except Exception as e:
            logger.error(f"Report Generation: Error during report creation: {str(e)}")
            logger.error("Full error traceback:", exc_info=True)
            new_state["status"] = "error"
            new_state["error"] = f"Report generation error: {str(e)}"
            
        return new_state
    

    
    def run(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the full political risk analysis workflow.
        
        Args:
            user_data (Dict[str, Any]): User profile and query information
            
        Returns:
            Dict[str, Any]: Final state with research results
        """
        logger.info("Starting political risk analysis workflow")
        
        # Initialize state
        initial_state = {
            "user_data": user_data,
            "keywords": {},
            "articles": {},
            "bigrams": [],
            "risk_scores": {},
            "report": {},
            "risk_df": [],
            "category_df": [],
            "subcategory_df": [],
            "top_subcategories": {},
            "context": [],
            "cosmos_db_info": {},
            "status": "initialized",
            "error": "",
            "next": ""
        }
        
        try:
            # Set execution configuration
            config = {"recursion_limit": 25}  # Add a recursion limit to prevent infinite loops
            
            # Invoke the workflow with initial state
            final_state = self.graph.invoke(initial_state, config=config)
            logger.info("Workflow completed successfully")
            return final_state
        except Exception as e:
            logger.error(f"Error during workflow execution: {str(e)}")
            return {
                "user_data": user_data,
                "status": "error",
                "error": str(e)
            }
    
    def print_execution_trace(self, trace):
        """Print a human-readable version of the execution trace."""
        if not trace or "execution_trace" not in trace:
            print("No valid trace provided")
            return
            
        trace_data = trace["execution_trace"]
        
        print("\n=== EXECUTION TRACE ===\n")
        
        for i, step in enumerate(trace_data):
            print(f"\n--- Step {i+1}: {step['node']} ---")
            
            # Print input state (simplified)
            print("\nInput:")
            self._print_simplified_state(step['input'])
            
            # Print output state (simplified)
            print("\nOutput:")
            self._print_simplified_state(step['output'])
            
            print("\n" + "-" * 50)
        
    def _print_simplified_state(self, state):
        """Helper method to print a simplified version of the state."""
        if isinstance(state, dict):
            for key, value in state.items():
                if key in ["user_data", "error", "status", "next"]:
                    print(f"  {key}: {value}")
                elif key in ["keywords", "articles", "risk_scores"]:
                    if value:
                        print(f"  {key}: [Data present with {len(value)} items]")
                    else:
                        print(f"  {key}: [Empty]")