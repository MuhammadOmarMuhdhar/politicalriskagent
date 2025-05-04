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
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.dataAgent import scenarioAgentlight
from agents.utils.cleanJson import parse
from agents import main
import subprocess
import redis
import uuid





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

load_dotenv()
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
r = redis.from_url(redis_url)


def submit_task(user_data):
    task_id = str(uuid.uuid4())
    task_data = {
        "id": task_id,
        "user_data": user_data,
        "created_at": time.time()
    }
    
    # Set initial status
    r.set(f"task:{task_id}:status", "pending")
    
    # Add task to queue (worker will pick it up)
    r.rpush("task_queue", json.dumps(task_data))
    
    return task_id

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


    if "user_data" not in st.session_state:
        st.session_state.user_data = {}

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
        "additional_info": st.session_state.get("additional_context", ""),
        "email": st.session_state.email
    }

    # store user data in session state
    st.session_state.user_data = user_data


    user_profile = {
        "Investor Type": st.session_state.investor_type,
        "Location": st.session_state.location,
        "Investment Sectors": ", ".join(st.session_state.investment_sectors),
        "Target Locations": ", ".join(st.session_state.target_locations),
        "Investment Objective": st.session_state.investment_objective,
        "Analysis Motivation": st.session_state.analysis_motivation,
        "Risk Experience": st.session_state.risk_experience,
        "Timeline": st.session_state.timeline,
        "Investment Scale": st.session_state.investment_scale,
        "Risk Tolerance": st.session_state.risk_tolerance,
        "ESG Considerations": st.session_state.esg,
        "Primary Concerns": ", ".join(st.session_state.primary_concerns),
        "Additional Information": st.session_state.get("additional_context", "")
    }

    # Display a review section with improved formatting
    st.markdown("### Review Your Investment Profile")
    st.markdown("""
    Please review the information you've provided before we proceed with your investment analysis.
    """)

    # Create a more visually appealing display of user data
    user_profile_df = pd.DataFrame(user_profile.items(), columns=["Parameter", "Response"])
    st.table(user_profile_df)


    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Previous", key="analysis_prev"):
            prev_page()
    with col2:
        if st.button("Next", key="new_analysis"):
            next_page()

