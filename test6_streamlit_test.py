import streamlit as st
import json
import boto3
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Initialize the Bedrock client
aws_session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    ws_secret_region=os.getenv("AWS_region"),
)
bedrock_client = aws_session.client(service_name="bedrock-runtime")

# List of required lead details
REQUIRED_LEAD_DETAILS = {
    # "Name": "May I have your name, please?",
    "Annual Revenue": "What is the approximate annual revenue of your business?",
    "Industry": "Which industry does your business operate in?",
    "Entity Type": "What is the entity type of your business (e.g., LLC, Corporation)?",
    "Publicly Traded": "Is your business publicly traded or privately held?",
    "Primary Accounting Software": "What is the primary accounting software your business uses (e.g., QuickBooks, Xero)?",
    "Months to Clean-Up": "How many months of bookkeeping clean-up are needed?",
    "Year to Be Filed": "Which financial year do you want to file taxes for?",
    "States to File Taxes": "Which states do you need to file taxes in?",
}

TAX_KEYWORDS = ["tax", "filing", "tax preparation", "tax filing"]

def is_tax_related(user_input):
    """Check if the user input relates to tax services."""
    return any(keyword in user_input.lower() for keyword in TAX_KEYWORDS)

def collect_missing_details_interactive(missing_keys):
    """Iteratively collect missing details one question at a time."""
    # Initialize session state variables if not already initialized
    if "answered_questions" not in st.session_state:
        st.session_state.answered_questions = set()
        st.session_state.collected_details = {}

    # Debug: Display the session state to verify updates
    # st.write("Session State Debug Info:", st.session_state)

    # Find the next unanswered question
    unanswered_keys = [key for key in missing_keys if key not in st.session_state.answered_questions]

    # If there are unanswered questions, display the first one
    if unanswered_keys:
        key = unanswered_keys[0]
        st.write(f"Question: {REQUIRED_LEAD_DETAILS[key]}")

        # Render input fields based on the key
        if key == "Publicly Traded":
            value = st.selectbox(
                REQUIRED_LEAD_DETAILS[key], ["Publicly Traded", "Privately Held"], key=f"select-{key}"
            )
        elif key == "Months to Clean-Up":
            value = st.number_input(REQUIRED_LEAD_DETAILS[key], min_value=0, step=1, key=f"number-{key}")
        else:
            value = st.text_input(REQUIRED_LEAD_DETAILS[key], key=f"text-{key}")

        # Submit button for the current question
        if st.button("Submit", key=f"submit-{key}"):
            if value:  # Ensure a valid response is provided
                st.session_state.collected_details[key] = value
                st.session_state.answered_questions.add(key)  # Mark this question as answered
                st.rerun()  # Reload the app to reflect the next question

    else:
        # If all questions are answered, return the collected details
        st.success("All questions answered!")
        return st.session_state.collected_details

    return None


def analyze_details_with_bedrock(user_input, model_response):
    """
    Analyze user input and model response to extract provided details and identify missing ones using Bedrock.
    """
    prompt = f"""
    You are a highly intelligent assistant responsible for analyzing user input and a model-generated response. Your task is to:

    1. Extract any lead details provided in either the user input or the model response.
    2. Identify missing details based on the required lead details list and ask questions to collect them.
    3. Return a structured JSON output.

    The required lead details are:
    {json.dumps(list(REQUIRED_LEAD_DETAILS.keys()))}

    Analyze the following inputs:
    - **User Input:** {user_input}
    - **Model Response:** {json.dumps(model_response)}

    Return the results as a JSON object with these keys:
    - "provided_details": A dictionary of all extracted lead details.
    - "missing_details": A list of required details still missing.
    - "questions": A list of specific questions to ask for the missing details.
    """

    try:
        # Prepare the request parameters
        request_parameters = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0,
            "messages": [{"role": "user", "content": prompt}],
        }
        request_body = json.dumps(request_parameters)

        # Invoke the Bedrock model
        response = bedrock_client.invoke_model(
            modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
            body=request_body,
        )

        # Decode the response body
        response_body = response.get("body").read().decode("utf-8")

        if not response_body:
            return {"error": "Empty response from the model"}

        # Parse the response content
        full_response = json.loads(response_body)
        content = full_response.get("content", [])[0].get("text", "")

        # Extract JSON from the model response
        start_index = content.find("{")
        if start_index == -1:
            return {"error": "No JSON object found in model response"}

        # Parse the JSON result
        result_json = json.loads(content[start_index:])
        return result_json

    except json.JSONDecodeError as e:
        return {"error": f"JSON parsing error: {str(e)}"}
    except Exception as e:
        return {"error": f"Exception occurred: {str(e)}"}

