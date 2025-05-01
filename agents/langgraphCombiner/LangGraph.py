# Add this at the top of the file
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Set API key here: 
os.environ["GEMINI_API_KEY"] = "AIzaSyCsyyClTLHUfvVesjKRkSvezgmMRAOTzl0"

# Import necessary libraries
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from typing import Dict, List, Any, TypedDict, Annotated, Literal, Union
import json
from IPython.display import display, HTML
from langchain_core.messages import HumanMessage, SystemMessage

# Import our existing agents
from agents.dataAgent.orchestrator import Orchestrator as DataOrchestrator
from agents.analysisAgent.orchestrator import Orchestrator as AnalysisOrchestrator

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# State definition
class PoliticalRiskState(TypedDict):
    # Input from user
    user_data: Dict[str, Any]
    # Data collection outputs
    keywords: Dict[str, Any]
    articles: Dict[str, Any]
    # Analysis outputs
    bigrams: List[Dict[str, Any]]
    risk_scores: Dict[str, Any]
    # Final result
    report: Dict[str, Any]
    # Control flow
    status: str
    error: str
    next: str

# Initialize the Google AI LLM
def init_llm(api_key, model_name="gemini-2.0-flash"):
    if not api_key:
        raise ValueError("API key cannot be empty")
        
    try:
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.7,
            convert_system_message_to_human=True
        )
    except Exception as e:
        logger.error(f"Error initializing ChatGoogleGenerativeAI: {str(e)}")
        raise

