import streamlit as st 
import pycountry
import time
import pandas as pd
import plotly.express as px
import io
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor

# Add logging configuration at the top of main.py
log_stream = io.StringIO()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(log_stream),
        logging.StreamHandler(sys.stdout)  # Also print to console
    ]
)

# Initialize session state variables if they don't exist
if 'page' not in st.session_state:
    st.session_state.page = 0

if 'email' not in st.session_state:
    st.session_state.email = ""

if 'target_locations' not in st.session_state:
    st.session_state.target_locations = []  # Initialize as empty list

# Functions to navigate between pages
def next_page():
    st.session_state.page += 1
    st.rerun()

def prev_page():
    st.session_state.page -= 1
    st.rerun()

# Page 0: Welcome and Email Collection
if st.session_state.page == 0:

    st.markdown(" ")
    st.markdown(" ")
    st.markdown(" ")
    st.markdown(" ")
    st.markdown(" ")
    st.markdown(" ")

    st.markdown("### Political Risk Analysis Agent")

    st.markdown("""
    
        This tool uses Agentic AI to assess political risks that could impact operations, investments, and strategic decisions across global markets.

        Our ontology combines diverse data sources, organizing them to map relationships between key elements. This creates a comprehensive view of political landscapes, enabling thorough risk assessment, factor breakdown, and opportunity analysis.

        ##### How It Works

        The process is simple:
        1. Complete a brief survey about your interests and objectives
        2. Describe the event or decision you need political risk analysis for

        ##### What You'll Receive

        Based on your input, our agents extract relevant data, perform inidvidualized analysis, and deliver:
        - **Early Warning Index**: Highlighting emerging risks
        - **Detailed Report**: Outlining political scenarios that might affect your interests and their probability of occuring

       
    """)

# Important Note

# This project was created as a submission for the Microsoft Agentic AI Hackathon. While it leverages innovative approaches and draws on real-world data and machine learning techniques used in professional political risk analysis, it should be considered a proof of concept rather than definitive advice.

# We encourage you to use our analysis as one of many tools in your decision-making process.
                
    
    st.markdown("To get started, please enter your email address below.")
    email = st.text_input("Enter your email address:", value=st.session_state.email)
    
    if st.button("Next", key="email_next"):
            if email and "@" in email and "." in email:
                st.session_state.email = email
                next_page() 
            else:
                st.error("Please enter a valid email address.")