def generate_proposal(user_input):
    """Generate a tailored financial proposal using Bedrock."""
    prompt = """    You are FinancialExpertAI, assigned to create a detailed SUMMARY PROPOSAL based on the provided requirements. 
Your task includes identifying the specific services, required skills, and relevant certifications from the given lists. 
The summary should be thorough, precise, and tailored to the mentioned requirements and available options.

Required Services:

    - Bookkeeping Clean Up
    - Accounting Advisory
    - Monthly Bookkeeping Support
    - Implementation of Accounting Software
    - Tax Filing
    - Tax Preparation
    - Basic Monthly Bookkeeping Support
    - Premium Monthly Bookkeeping Support
    - Plus Monthly Bookkeeping Support

Required Skills:

    - Tax Filing
    - Accounting
    - Auditing
    - Financial Analysis & Management
    - Data & Analytics
    - Compliance & Regulation
    - Soft Skills & General Management

Required Certificates:

    - Accredited in Business Valuations (ABV)
    - Certified Public Accountant (CPA)
    - Chartered Financial Analyst (CFA)
    
Required Service Lines: 

    - Tax Preparation
    - CPA/Accounting Advisory
    - Full Charge Bookkeeping
    - FP&A
    - CFO

Instructions:

- **Proposal Description:** Summarize the customer's requirements within this heading. Ensure that all provided information is addressed without adding anything extra.
- **Required Services:** From the list of available services, identify the specific services needed based on the customer's requirements. Present this as a list.
- **Required Skills:** Identify the required skills that correspond to the selected services. Present this as a list.
- **Required Certifications:** Identify the necessary certifications from the provided list based on the identified services and skills. Present this as a list.
- **Required Software:** Mention any software requirements if specified by the client. If not mentioned, state 'Not Mentioned'.
- **Required Service Line:** From the list of Required Service Lines, identify the specific services needed based on the customer's requirements. Present this as a list. 
- **Required Language:** Mention any Language requirements if specified by the client. If not mentioned, state 'Not Mentioned'.
- **Required Location and Time Zones:** Mention any location, time zone, or location radius if specified by the client. If not mentioned, state 'Not Mentioned'.
- **Required Teams:** Mention any Teams requirements if specified by the client. If not mentioned, state 'Not Mentioned'.
- **Start/End Dates:** Mention any Start/End Dates or any Timeline requirements if specified by the client. If not mentioned, state 'Not Mentioned'.

Return the response as a valid JSON object, **not a string**. The output must follow this exact format:

{
    "Proposal Description": "<Your detailed summary here>",
    "Required Services": ["<Service 1>", "<Service 2>", "<Service N>"],
    "Required Skills": ["<Skill 1>", "<Skill 2>", "<Skill N>"],
    "Required Certifications": ["<Certification 1>", "<Certification 2>", "<Certification N>"],
    "Required Software": "<Software name or 'Not Mentioned'>",
    "Required Service Line": ["<Service Line 1>", "<Service Line 2>", "<Service Line N>"],
    "Required Language": "<Language or 'Not Mentioned'>",
    "Required Location and Time Zones": "<Location or 'Not Mentioned'>",
    "Required Teams": "<Teams or 'Not Mentioned'>",
    "Start/End Dates": "<Dates or 'Not Mentioned'>"
}

Ensure the response is a valid JSON object, without extra formatting or escape characters."""  # Masked for brevity, same as your provided prompt
    full_prompt = prompt + "\nUser Input: " + user_input

    try:
        # Prepare request parameters
        request_parameters = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "temperature": 0,
            "messages": [
                {"role": "user", "content": full_prompt}
            ],
        }
        request_body = json.dumps(request_parameters)

        # Invoke the Bedrock model
        response = bedrock_client.invoke_model(
            modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
            body=request_body,
            contentType="application/json"
        )

        # Read response body
        response_body = response["body"].read().decode("utf-8")

        # Validate response
        if not response_body or not response_body.strip():
            return {"error": "Empty or invalid response from the model"}

        # Parse response content
        raw_content = json.loads(response_body)
        content_text = raw_content.get("content")[0]["text"]
        return json.loads(content_text)  # Final parsed JSON object

    except Exception as e:
        return {"error": f"Exception occurred: {str(e)}"}

# Streamlit App Code
st.title("Financial Proposal Generator")
st.write("Enter your business details to generate a tailored financial proposal.")

# Collect user input
user_input = st.text_area("Enter your requirements for the proposal")

if "response" not in st.session_state:
    st.session_state.response = None

if st.button("Generate Proposal"):
    with st.spinner("Generating proposal..."):
        response = generate_proposal(user_input)  # Replace with your actual function
        if "error" in response:
            st.error(f"Error: {response['error']}")
        else:
            st.session_state.response = response

# Display the proposal or additional details form
if st.session_state.response:
    response = st.session_state.response

    # Check if tax-related and collect additional details if needed
    if is_tax_related(user_input):  # Replace with your logic
        result = analyze_details_with_bedrock(user_input, response)  # Replace with your actual function

        if result.get("error"):
            st.error(f"Error: {result['error']}")
        else:
            provided_details = result["provided_details"]
            missing_keys = result["missing_details"]

            if missing_keys:
                st.warning("The proposal includes tax-related services. Please provide additional details below.")
                collected_details = collect_missing_details_interactive(missing_keys)

                if collected_details:  # Once all details are collected
                    provided_details.update(collected_details)
                    response["Additional Details"] = provided_details
                    st.success("All additional details collected successfully!")
                    st.json(response)
            else:
                st.success("All required details are already provided!")
                st.json(response)
    else:
        st.success("This is not related to tax. Here's your proposal:")
        st.json(response)
