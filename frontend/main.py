import streamlit as st 
import pycountry

# Initialize session state variables if they don't exist
if 'page' not in st.session_state:
    st.session_state.page = 0

if 'email' not in st.session_state:
    st.session_state.email = ""

# Functions to navigate between pages
def next_page():
    st.session_state.page += 1
    st.rerun()

def prev_page():
    st.session_state.page -= 1
    st.rerun()


# Page 0: Welcome and Email Collection
if st.session_state.page == 0:

    st.markdown("### Political Risk Analysis Agent")

    st.markdown("""
    Welcome to the Political Risk Analysis Agent.
    This tool is designed to utilize Agentic AI to help businesses assess political risks that could impact their operations, 
    investments, and strategic decisions across global markets.

    Our ontology combines a variety of structured and unstructured data sources, organizing them to map the relationships 
    between key data elements. This allows for the creation of a cohesive and consistent view of political landscapes,
    allowing for:

    * Comprehensive Risk Assessment
    * Risk Factor Breakdown
    * Opportunity Analysis
    * Comparative Analysis
                
    """)
    
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
   
    # Page header with attractive styling
    st.title("Business Profile")
    
    # Introduction and context explanation
    st.markdown("""
    Political risks impact businesses in different ways. 
    For example, a manufacturing firm with global supply chains faces distinct challenges compared to a software tech startup. 
    To provide meaningful analysis, our AI analyst needs a clear picture of your specific business environment.

    This brief business profile allows our system to understand the core aspects of your company, how you operate, where you're located, and what industry you're in. 
    The information you provide will enable us to generate insights that are tailored to your unique risk landscape.

    Your responses will be used exclusively to create a more accurate and relevant political risk assessment.

    Please complete all fields below to proceed.
    """)
    
    # Create two columns for better layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Industry Selection
        if 'industry' not in st.session_state:
            st.session_state.industry = "Select Sector"
        
        st.markdown("##### Industry Sector")
        industry_tooltip = "Your industry sector helps identify sector-specific political risks and regulatory concerns"
        industry = st.selectbox(
            "Which industry represents your primary business?",
            options=["Select Sector", "Energy & Resources", "Manufacturing", "Financial Services",
                    "Technology", "Healthcare", "Consumer Goods", "Infrastructure & Construction",
                    "Agriculture", "Transportation & Logistics", "Other"],
            help=industry_tooltip
        )
        
        # Business Location
        if 'location_business' not in st.session_state:
            st.session_state.location_business = "Select Region"
        
        st.markdown("##### Headquarters Location")
       # Get all country names
        all_countries = sorted([country.name for country in pycountry.countries if country.name != "United States"])
        # Add United States at the top
        country_names = ["Select Country"]+["United States"] + all_countries
        location_tooltip = "Your home base influences your exposure to domestic political risks"
        location_business = st.selectbox(
            "Where is your business headquartered?",
            options= country_names,
            help=location_tooltip
        )
        
        # Company Size
        if 'company_size' not in st.session_state:
            st.session_state.company_size = "Select Size"
        
        st.markdown("##### Company Size")
        size_tooltip = "The size of your organization may affect your vulnerability to certain types of political risk"
        company_size = st.selectbox(
            "How many employees work in your organization?",
            options=["Select Size", "Small (1-50 employees)", "Medium (51-200 employees)", "Large (201+ employees)"],
            help=size_tooltip
        )
    
    with col2:
        # Business Maturity
        if 'business_maturity' not in st.session_state:
            st.session_state.business_maturity = "Select Maturity"
        
        st.markdown("##### Business Maturity")
        maturity_tooltip = "Your company's maturity level helps determine your resilience to political disruptions"
        business_maturity = st.selectbox(
            "What stage is your business currently in?",
            options=["Select Maturity", "Startup", "Growth Stage", "Established", "Mature"],
            help=maturity_tooltip
        )
        
        # Business Model
        if 'business_model' not in st.session_state:
            st.session_state.business_model = "Select Model"
        
        st.markdown("##### Business Model")
        model_tooltip = "Different business models face different types of political and regulatory challenges"
        business_model = st.selectbox(
            "What is your primary business model?",
            options=["Select Model", "B2B (Business to Business)", "B2C (Business to Consumer)", 
                    "C2C (Consumer to Consumer)", "B2G (Business to Government)", "G2G (Government to Government)"],
            help=model_tooltip
        )
        
        # International Exposure (additional relevant question)
        if 'international_exposure' not in st.session_state:
            st.session_state.international_exposure = "Select Exposure"
        
        st.markdown("##### International Exposure")
        exposure_tooltip = "Your level of global activity directly impacts your political risk profile"
        international_exposure = st.selectbox(
            "What is your level of international business activity?",
            options=["Select Exposure", "Domestic only", "Limited international", "Significant international", "Global operations"],
            help=exposure_tooltip
        )
    
    # Save all selections to session state
    st.session_state.industry = industry
    st.session_state.location_business = location_business
    st.session_state.company_size = company_size
    st.session_state.business_maturity = business_maturity
    st.session_state.business_model = business_model
    st.session_state.international_exposure = international_exposure
   
    # Proceed and Previous buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Previous", key="profile_prev"):
            prev_page()

    with col2:
        proceed_button_disabled = (
            industry == "Select Sector" or 
            location_business == "Select Region" or 
            company_size == "Select Size" or
            business_maturity == "Select Maturity" or
            business_model == "Select Model" or
            international_exposure == "Select Exposure"
        )
        
        if st.button("Next", key="profile_next", disabled=proceed_button_disabled):
            next_page()

