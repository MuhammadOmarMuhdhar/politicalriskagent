import streamlit as st 

import streamlit as st

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



# Title and header shown on all pages
st.title("Political Risk Analysis Agent")

# Page 0: Welcome and Email Collection
if st.session_state.page == 0:
    st.markdown("""
    Welcome to the Political Risk Analysis Agent.
    This tool is designed to utilize Agentic AI to help businesses assess political risks that could impact their operations, 
    investments, and strategic decisions across global markets.

    Our ontology combines a variety of structured and unstructured data sources, organizing them to clarify the relationships 
    between key elements. This framework creates a cohesive and consistent view of the political landscape, offering:

    * **Comprehensive Risk Assessment**
    * **Risk Factor Breakdown**
    * **Opportunity Analysis**
    * **Comparative Analysis**
                
    """)
    
    st.markdown("To get started, please enter your email address below.")
    email = st.text_input("Enter your email address:", value=st.session_state.email)
    
    if st.button("Next", key="email_next"):
            if email and "@" in email and "." in email:
                st.session_state.email = email
                next_page 
            else:
                st.error("Please enter a valid email address.")
    
 