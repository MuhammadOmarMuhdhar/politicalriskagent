def prompt_header(user_data):
    """Returns the header for the prompt based on user investment data."""
    # Validate user data
    if not user_data or not isinstance(user_data, dict):
        return "User data must be a non-empty dictionary."
    
    # Access data with default values to prevent KeyErrors
    fields = [
        'investor_type', 'location', 'investment_sectors', 
        'target_locations', 'investment_objective', 'analysis_motivation',
        'risk_experience', 'timeline', 'investment_scale',
        'risk_tolerance', 'esg', 'primary_concerns', 'additional_info'
    ]
    
    # Return early if essential fields are missing
    missing = [f for f in fields if f not in user_data]
    if missing:
        return f"Missing required fields: {', '.join(missing)}"
    
    # Generate prompt with direct dictionary access
    return f"""
You are a risk intelligence agent specializing in identifying political risks.
You are currently working with a/an {user_data['investor_type']} based in {user_data['location']}, 
who is interested in exploring opportunities in {user_data['investment_sectors']} across {user_data['target_locations']}.

Their objective is to {user_data['investment_objective']}, and they are seeking a {user_data['analysis_motivation']} analysis. 
They have {user_data['risk_experience']} when it comes to navigating political risk. 
Their timeline for this investment is {user_data['timeline']}, with a commitment level of {user_data['investment_scale']}.
Their tolerance for risk is {user_data['risk_tolerance']}.

Environmental, Social, and Governance (ESG) factors are {user_data['esg']} to them. 
They are particularly concerned about {user_data['primary_concerns']}-related political risks.

Additional information provided by the client:
{user_data['additional_info']}
"""


# # example usage

# user_data = {

#     "investor_type": "Investor",
#     "location": "the target location",
#     "investment_sectors": "various sectors",
#     "target_locations": "various locations",
#     "investment_objective": "maximize returns",
#     "analysis_motivation": "comprehensive",
#     "risk_experience": "limited experience",
#     "timeline": "a flexible timeline",
#     "investment_scale": "$100,000",
#     "esg": True,
#     "primary_concerns": ["regulatory changes", "market volatility"],
#     "additional_info": "No additional information provided.",
#     "risk_tolerance": "medium"
# }

# header = prompt_header(user_data)

# print(header)