# page 1 : Survey 
elif st.session_state.page == 1:

    st.title("Survey")

    st.markdown("""
    We'll ask a few questions to better understand your investment objectives. We only ask for general information needed for analysis. 
    No specific or proprietary details are required. At our current development stage, we've deliberately limited what we collect. 
    Our system works effectively without needing sensitive details about your actual plans or business.
    """)
   
    # Page header with attractive styling
    st.markdown("### Profile Details")
    
    # Introduction and context explanation
    st.markdown("""
    Political factors influence investments differently based on your objectives and situation.

    This profile helps us understand key aspects like your investment horizon, risk tolerance, and areas of interest.

    Please complete all fields below to proceed.
    """)
    
    # Create two columns for better layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Investor Type Selection
        if 'investor_type' not in st.session_state:
            st.session_state.investor_type = "Select"
        
        st.markdown("##### Investor Type")
        industry_tooltip = "Your classification helps us tailor our analysis to your specific needs"
        investor_type = st.selectbox(
            "Which best describes you?",
            options=["Select", "Individual Investor", "Institutional Investor", "Business Executive", "Other"],
            help=industry_tooltip
        )
        
        # Show text input field if "Other" is selected
        if investor_type == "Other":
            other_investor_type = st.text_input("Please specify your investor type:")
        
        # Location
        if 'location' not in st.session_state:
            st.session_state.location = "Select Region"
        
        st.markdown("##### Location")
        # Get all country names
        all_countries = sorted([country.name for country in pycountry.countries if country.name != "United States"])
        # Add United States at the top
        country_names = ["Select Country"]+["United States"] + all_countries
        location_tooltip = "Your home base influences your exposure to domestic political risks"
        location = st.selectbox(
            "What is your geographic location?",
            options=country_names,
            help=location_tooltip
        )
        
        # Investment Sectors
        if 'investment_sectors' not in st.session_state:
            st.session_state.investment_sectors = "Select Sector"
        
        st.markdown("##### Investment Sectors")
        sectors_tooltip = "Different sectors have varying levels of political risk exposure"
        investment_sectors = st.multiselect(
            label = "Which sectors are you interested in?",
            options=["Agriculture", "Energy", "Finance", "Healthcare", "Consumer goods", "Manufacturing", "Infrastructure", "Technology", "Real Estate", "Other"],
            help=sectors_tooltip
        )
        
        # Show text input field if "Other" is selected
        if investment_sectors == "Other":
            other_sector = st.text_input("Please specify the sector:")
    
    with col2:
        # Investment Objective
        if 'investment_objective' not in st.session_state:
            st.session_state.investment_objective = "Select"
        
        st.markdown("##### Investment Objective")
        objective_tooltip = "Your primary goal influences which political factors are most relevant to your analysis"
        investment_objective = st.selectbox(
            "What is your primary objective?",
            options=["Select", "Capital Growth", "Stable Income", "Diversification", "Hedging", "Speculation", "Other"],
            help=objective_tooltip
        )

         # Analysis Motivation
        if 'analysis_motivation' not in st.session_state:
            st.session_state.analysis_motivation = "Select"
        
        st.markdown("##### Analysis Motivation")
        motivation_tooltip = "Understanding your motivation helps us tailor our analysis to your specific needs"
        analysis_motivation = st.selectbox(
            "Why are you seeking political risk analysis?",
            options=["Select", "Existing Investment Protection", "Portfolio Diversification", "Due Diligence", "Strategic Planning", "Regulatory Compliance", "Other"],
            help=motivation_tooltip
        )
        
        # Show text input field if "Other" is selected
        if analysis_motivation == "Other":
            other_motivation = st.text_input("Please specify your motivation:")
        
        # Show text input field if "Other" is selected
        if investment_objective == "Other":
            other_objective = st.text_input("Please specify your investment objective:")
        
        # Risk Analysis Experience
        if 'risk_experience' not in st.session_state:
            st.session_state.risk_experience = "Select Level"
        
        st.markdown("##### Political Risk Experience")
        experience_tooltip = "Your familiarity with political risk analysis helps us determine the depth of information to provide"
        risk_experience = st.selectbox(
            "How familiar are you with political risk analysis?",
            options=["Not at all familiar", "Slightly familiar", "Moderately familiar", "Very familiar"],
            help=experience_tooltip
        )
 

        # Save all selections to session state
        st.session_state.investor_type = investor_type
        st.session_state.location = location
        st.session_state.investment_sectors = investment_sectors
        st.session_state.investment_objective = investment_objective
        st.session_state.risk_experience = risk_experience
        st.session_state.analysis_motivation = analysis_motivation
       
        
        # Save "Other" text inputs if applicable
        if investor_type == "Other" and 'other_investor_type' in locals():
            st.session_state.other_investor_type = other_investor_type
        if investment_sectors == "Other" and 'other_sector' in locals():
            st.session_state.other_sector = other_sector
        if investment_objective == "Other" and 'other_objective' in locals():
            st.session_state.other_objective = other_objective
        if analysis_motivation == "Other" and 'other_motivation' in locals():
            st.session_state.other_motivation = other_motivation
                
        if (
            investor_type == "Select" or
            location == "Select Country" or
            investment_sectors == "Select Sector" or
            investment_objective == "Select" or
            risk_experience == "Not at all familiar" or
            analysis_motivation == "Select"
        ):
            st.warning('Please fill out all profile fields to continue')
            st.stop()
            
    
    # Page header with attractive styling
    st.markdown("### Activity Assessment")
    
    # Introduction and context explanation
    st.markdown("""
    
    Now that we have some basic information, please provide details about the activities or opportunities you're considering.

    """)
    # Create two columns for better layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
         # Investment Scale
        if 'investment_scale' not in st.session_state:
            st.session_state.investment_scale = "Select Scope"
        
        st.markdown("###### Resource Investment")
        scope_tooltip = "The relative financial scope of your planned investment activity"
        investment_scale = st.selectbox(
            "What is the relative scope of this investment?",
            options=["Select Scope", "Minimal Commitment", "Moderate Commitment", "Substantial Commitment", "Full Commitment"],
            help=scope_tooltip
        )
        
        # Target Country/Region
        if 'target_locations' not in st.session_state:
            st.session_state.target_locations = []
        
        st.markdown("###### Target Locations")
        target_tooltip = "Countries or regions where you plan to invest"
        # Get all country names
        all_countries = sorted([country.name for country in pycountry.countries if country.name != "United States"])
        # Add United States at the top
        country_names = ["United States"] + all_countries
        # Two-step location selection
        target_locations = st.multiselect(
            "Select the countries or regions you're interested in",
            options=country_names,
            help=target_tooltip,
            default=st.session_state.target_locations
        )
        
        # Timeline
        if 'timeline' not in st.session_state:
            st.session_state.timeline = "Select Timeline"
        
        st.markdown("###### Timeline")
        timeline_tooltip = "When you plan to initiate this investment activity"
        timeline = st.selectbox(
            "When do you plan to initiate this activity?",
            options=["Select Timeline", "Immediate (0-3 months)", "Short-term (3-12 months)", 
                     "Medium-term (1-2 years)", "Long-term (2+ years)"],
            help=timeline_tooltip
        )
    
    with col2:
        # ESG Importance
        if 'esg' not in st.session_state:
            st.session_state.esg = "Select Importance"
        
        st.markdown("###### ESG Importance")
        esg_tooltip = "How important are political factors related to environmental, social, and governance issues in your investment decision-making?"
        esg = st.selectbox(
             "Importance of ESG factors", 
            options=["Select Importance", "Not Important", "Somewhat Important", "Important", "Very Important", "Critical"],
            help=esg_tooltip
        )
        
        # Risk Tolerance
        if 'risk_tolerance' not in st.session_state:
            st.session_state.risk_tolerance = "Select Tolerance"
        
        st.markdown("###### Risk Tolerance")
        tolerance_tooltip = "Your overall tolerance for political risk in investments"
        risk_tolerance = st.selectbox(
            "Your overall tolerance for political risk in investments",
            options=["Select Tolerance", "Very Conservative", "Conservative", "Moderate", "Aggressive", "Very Aggressive"],
            help=tolerance_tooltip
        )

        # Primary Concerns
        if 'primary_concerns' not in st.session_state:
            st.session_state.primary_concerns = []
        
        st.markdown("###### Primary Risk Concerns")
        concerns_tooltip = "Select the political risk factors you're most concerned about"
        primary_concerns = st.multiselect(
            "Select the political risk factors that most concern you",
            options=["Regulatory Changes", "Political Instability", "Corruption", "Expropriation", 
                     "Currency Controls", "Social Unrest", "Trade Barriers", "Labor Regulations", 
                     "Environmental Regulations", "Sanctions", "Terrorism/Security"],
            help=concerns_tooltip,
            default=st.session_state.primary_concerns
        )

    # Validation check (corrected)
    if (
        investment_scale == "Select Scope" or 
        not target_locations or
        timeline == "Select Timeline" or
        esg == "Select Importance" or
        risk_tolerance == "Select Tolerance" or
        not primary_concerns
    ):
        st.warning('Please fill out your investment and expansion details to continue')
        st.stop()

    st.markdown("### Additional Details")

    st.markdown("""
    Please share any extra details or concerns about this that haven't been covered above. 
    The more specific the better.
                 
    """)
    additional_context = st.text_area(
        "Optional",
        help="Include any specific concerns or details not covered above",
        height=100,
        key="additional_context"
    )
        
    # Save all selections to session state
    st.session_state.investment_scale = investment_scale
    st.session_state.target_locations = target_locations
    st.session_state.timeline = timeline
    st.session_state.esg = esg
    st.session_state.risk_tolerance = risk_tolerance
    st.session_state.primary_concerns = primary_concerns

    
    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Previous", key="investment_prev"):
            prev_page()

    with col2:
        proceed_button_disabled = (
            investment_scale == "Select Scope" or 
            not target_locations or
            timeline == "Select Timeline" or
            esg == "Select Importance" or
            risk_tolerance == "Select Tolerance" or
            not primary_concerns
        )
        
        if st.button("Next", type="primary", key="investment_next", disabled=proceed_button_disabled):
            next_page()