class LangGraphOrchestrator:
    def __init__(self, api_key):
        """Initialize the LangGraph orchestrator with API key."""
        self.api_key = api_key
        self.llm = init_llm(api_key)
        # Initialize the graph
        self.graph = self._build_graph()
        
    def _build_graph(self):
        """Build the LangGraph with all nodes and edges."""
        
        # Create workflow graph
        workflow = StateGraph(PoliticalRiskState)
        
        # Add nodes
        workflow.add_node("supervisor", self.supervisor)
        workflow.add_node("research_team", self.research_team)
        
        # Define edges
        workflow.add_edge(START, "supervisor")
        workflow.add_edge("supervisor", "research_team")
        workflow.add_edge("research_team", "supervisor")
        workflow.add_edge("supervisor", END)
        
        # Compile the graph
        return workflow.compile()
    
    def supervisor(self, state: PoliticalRiskState) -> PoliticalRiskState:
        """
        Central coordination node that determines the next steps in the workflow.
        This node routes tasks to appropriate teams based on the current state.
        """
        logger.info("Supervisor: Evaluating current state")
        
        # Initial state - just received user data
        if state.get("status") == "initialized":
            logger.info("Supervisor: Routing to Research Team for data collection and analysis")
            new_state = state.copy()
            new_state["next"] = "research_team"
            new_state["status"] = "collecting_data"
            return new_state
            
        # Data collection and analysis complete
        elif state.get("status") == "research_complete":
            # In a full implementation, we would route to the Document Authoring team next
            # For now, we'll just end the workflow
            logger.info("Supervisor: Research complete, ending workflow")
            new_state = state.copy()
            new_state["next"] = END
            return new_state
            
        # Error occurred
        elif state.get("status") == "error":
            logger.error(f"Supervisor: Error encountered: {state.get('error')}")
            new_state = state.copy()
            new_state["next"] = END
            return new_state
            
        # Default case
        else:
            logger.warning(f"Supervisor: Unhandled state: {state.get('status')}")
            new_state = state.copy()
            new_state["next"] = END
            return new_state
    
    def research_team(self, state: PoliticalRiskState) -> PoliticalRiskState:
        """
        Research team node that integrates data collection and analysis.
        Uses both dataAgent and analysisAgent to gather and process information.
        """
        logger.info("Research Team: Starting research process")
        logger.info(f"Processing user data: {json.dumps(state.get('user_data', {}), indent=2)}")
        
        try:
            user_data = state.get("user_data", {})
            
            # Initialize the data agent
            logger.info("Research Team: Initializing data agent")
            logger.info(f"Using domains: reuters.com, theguardian.com, nytimes.com, wsj.com, bloomberg.com, ft.com")
            data_agent = DataOrchestrator(api_key=self.api_key, user_data=user_data, domains=["reuters.com", "theguardian.com", "nytimes.com", "wsj.com", "bloomberg.com", "ft.com"])
            
            # Run data collection
            logger.info("Research Team: Running data collection")
            results, articles_dict = data_agent.run()
            
            # Log the results from data collection
            logger.info("Data Collection Results:")
            logger.info(f"Generated Keywords: {json.dumps(results, indent=2)}")
            logger.info(f"Number of articles found: {len(articles_dict)}")
            for url, article in articles_dict.items():
                logger.info(f"Article from {url}:")
                logger.info(f"- Title: {article.get('title', 'No title')}")
                logger.info(f"- Date: {article.get('date', 'No date')}")
            
            # Initialize the analysis agent
            logger.info("Research Team: Initializing analysis agent")
            analysis_agent = AnalysisOrchestrator(
                api_key=self.api_key, 
                user_data=user_data,
                articles_dict=articles_dict
            )
            
            # Run analysis
            logger.info("Research Team: Running analysis")
            risk_scores = analysis_agent.run()
            
            # Log the analysis results
            logger.info("Analysis Results:")
            logger.info(f"Risk Scores: {json.dumps(risk_scores, indent=2)}")
            
            # Update state with results
            new_state = state.copy()
            new_state["keywords"] = results
            new_state["articles"] = articles_dict
            new_state["risk_scores"] = risk_scores
            new_state["status"] = "research_complete"
            
            logger.info("Research Team: Research process completed successfully")
            logger.info(f"Final state status: {new_state['status']}")
            return new_state
            
        except Exception as e:
            logger.error(f"Research Team: Error during research: {str(e)}")
            logger.error(f"Full error traceback:", exc_info=True)
            new_state = state.copy()
            new_state["status"] = "error"
            new_state["error"] = str(e)
            return new_state
    
    def run(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the entire LangGraph workflow with user data.
        
        Parameters:
        -----------
        user_data : Dict[str, Any]
            User profile and query information
            
        Returns:
        --------
        Dict[str, Any]
            Final state containing research results and execution information
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
            "status": "initialized",
            "error": "",
            "next": ""
        }
        
        try:
            final_state = self.graph.invoke(initial_state)
            logger.info("Workflow completed successfully")
            return final_state
        except Exception as e:
            logger.error(f"Error during workflow execution: {str(e)}")
            return {
                "user_data": user_data,
                "status": "error",
                "error": str(e)
            }

    def visualize(self):
        """
        Visualize the LangGraph structure in a notebook.
        Returns the HTML representation that can be displayed.
        """
        try:
            # Get the graph structure as a dictionary
            graph_data = self.graph.get_graph()
            
            # Convert to JSON for display
            graph_json = json.dumps(graph_data, indent=2)
            
            # Create HTML representation - note the triple quotes
            html = f"""
            <h3>Political Risk Analysis Workflow</h3>
            <div id="graph-viz"></div>
            <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
            <script>
                const graphData = {graph_json};
                
                // Create visualization
                const width = 800;
                const height = 600;
                
                const svg = d3.select("#graph-viz")
                    .append("svg")
                    .attr("width", width)
                    .attr("height", height);
                
                // Create force simulation
                const simulation = d3.forceSimulation(Object.keys(graphData.nodes).map(id => ({{id}})))
                    .force("link", d3.forceLink(
                        Object.entries(graphData.edges).flatMap(([source, targets]) => 
                            targets.map(target => ({{source, target}}))
                        )
                    ).id(d => d.id))
                    .force("charge", d3.forceManyBody().strength(-400))
                    .force("center", d3.forceCenter(width / 2, height / 2));
                
                // Draw links
                const link = svg.append("g")
                    .selectAll("line")
                    .data(Object.entries(graphData.edges).flatMap(([source, targets]) => 
                        targets.map(target => ({{source, target}}))
                    ))
                    .enter().append("line")
                    .attr("stroke", "#999")
                    .attr("stroke-width", 2);
                
                // Draw nodes
                const node = svg.append("g")
                    .selectAll("circle")
                    .data(Object.keys(graphData.nodes).map(id => ({{id}})))
                    .enter().append("g");
                
                node.append("circle")
                    .attr("r", 20)
                    .attr("fill", d => d.id === "START" ? "#4CAF50" : 
                                    d.id === "END" ? "#F44336" : "#2196F3");
                
                node.append("text")
                    .text(d => d.id)
                    .attr("text-anchor", "middle")
                    .attr("dy", 5)
                    .attr("fill", "white");
                
                // Update positions
                simulation.on("tick", () => {{
                    link
                        .attr("x1", d => d.source.x)
                        .attr("y1", d => d.source.y)
                        .attr("x2", d => d.target.x)
                        .attr("y2", d => d.target.y);
                    
                    node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
                }});
            </script>
            """
            
            return HTML(html)
        except Exception as e:
            logger.error(f"Error visualizing graph: {str(e)}")
            return f"Error visualizing graph: {str(e)}"
    
    def print_execution_trace(self, trace):
        """
        Print a human-readable version of the execution trace.
        
        Parameters:
        -----------
        trace : dict
            Execution trace from run_with_tracing
        """
        if not trace or "execution_trace" not in trace:
            print("No valid trace provided")
            return
            
        trace_data = trace["execution_trace"]
        
        print("\n=== EXECUTION TRACE ===\n")
        
        for i, step in enumerate(trace_data):
            print(f"\n--- Step {i+1}: {step['node']} ---")
            
            # Print input state (simplified)
            print("\nInput:")
            input_state = step['input']
            self._print_simplified_state(input_state)
            
            # Print output state (simplified)
            print("\nOutput:")
            output_state = step['output']
            self._print_simplified_state(output_state)
            
            print("\n" + "-" * 50)
            
    def _print_simplified_state(self, state):
        """Helper method to print a simplified version of the state"""
        if isinstance(state, dict):
            for key, value in state.items():
                if key in ["user_data", "error", "status", "next"]:
                    print(f"  {key}: {value}")
                elif key in ["keywords", "articles", "risk_scores"]:
                    if value:
                        print(f"  {key}: [Data present with {len(value)} items]")
                    else:
                        print(f"  {key}: [Empty]")