# Page 2: Investment/Expansion Details
elif st.session_state.page == 2:
    
    # Page header with attractive styling
    st.title("Investment or Expansion Details")
    
    # Introduction and context explanation
    st.markdown("""
    
    Now that we understand your business profile, please provide specific details about the investment, 
    expansion, or business activity you're considering. 
    
    Political risks vary significantly depending on the type of activity, location, timeframe, and scale 
    of your planned investment. The more specific information you can provide, the more targeted and 
    actionable your risk assessment will be.
    """)
    
    # Create two columns for better layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Activity Type
        if 'activity_type' not in st.session_state:
            st.session_state.activity_type = "Select Activity"
        
        st.markdown("###### Type of Activity")
        activity_tooltip = "Different business activities face distinct political risk factors"
        activity_type = st.selectbox(
            "What type of business activity are you planning?",
            options=["Select Activity", "New Market Entry", "Facility Construction", "Acquisition/M&A", 
                     "Joint Venture", "Distribution Expansion", "Supply Chain Development",
                     "Research & Development", "Financial Investment", "Government Contract", "Other"],
            help=activity_tooltip
        )
        
        # Target Country/Region
        if 'target_location' not in st.session_state:
            st.session_state.target_location = "Select Region"
        
        st.markdown("###### Target Location")
        target_tooltip = "The specific country where your activity will take place"
        # Get all country names
        all_countries = sorted([country.name for country in pycountry.countries if country.name != "United States"])
        # Add United States at the top
        country_names = ["Select Country"]+["United States"] + all_countries
        # Two-step location selection
        target_region = st.selectbox(
            "In which country will this activity take place?",
            options=country_names,
            help=target_tooltip,
            key="target_region"
        )
        
        
        # Timeline
        if 'timeline' not in st.session_state:
            st.session_state.timeline = "Select Timeline"
        
        st.markdown("###### Timeline")
        timeline_tooltip = "When you plan to begin this activity"
        timeline = st.selectbox(
            "When do you plan to initiate this activity?",
            options=["Select Timeline", "Immediate (0-3 months)", "Short-term (3-12 months)", 
                     "Medium-term (1-2 years)", "Long-term (2+ years)"],
            help=timeline_tooltip
        )

        st.markdown("""
        The agent will conduct a comprehensive assessment of all identifiable risks related to your operation.
        However, are there any particular risks you believe we should be especially aware of or give priority to?

        """)    
        # Primary Concerns
        if 'primary_concerns' not in st.session_state:
            st.session_state.primary_concerns = []
        
        # st.markdown("###### Primary Risk Concerns")
        concerns_tooltip = "Select the political risk factors you're most concerned about"
        primary_concerns = st.multiselect(
            "Which risk factors are you most concerned about?",
            options=["Regulatory Changes", "Political Instability", "Corruption", "Expropriation", 
                        "Currency Controls", "Social Unrest", "Trade Barriers", "Labor Regulations", 
                        "Environmental Regulations", "Sanctions", "Terrorism/Security"],
            help=concerns_tooltip,
            default=st.session_state.primary_concerns
        )
    
    with col2:
        # Investment Scale
        if 'investment_scale' not in st.session_state:
            st.session_state.investment_scale = "Select Scale"
        
        st.markdown("###### Investment Scale")
        scale_tooltip = "The approximate financial scale of your planned activity"
        investment_scale = st.selectbox(
            "What is the approximate scale of this investment?",
            options=["Select Scale", "Small (<$1M USD)", "Medium ($1M-$10M USD)", 
                     "Large ($10M-$100M USD)", "Major (>$100M USD)"],
            help=scale_tooltip
        )
        
        # Strategic Importance
        if 'strategic_importance' not in st.session_state:
            st.session_state.strategic_importance = "Select Importance"
        
        st.markdown("###### Strategic Importance")
        importance_tooltip = "How critical this activity is to your overall business strategy"
        strategic_importance = st.selectbox(
            "How important is this activity to your business strategy?",
            options=["Select Importance", "Critical (core to strategy)", "Significant (major initiative)", 
                     "Moderate (important but not critical)", "Minor (experimental/exploratory)"],
            help=importance_tooltip
        )
        
        # Local Partners
        if 'local_partners' not in st.session_state:
            st.session_state.local_partners = "Select Option"
        
        st.markdown("###### Local Partners")
        partners_tooltip = "Working with local partners can mitigate certain political risks"
        local_partners = st.selectbox(
            "Will you be working with local partners?",
            options=["Select Option", "Yes, established relationship", "Yes, new relationship", 
                     "No, direct operation", "Undecided"],
            help=partners_tooltip
        )


        # Additional Context
        if 'additional_context' not in st.session_state:
            st.session_state.additional_context = " "

        st.markdown("""
        Please share any extra details or concerns about this activity that haven't been covered above. 
        This may include specific challenges, nuances, or unique aspects that could influence the risk assessment. 
        """)
        additional_context = st.text_area(
            "Any additional context about this activity?",
            help="Include any specific concerns or details not covered above",
            height=100,
            key="additional_context",
            value=st.session_state.get('additional_context', '')
        )
        
    # Save all selections to session state
    st.session_state.activity_type = activity_type
    st.session_state.target_location = target_region
    st.session_state.timeline = timeline
    st.session_state.investment_scale = investment_scale
    st.session_state.strategic_importance = strategic_importance
    # st.session_state.local_partners = local_partners
    st.session_state.primary_concerns = primary_concerns
    st.session_state.local_partners = local_partners
    # st.session_state.additional_context = additional_context
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Previous", key="investment_prev"):
            prev_page()

    with col2:
        proceed_button_disabled = (
            activity_type == "Select Activity" or 
            target_region == "Select Country" or 
            timeline == "Select Timeline" or
            investment_scale == "Select Scale" or
            strategic_importance == "Select Importance" or
            local_partners == "Select Option"
        )
        
        if st.button("Next", type="primary", key="investment_next", disabled=proceed_button_disabled):
            next_page()

elif st.session_state.page == 3:
    pass

