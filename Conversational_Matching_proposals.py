import streamlit as st
import json
import boto3
from dotenv import load_dotenv
import os
# from price_estimation import log_chat_new, display_chat_history_new, handle_dynamic_questions, calculate_price


# Load environment variables
load_dotenv()

# Initialize the Bedrock client
aws_session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("aws_secret_region")
)
bedrock_client = aws_session.client(service_name="bedrock-runtime")

# List of required lead details
REQUIRED_LEAD_DETAILS = {
    "Annual Revenue": "What is the approximate annual revenue of your business?",
    "Industry": "Which industry does your business operate in?",
    "Entity Type": "What is the entity type of your business (e.g., LLC, Corporation)?",
    "Publicly Traded": "Is your business publicly traded or privately held?",
    "Primary Accounting Software": "What is the primary accounting software your business uses (e.g., QuickBooks, Xero)?",
    "Months to Clean-Up": "How many months of bookkeeping clean-up are needed?",
    "Year to Be Filed": "Which financial year do you want to file taxes for?",
    "States to File Taxes": "Which states do you need to file taxes in?",
}

# Tax-related keywords
TAX_KEYWORDS = ["tax", "filing", "tax preparation", "tax filing"]

def is_tax_related(user_input):
    """Check if the user input relates to tax services."""
    return any(keyword in user_input.lower() for keyword in TAX_KEYWORDS)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "asked_questions" not in st.session_state:
    st.session_state.asked_questions = set()
if "collected_details" not in st.session_state:
    st.session_state.collected_details = {}
if "response" not in st.session_state:
    st.session_state.response = None
if "final_response" not in st.session_state:
    st.session_state.final_response = None
if "asked_questions" not in st.session_state:
    st.session_state.asked_questions = set()
if "show_price_estimation_button" not in st.session_state:
    st.session_state.show_price_estimation_button = False

def log_chat(sender, message):
    """Log chat messages while avoiding duplicates."""
    if sender == "Bot" and message in st.session_state.asked_questions:
        return  # Skip if the bot already asked this question
    st.session_state.chat_history.append({"sender": sender, "message": message})
    if sender == "Bot":
        st.session_state.asked_questions.add(message)

def display_chat_history():
    """Display the chat history."""
    for chat in st.session_state.chat_history:
        sender, message = chat["sender"], chat["message"]
        st.markdown(f"**{sender}:** {message}")
        
# Dynamic questions for price estimation
def handle_dynamic_questions():
    """Handle dynamic question flows and store responses."""
    if "dynamic_details" not in st.session_state:
        st.session_state.dynamic_details = {}

    # Question 1: Filing Type
    if "Filing Type" not in st.session_state.dynamic_details:
        filing_type = st.radio(
            "Are you filing for Personal, Business, or Both?",
            ["Personal", "Business", "Both"],
            key="dynamic_filing_type",
        )
        if st.button("Submit Filing Type"):
            st.session_state.dynamic_details["Filing Type"] = filing_type
            st.rerun()

    # Personal questions
    elif st.session_state.dynamic_details["Filing Type"] == "Personal":
        # State of residence question
        if "State of Residence" not in st.session_state.dynamic_details:
            state = st.text_input("What is your state of residence?", key="state_residence")
            if st.button("Submit State"):
                st.session_state.dynamic_details["State of Residence"] = state
                st.rerun()

        # Self-employment income question
        elif "Self Employment Income" not in st.session_state.dynamic_details:
            self_employment = st.radio(
                "Did you earn any income through self-employment?",
                ["Yes-1040-C", "No-1040"],
                key="self_employment_income",
            )
            if st.button("Submit Self Employment Income"):
                st.session_state.dynamic_details["Self Employment Income"] = self_employment
                st.rerun()

    # Business questions
    elif st.session_state.dynamic_details["Filing Type"] == "Business":
        # Number of businesses
        if "Number of Businesses" not in st.session_state.dynamic_details:
            num_businesses = st.number_input(
                "How many businesses are you filing for?", min_value=1, step=1, key="num_businesses"
            )
            if st.button("Submit Number of Businesses"):
                st.session_state.dynamic_details["Number of Businesses"] = num_businesses
                st.rerun()

        # Businesses in the same state
        elif "Businesses in Same State" not in st.session_state.dynamic_details:
            same_state = st.radio(
                "Are all your businesses located in the same state?",
                ["Yes", "No"],
                key="same_state",
            )
            if st.button("Submit Businesses in Same State"):
                st.session_state.dynamic_details["Businesses in Same State"] = same_state
                st.rerun()

        # Legal structure for each business
        elif st.session_state.dynamic_details["Businesses in Same State"] == "No":
            for i in range(1, st.session_state.dynamic_details["Number of Businesses"] + 1):
                if f"Business {i} State" not in st.session_state.dynamic_details:
                    state = st.text_input(f"What is the state for Business {i}?", key=f"business_{i}_state")
                    if st.button(f"Submit State for Business {i}"):
                        st.session_state.dynamic_details[f"Business {i} State"] = state
                        st.rerun()

                if f"Business {i} Legal Structure" not in st.session_state.dynamic_details:
                    structure = st.selectbox(
                        f"What is the legal structure for Business {i}?",
                        ["Partnership - 1065", "S Corp - 1120-S", "C Corp - 1120"],
                        key=f"business_{i}_structure"
                    )
                    if st.button(f"Submit Legal Structure for Business {i}"):
                        st.session_state.dynamic_details[f"Business {i} Legal Structure"] = structure
                        st.rerun()

    return st.session_state.dynamic_details