elif st.session_state.page == 2:
    st.title("Political Risk Analysis")

    # Set up the Python path to find the agents module
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.append(project_root)
    
    # Now try importing with better error handling
    try:
        from agents.langgraphCombiner.LangGraph import LangGraphOrchestrator
        from apisecrets.geminapi import api_key
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as e:
        st.error(f"""
        Failed to import required modules. Error: {str(e)}
        
        Current path: {os.getcwd()}
        Python path: {sys.path}
        Project root: {project_root}
        """)
        st.stop()

    # Convert session state data to the format expected by LangGraph
    user_data = {
        "investor_type": st.session_state.investor_type,
        "location": st.session_state.location,
        "investment_sectors": ", ".join(st.session_state.investment_sectors),
        "target_locations": ", ".join(st.session_state.target_locations),
        "investment_objective": st.session_state.investment_objective,
        "analysis_motivation": st.session_state.analysis_motivation,
        "risk_experience": st.session_state.risk_experience,
        "timeline": st.session_state.timeline,
        "investment_scale": st.session_state.investment_scale,
        "risk_tolerance": st.session_state.risk_tolerance,
        "esg": st.session_state.esg,
        "primary_concerns": ", ".join(st.session_state.primary_concerns),
        "additional_info": st.session_state.get("additional_context", "")
    }

    # Add a placeholder for logs
    log_display = st.empty()

    with st.spinner("Initializing analysis..."):
        try:
            # Initialize LangGraph Orchestrator
            orchestrator = LangGraphOrchestrator(api_key=api_key)
            
            # Run analysis with progress tracking
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

                    # Display results
                    st.header("Analysis Results")

                    # Display research team results
                    with st.expander("Research Details"):
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

                    # Display summary
                    st.header("Risk Assessment Summary")
                    if final_state.get("status") == "research_complete":
                        st.success("Analysis completed successfully!")
                        
                        if risk_scores:
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

                except TimeoutError:
                    st.error("Analysis timed out after 5 minutes. Please try again.")

        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")

    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Previous", key="results_prev"):
            prev_page()
    with col2:
        if st.button("Start New Analysis", key="new_analysis"):
            st.session_state.page = 0
            st.rerun()








    
