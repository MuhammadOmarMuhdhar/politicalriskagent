# Add this at the top of the file
import sys
import os
import time
from contextlib import contextmanager
import signal
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import io
import logging

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


import streamlit as st
import json
from apisecrets import geminapi
from agents.langgraphCombiner.LangGraph import LangGraphOrchestrator
from langchain_google_genai import ChatGoogleGenerativeAI
import pandas as pd
import plotly.express as px

# Create a string buffer to capture logs
log_stream = io.StringIO()
# Add a stream handler to the logger
stream_handler = logging.StreamHandler(log_stream)
logging.getLogger().addHandler(stream_handler)

@contextmanager
def timeout(seconds):
    def signal_handler(signum, frame):
        raise TimeoutError("Analysis timed out")
    
    # Set the signal handler and a timeout
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        signal.alarm(0)

def run_visualizer():
    st.title("Political Risk Analysis Agent Visualizer")
    
    # Display graph structure first
    st.header("Agent Workflow Structure")
    st.json({
        "nodes": ["START", "supervisor", "research_team", "END"],
        "edges": {
            "START": ["supervisor"],
            "supervisor": ["research_team", "END"],
            "research_team": ["supervisor"]
        }
    })
    
    # Input user data section
    st.header("User Data Input")
    with st.form("user_data_form"):
        # API Key input at the top of the form
        api_key = geminapi.api_key  # Default from secrets
        user_api_key = st.text_input("Enter your Gemini API Key (optional):", type="password")
        
        # Rest of the form inputs
        investor_type = st.text_input("Investor Type:", value="private equity firm")
        location = st.text_input("Your Location:", value="United States") 
        investment_sectors = st.text_input("Investment Sectors:", value="renewable energy, manufacturing")
        target_locations = st.text_input("Target Locations:", value="Brazil, Indonesia")
        investment_objective = st.text_area("Investment Objective:", value="acquire majority stakes in mid-sized companies")
        analysis_motivation = st.text_input("Analysis Motivation:", value="pre-investment due diligence")
        risk_experience = st.select_slider("Risk Experience:", options=["minimal", "moderate", "extensive"], value="moderate")
        timeline = st.text_input("Timeline:", value="6-12 months")
        investment_scale = st.text_input("Investment Scale:", value="$50-100 million per deal")
        risk_tolerance = st.select_slider("Risk Tolerance:", options=["low", "moderate", "high"], value="moderate")
        esg = st.select_slider("ESG Importance:", options=["not important", "somewhat important", "very important"], value="very important")
        primary_concerns = st.text_input("Primary Concerns:", value="regulatory and political stability")
        additional_info = st.text_area("Additional Information:", value="Particularly interested in policy changes related to foreign investment")
        
        submitted = st.form_submit_button("Run Analysis")
    
    # Only process when form is submitted
    if submitted:
        # Use user-provided API key if given, otherwise use default
        final_api_key = user_api_key if user_api_key else api_key
        
        if not final_api_key:
            st.error("Please provide an API key")
            return
            
        # Validate API key and run analysis
        with st.spinner("Validating API key and initializing..."):
            try:
                # Test API key
                test_llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    google_api_key=final_api_key
                )
                test_response = test_llm.invoke("Hello")
                
                # Create orchestrator
                orchestrator = LangGraphOrchestrator(api_key=final_api_key)
                
                # Prepare user data
                user_data = {
                    "investor_type": investor_type,
                    "location": location,
                    "investment_sectors": investment_sectors,
                    "target_locations": target_locations,
                    "investment_objective": investment_objective,
                    "analysis_motivation": analysis_motivation,
                    "risk_experience": risk_experience,
                    "timeline": timeline,
                    "investment_scale": investment_scale,
                    "risk_tolerance": risk_tolerance,
                    "esg": esg,
                    "primary_concerns": primary_concerns,
                    "additional_info": additional_info
                }
                
                # Add a placeholder for logs
                log_display = st.empty()
                
                # Run analysis
                with st.spinner("Running political risk analysis..."):
                    try:
                        with ThreadPoolExecutor() as executor:
                            future = executor.submit(orchestrator.run, user_data)
                            while not future.done():
                                # Update logs every second
                                log_display.code(log_stream.getvalue(), language="text")
                                time.sleep(1)
                            final_state = future.result(timeout=300)  # 5 minutes timeout
                            # Final log update
                            log_display.code(log_stream.getvalue(), language="text")
                    except TimeoutError:
                        st.error("Analysis timed out after 5 minutes. Please try again.")
                        return
                    
                    # Display the execution flow
                    st.header("Execution Flow")
                    
                    # Display initial state
                    with st.expander("Initial State"):
                        st.json({
                            "state": "initialized",
                            "user_data": user_data
                        })
                    
                    # Display research team results
                    with st.expander("Research Team Results"):
                        st.subheader("Keywords")
                        st.json(final_state.get("keywords", {}))
                        
                        st.subheader("Articles")
                        st.json(final_state.get("articles", {}))
                        
                        st.subheader("Risk Scores")
                        risk_scores = final_state.get("risk_scores", {})
                        if risk_scores:
                            st.bar_chart(risk_scores)
                        else:
                            st.warning("No risk scores were generated.")
                    
                    # Display final state
                    with st.expander("Final State"):
                        st.json({
                            "status": final_state.get("status", "unknown"),
                            "error": final_state.get("error", ""),
                            "risk_scores": final_state.get("risk_scores", {})
                        })
                    
                    # Display summary
                    st.header("Analysis Summary")
                    if final_state.get("status") == "research_complete":
                        st.success("Analysis completed successfully!")
                        
                        # Display risk scores in a more visual way
                        if risk_scores:
                            st.subheader("Risk Assessment")
                            
                            # Convert risk scores to a format suitable for visualization
                            risk_data = pd.DataFrame({
                                'Risk Category': list(risk_scores.keys()),
                                'Risk Score': list(risk_scores.values())
                            })
                            
                            # Create a bar chart
                            fig = px.bar(risk_data, 
                                       x='Risk Category', 
                                       y='Risk Score',
                                       title='Political Risk Assessment Results')
                            st.plotly_chart(fig)
                            
                            # Add textual summary
                            st.subheader("Key Findings")
                            for category, score in risk_scores.items():
                                risk_level = "High" if score > 0.7 else "Medium" if score > 0.4 else "Low"
                                st.write(f"- **{category}**: {risk_level} risk (score: {score:.2f})")
                    else:
                        st.error(f"Analysis ended with status: {final_state.get('status')}")
                        if final_state.get('error'):
                            st.error(f"Error: {final_state.get('error')}")
                            
            except Exception as e:
                st.error(f"Error initializing API: {str(e)}")

if __name__ == "__main__":
    run_visualizer() 