# Price calculation function
def calculate_price(dynamic_details):
    filing_type = dynamic_details.get("Filing Type")
    price = 0
    overage_cost = 75

    if filing_type == "Personal":
        self_employment = dynamic_details.get("Self Employment Income")
        if self_employment == "Yes-1040-C":
            price = 350
        else:
            price = 300

    elif filing_type == "Business":
        num_businesses = dynamic_details.get("Number of Businesses", 1)
        if num_businesses == 1:
            price = 540
        else:
            price = 540 * num_businesses

    elif filing_type == "Both":
        # Separate calculations for each filing type
        personal_price, business_price = 0, 0

        self_employment = dynamic_details.get("Self Employment Income")
        if self_employment == "Yes-1040-C":
            personal_price = 350
        else:
            personal_price = 300

        num_businesses = dynamic_details.get("Number of Businesses", 1)
        if num_businesses == 1:
            business_price = 540
        else:
            business_price = 540 * num_businesses

        price = personal_price + business_price

    total_price = price + overage_cost
    return price, overage_cost, total_price


def collect_missing_details_interactive(missing_keys):
    """Iteratively collect missing details in Q&A format and confirm final details."""
    unanswered_keys = [key for key in missing_keys if key not in st.session_state.collected_details]

    total_questions = len(missing_keys)
    asked_questions = len(st.session_state.asked_questions)
 
    status_bar = "".join(
    ["✅" if i < asked_questions else "⬜" for i in range(total_questions)]
    )

    st.write(
        f"Questions Status: {status_bar} {asked_questions}/{total_questions} questions answered"
    )
    
    if unanswered_keys:
        key = unanswered_keys[0]
        question = REQUIRED_LEAD_DETAILS[key]

        # Log the question if not already asked
        log_chat("Bot", question)

        value = st.text_input(question, key=f"text-{key}")

        if st.button("Submit", key=f"submit-{key}"):
            if value:  # Ensure a valid response
                st.session_state.collected_details[key] = value
                log_chat("User", value)
                st.rerun()
            if not value:
                value = ""
                st.session_state.collected_details[key] = ""
                st.session_state.asked_questions.add(key)  # Mark as answered
                st.rerun()# Restart the Streamlit app to continue

    elif st.session_state.collected_details:
        st.subheader("Review Your Details")

        # Combine available details (from the model) and missing details (Q&A collected)
        combined_details = {
            **st.session_state.response.get("provided_details", {}),
            **st.session_state.collected_details,
        }

        # Create editable fields for each detail
        edited_details = {}
        for key, value in combined_details.items():
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                edited_details[key] = st.text_input(f"{key}:", value=value, key=f"edit-{key}")
            with col2:
                st.write("✏️")  # Pen emoji for visual effect

        if st.button("Confirm Details"):
            # st.spinner("Analyzing details and generating proposal...")
            st.success("Details confirmed! Analyzing details and generating proposal...")
            
            
            # Update the collected details with edits
            st.session_state.collected_details = edited_details
            
            # Update the final response with combined details
            st.session_state.final_response = combine_responses(
                st.session_state.response, edited_details
            )
            
            # Combine edited details with user input for generating the proposal
            final_data1 = {
                    "user_input": user_input,  # Add the original user input
                    "edited_details": edited_details,  # Add the finalized edited details
                }
              

            # Generate the analyze details response
            analyze_response = analyze_details_with_bedrock(
                json.dumps(edited_details),
                st.session_state.response)

            # Generate the proposal response
            proposal_response = generate_proposal(json.dumps(final_data1))

            # Display both responses
            st.subheader("Generated Proposal Response:")
            st.json(proposal_response)
            # st.subheader("Analyze Details Response:")
            st.json(analyze_response)
            
             # Set the flag to show the Price Estimation button
            st.session_state.show_price_estimation_button = True


    else:
        st.success("All questions answered!")
        # Combine collected details with the MODEL RESPONSE
        st.session_state.final_response = combine_responses(
            st.session_state.response, st.session_state.collected_details
        )
    return None