elif st.session_state.page == 3:
    

    st.title("Research Validation")

    st.markdown("""
    ### Human-in-the-Loop Review
    
    Based on your profile and activity details, we've generated potential risk scenarios that could impact your interests.
    
    Please review these scenarios carefully. You can:
    - Accept them as is
    - Request regeneration if they don't align with your concerns
    - Provide specific feedback to refine the analysis
    
    This step ensures our analysis is tailored to your specific situation.
    """)

    user_data = st.session_state.user_data

    # Initialize session state variables for scenarios
    if 'scenario' not in st.session_state:
        st.session_state.scenario = {}
        st.session_state.regenerate_count = 0

    if 'scenario_generated' not in st.session_state:
        st.session_state.scenario_generated = False
    
    if 'selected_scenarios' not in st.session_state:
        st.session_state.selected_scenarios = []

    if 'regenerate_count' not in st.session_state:
        st.session_state.regenerate_count = 0
    # Function to generate scenarios
    def generate_scenarios():
        with st.spinner("Generating risk scenarios based on your profile..."):
            api_key = os.getenv("gemini_api_key")
            model_name = "gemini-2.0-flash"
            scenario_agent = scenarioAgentlight.agent(api_key=api_key, model_name=model_name)
            
            scenarios = scenario_agent.generate(user_data, risk_type=None)
            scenarios_cleaned = parse(scenarios, field_to_clean="scenario", fallback={})
            
            # Save scenarios to session state
            st.session_state.scenario = scenarios_cleaned
            st.session_state.scenario_generated = True
            st.session_state.regenerate_count += 1
        
        return scenarios_cleaned

    # Generate scenarios if not already done
    if not st.session_state.scenario_generated:
        scenarios_cleaned = generate_scenarios()
    else:
        scenarios_cleaned = st.session_state.scenario

    # Display scenarios in an organized, interactive way
    if scenarios_cleaned:
        st.markdown("## Risk Scenarios")
        
        scenario_list = []
        scenario_descriptions = {}
        
        # Extract and organize scenarios for display
        for broad_risk, specific_risks in scenarios_cleaned.items():
            for specific_risk, details in specific_risks.items():
                for key, value in details.items():
                    if isinstance(value, list) and value:
                        scenario_id = f"{broad_risk}_{specific_risk}_{key}"
                        scenario_title = f"{broad_risk.title()}: {specific_risk.title()}"
                        scenario_list.append(scenario_id)
                        scenario_descriptions[scenario_id] = {
                            "title": scenario_title,
                            "description": value[0],
                            "category": broad_risk,
                            "subcategory": specific_risk
                        }
        
        # Display each scenario with checkbox for selection
        with st.form(key="scenario_validation_form"):
            st.markdown("### Select the scenarios you'd like to include in your analysis:")
            
            # Group scenarios by broad risk category for better organization
            categories = set(desc["category"] for desc in scenario_descriptions.values())
            
            for category in categories:
                st.markdown(f"#### {category.title()}")
                cat_scenarios = {k: v for k, v in scenario_descriptions.items() if v["category"] == category}
                
                for scenario_id, details in cat_scenarios.items():
                    col1, col2 = st.columns([0.1, 0.9])
                    with col1:
                        scenario_selected = st.checkbox(
                            label="",
                            value=scenario_id in st.session_state.selected_scenarios,
                            key=f"check_{scenario_id}"
                        )
                    with col2:
                        st.markdown(f"**{details['subcategory']}**")
                        st.markdown(details['description'])
                        st.markdown("---")
                    
                    if scenario_selected and scenario_id not in st.session_state.selected_scenarios:
                        st.session_state.selected_scenarios.append(scenario_id)
                    elif not scenario_selected and scenario_id in st.session_state.selected_scenarios:
                        st.session_state.selected_scenarios.remove(scenario_id)
            
            # Feedback section
            st.markdown("### Additional Feedback")
            feedback = st.text_area(
                "Is there anything specific about these scenarios you'd like us to consider or modify?",
                key="scenario_feedback",
                height=100
            )

            
            # Save feedback to session state
            if "scenario_feedback" not in st.session_state:
                st.session_state["scenario_feedback"] = feedback  # only set if it doesn't exist yet

             # Submit button for the form
            submit = st.form_submit_button("Submit Selected Scenarios")
            
           
            
            if submit:
                if st.session_state.selected_scenarios:
                    st.session_state.selected_scenario_details = {
                        scenario_id: scenario_descriptions[scenario_id] 
                        for scenario_id in st.session_state.selected_scenarios 
                        if scenario_id in scenario_descriptions
                    }
                    next_page()
                    user_data = st.session_state.user_data

                    task_id = submit_task(user_data)

                    
                    # Use a non-daemon thread
                   
                else:
                    st.error("Please select at least one scenario before proceeding.")
    
    # Regeneration option with limitation
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Previous", key="scenario_prev"):
            prev_page()
    
    with col2:
        # Limit regenerations to prevent abuse
        max_regenerations = 3
        regenerate_disabled = st.session_state.regenerate_count >= max_regenerations
        
        if st.button("Regenerate Scenarios", 
                    disabled=regenerate_disabled,
                    help="Generate new scenarios based on your profile" if not regenerate_disabled else 
                         f"Maximum of {max_regenerations} regenerations reached"):
            st.session_state.scenario = {}
            st.session_state.scenario_generated = False
            st.session_state.selected_scenarios = []
            st.rerun()
    
    # Display warning if regeneration limit reached
    if regenerate_disabled:
        st.warning(f"You've reached the maximum of {max_regenerations} scenario regenerations. Please select from the current scenarios or go back to modify your profile.")



elif st.session_state.page == 4:
    import json
    import threading
    st.title("Analysis Submitted")

    user_data = st.session_state.user_data

    def run_analysis():
        import subprocess
        subprocess.run(["python", "agents/main.py", json.dumps(user_data)])
    
    # Use a non-daemon thread
    thread = threading.Thread(target=run_analysis, daemon=False)
    thread.start()
    
    # Display a success message
    st.success("Your political risk analysis is being processed!")
    
    st.markdown(f"""
    ### Thank You
    
    Your report will be sent to **{st.session_state.email}** within 20-60 minutes.
    
    **Confirmation ID:** {st.session_state.get('email', '')[:3].upper()}{int(time.time())%10000}

    
    """)