def combine_responses(model_response, collected_details):
    """
    Combine the model response with all collected details (provided and missing),
    ensuring a complete and finalized response.
    """
    # Start with a copy of the original model response to avoid mutation
    combined_response = model_response.copy()

    # Merge provided details from both the model response and Q&A collected details
    combined_details = {
        **model_response.get("provided_details", {})
        # ,
        # **collected_details
    }

    # Update the combined response
    combined_response["provided_details"] = combined_details
    # combined_response["missing_details"] = []  # Clear missing details since they're resolved

    return combined_response



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

    Return the results **strictly as a valid JSON object**, without any additional text or commentary. 
    The JSON object must have the following structure:
    {{
        "provided_details": A dictionary of all extracted lead details,
        "missing_details": A list of required details that are missing
    }}

    Ensure the output is valid JSON and does not include any explanatory text.
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
            contentType="application/json"
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




# from price_estimation import log_chat_new, display_chat_history_new, handle_dynamic_questions, calculate_price

st.title("Financial Proposal Generator")
st.write("Enter your business details to generate a tailored financial proposal.")

# Initialize session state variables
if "response" not in st.session_state:
    st.session_state.response = None
if "final_response" not in st.session_state:
    st.session_state.final_response = None
if "collected_details" not in st.session_state:
    st.session_state.collected_details = {}
if "missing_keys" not in st.session_state:
    st.session_state.missing_keys = []
if "show_final_response" not in st.session_state:
    st.session_state.show_final_response = False
if "process_started" not in st.session_state:
    st.session_state.process_started = False
if "price_estimation_started" not in st.session_state:
    st.session_state.price_estimation_started = False

# Collect user input
user_input = st.text_area("Enter your requirements for the proposal")
display_chat_history()

# Only show the "Generate Proposal" button if input is entered and process has not started yet
if not st.session_state.process_started:
    if user_input.strip():
        if st.button("Generate Proposal"):
            with st.spinner("Generating proposal..."):
                response = generate_proposal(user_input)  # Replace with your actual function
                if "error" in response:
                    st.error(f"Error: {response['error']}")
                else:
                    st.session_state.response = response
                    st.session_state.process_started = True  # Set process_started to True

# If the process has started, handle tax-related logic or proceed with the flow
if st.session_state.process_started:
    if st.session_state.response:
        response = st.session_state.response

        if is_tax_related(user_input):  # Replace with your tax-checking logic
            with st.spinner("Analyzing details and generating proposal..."):
                # Trigger the first model: analyze_details_with_bedrock
                analysis_result = analyze_details_with_bedrock(user_input, response)  # First model
                if analysis_result.get("error"):
                    st.error(f"Error in analysis: {analysis_result['error']}")
                else:
                    provided_details = analysis_result.get("provided_details", {})
                    st.session_state.missing_keys = analysis_result.get("missing_details", [])

                    # Store provided details
                    st.session_state.collected_details.update(provided_details)

                    # Collect additional details interactively if needed
                    if st.session_state.missing_keys:
                        collect_missing_details_interactive(st.session_state.missing_keys)

            # Display the final combined response
            st.success("This proposal is tax-related. Here's your response:")
            st.session_state.final_response = response
            st.session_state.show_final_response = True

        else:
            # If not tax-related, only trigger the proposal model
            st.success("This proposal is not related to tax. Here's your response:")
            st.session_state.final_response = response
            st.session_state.show_final_response = True
            st.subheader("Final Response")
            st.json(st.session_state.final_response)

# Display the final combined response only after details are submitted
# if st.session_state.show_final_response:
#     st.json(st.session_state.final_response)
           
                
# Display the generated proposal response if available
# if st.session_state.final_response:
#     st.subheader("Generated Proposal Response:")
#     st.json(st.session_state.final_response)
# if is_tax_related(user_input):
# Show the Price Estimation button after confirming details
if st.session_state.show_price_estimation_button:
    st.subheader("Price Estimation")
    if is_tax_related(user_input):  # Assuming this function checks if the input is tax-related
        # Button to start price estimation
        if st.button("Start Price Estimation"):
            st.session_state.price_estimation_started = True

        # Proceed with price estimation process if button is clicked
    if st.session_state.price_estimation_started:
        # Gather additional details interactively
        dynamic_details = handle_dynamic_questions()

        # Ensure all details are complete before calculating the price
        if "Filing Type" in dynamic_details:
            if (
                (dynamic_details["Filing Type"] == "Personal" and "Self Employment Income" in dynamic_details) or
                (dynamic_details["Filing Type"] == "Business" and "Number of Businesses" in dynamic_details) or
                (dynamic_details["Filing Type"] == "Both" and "Number of Businesses" in dynamic_details)
            ):
                price, overage_cost, total_price = calculate_price(dynamic_details)
                st.write(f"Service cost: ${price}")
                st.write(f"Overage cost: ${overage_cost}")
                st.write(f"Total cost: ${total_price}")
            else:
                st.warning("Please complete all required selections for price estimation.")
        else:
            st.warning("Filing Type is required for price estimation.")