import streamlit as st
import json
import boto3
from dotenv import load_dotenv
import os

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
    "Months to Clean-Up": "How many months of clean-up are needed?",
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


def handle_dynamic_questions(step):
    # Initialize session state if not already set
    if "dynamic_details" not in st.session_state:
        st.session_state.dynamic_details = {}

    dynamic_details = st.session_state.dynamic_details

    if step == 1:
        filing_type = st.selectbox("What is your filing type?", ["Personal", "Business", "Both"], key="filing_type")
        dynamic_details["Filing Type"] = filing_type

        if st.button("Next", key="step1_next"):
            st.session_state.dynamic_step = 2
            st.rerun()

    elif step == 2:
        filing_type = dynamic_details.get("Filing Type")

        if filing_type in ["Personal", "Both"]:
            self_employment = st.radio("Do you have self-employment income?", ["Yes-1040-C", "No"], key="self_employment")
            dynamic_details["Self Employment Income"] = self_employment

        if filing_type in ["Business", "Both"]:
            num_businesses = st.number_input("How many businesses do you own?", min_value=1, step=1, key="num_businesses")
            dynamic_details["Number of Businesses"] = num_businesses

            same_state = st.radio("Are all businesses in the same state?", ["Yes", "No"], key="same_state")
            dynamic_details["Businesses in Same State"] = same_state

            if same_state == "No":
                for i in range(1, num_businesses + 1):
                    if f"Business {i} State" not in dynamic_details:
                        state = st.text_input(f"What is the state for Business {i}?", key=f"business_{i}_state")
                        if st.button(f"Submit State for Business {i}"):
                            dynamic_details[f"Business {i} State"] = state
                            st.rerun()

                    if f"Business {i} Legal Structure" not in dynamic_details:
                        structure = st.selectbox(
                            f"What is the legal structure for Business {i}?",
                            ["Partnership - 1065", "S Corp - 1120-S", "C Corp - 1120"],
                            key=f"business_{i}_structure"
                        )
                        if st.button(f"Submit Legal Structure for Business {i}"):
                            dynamic_details[f"Business {i} Legal Structure"] = structure
                            st.rerun()

        # Calculate price without displaying
        price, overage_cost, total_price = calculate_price(dynamic_details)
        st.session_state.price_details = {
            "Base Price": price,
            "Overage Cost": overage_cost,
            "Total Price": total_price,
        }

        if st.button("Finish", key="step2_finish"):
            st.session_state.dynamic_step = 3
            st.rerun()

    elif step == 3:
        st.success("Confirm Details to see Price along with Proposal Descriptions.")
        # Final details and price are stored in session state for use elsewhere


# def run_additional_streamlit_code():
#     st.subheader("Answer a fews additional questions to find the best price for you")

#     if "dynamic_step" not in st.session_state:
#         st.session_state.dynamic_step = 1

#     if "dynamic_details" not in st.session_state:
#         st.session_state.dynamic_details = {}

#     current_step = st.session_state.dynamic_step
#     handle_dynamic_questions(current_step)



def run_additional_streamlit_code():
    # Placeholder function for your above Streamlit code
    # Replace this section with your exact Streamlit code implementation
    
    st.subheader("Answer few Additional questions to find out the best price for you")
    # Simulated output from the above Streamlit code
    # st.title("Dynamic Question Handling")

    if "dynamic_step" not in st.session_state:
        st.session_state.dynamic_step = 1

    if "dynamic_details" not in st.session_state:
        st.session_state.dynamic_details = {}

    current_step = st.session_state.dynamic_step
    handle_dynamic_questions(current_step)
    additional_output = {"additional_key": "additional_value"}
    return additional_output


def collect_missing_details_interactive(missing_keys):
    """Iteratively collect missing details in Q&A format and confirm final details."""
    unanswered_keys = [key for key in missing_keys if key not in st.session_state.collected_details]

    total_questions = len(missing_keys)
    asked_questions = len(st.session_state.collected_details)
    Total_count_questions = total_questions + asked_questions
    answered_questions = Total_count_questions - total_questions

    # Progress bar for questions answered
    status_bar = "".join(
        ["✅" if i < answered_questions else "⬜" for i in range(8)]
    )
    st.write(
        f"Questions Status: {status_bar} ({answered_questions}/8) questions answered"
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
                st.rerun()  # Re-run to update the state and proceed to the next question

    elif st.session_state.collected_details:
        st.subheader("Review Your Details")

        # Combine available details (from the model) and missing details (Q&A collected)
        combined_details = {
            **st.session_state.response.get("provided_details", {}),
            **st.session_state.collected_details,
        }

        # Run additional Streamlit code and append its output
        additional_output = run_additional_streamlit_code()
        combined_details.update(additional_output)

        # Create editable fields for each detail
        edited_details = {}
        for key, value in combined_details.items():
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                edited_details[key] = st.text_input(f"{key}:", value=value, key=f"edit-{key}")
            with col2:
                st.write("✏️")  # Pen emoji for visual effect

        if st.button("Confirm Details"):
            st.success("Details confirmed! Analyzing details and generating proposal...")

            # Update the collected details with edits
            st.session_state.collected_details = edited_details

            # Update the final response with combined details
            st.session_state.final_response = combine_responses(
                st.session_state.response, edited_details
            )

            # Combine edited details with user input for generating the proposal
            final_data = {
                "user_input": st.session_state.user_input,  # Add the original user input
                "edited_details": edited_details,  # Add the finalized edited details
            }

            # Generate the analyze details response
            analyze_response = analyze_details_with_bedrock(
                json.dumps(edited_details),
                st.session_state.response
            )

            # Generate the proposal response
            proposal_response = generate_proposal(json.dumps(final_data))

            # Display both responses
            st.subheader("Generated Proposal Response:")
            st.json(proposal_response)
            st.subheader("Additional Details collected:")
            st.json(analyze_response)

            # Add Price Details as JSON (Only if tax-related)
            if is_tax_related(st.session_state.user_input):  # Assuming user input is stored in session state
                price, overage_cost, total_price = calculate_price(st.session_state.dynamic_details)

                # Create a dictionary for price details
                price_details = {
                    "Base Price": price,
                    "Overage Cost": overage_cost,
                    "Total Price": total_price,
                }

                # Display the price details as JSON
                # st.subheader("Price Calculation Results (JSON Format):")
                # st.json(price_details)

                # Update session state for price details (if needed for future use)
                st.session_state.price_details = price_details

            # Display the final price details section alongside other responses
            st.subheader("Estimated Price Details:")
            st.write("Here are the estimated price details:")
            st.json(st.session_state.price_details)

    else:
        st.success("All questions answered!")
        # Combine collected details with the model response
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

    Return the results as a JSON object with these keys:
    - "provided_details": A dictionary of all extracted lead details.
    - "missing_details": A list of missing lead details, if any.
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

        # Debugging: log the raw response
        # st.write("Raw model response:", response_body)

        # Check if the response body contains valid JSON and strip extra content
        try:
            # Extract the first valid JSON object from the response
            start_index = response_body.find("{")
            if start_index == -1:
                return {"error": "No JSON object found in model response"}

            # Extract the valid JSON string
            valid_json_str = response_body[start_index:]

            # Parse the valid JSON
            result_json = json.loads(valid_json_str)

            # Log the parsed JSON for further debugging
            # st.write("Parsed model response:", result_json)
        except json.JSONDecodeError as e:
            return {"error": f"JSON parsing error: {str(e)}"}

        # Access the 'content' field and parse the details from the first item
        model_content = result_json.get("content", [])
        if not model_content:
            return {"error": "No content found in model response"}

        content = model_content[0].get("text", "")
        # Extract the valid JSON part from the content
        json_start_index = content.find("{")
        json_end_index = content.rfind("}") + 1  # Ensure the full JSON is captured

        if json_start_index == -1 or json_end_index == -1:
            return {"error": "No valid JSON object found in content"}

        # Extract the JSON string and parse it
        valid_json_str = content[json_start_index:json_end_index]
        try:
            details_json = json.loads(valid_json_str)
        except json.JSONDecodeError as e:
            return {"error": f"Error extracting JSON from content: {str(e)}"}

        # Now, extract the provided and missing details
        provided_details = details_json.get("provided_details", {})
        missing_details = details_json.get("missing_details", [])

        if not provided_details and not missing_details:
            return {"error": "No provided or missing details found in model response"}

        return {
            "provided_details": provided_details,
            "missing_details": missing_details
        }

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
    
# st.write(response)

# Streamlit App
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
if "dynamic_step" not in st.session_state:
    st.session_state.dynamic_step = 1
if "dynamic_details" not in st.session_state:
    st.session_state.dynamic_details = {}
if "user_input" not in st.session_state:
    st.session_state.user_input = ""
if "price_details" not in st.session_state:
    st.session_state.price_details = {}

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
                    st.session_state.user_input = user_input
                    st.session_state.process_started = True

# If the process has started, handle tax-related logic or proceed with the flow
if st.session_state.process_started:
    if st.session_state.response:
        response = st.session_state.response

        if is_tax_related(st.session_state.user_input):  # Check if input is tax-related
            with st.spinner("Analyzing details and generating proposal..."):
                # Trigger the first model: analyze_details_with_bedrock
                analysis_result = analyze_details_with_bedrock(
                    st.session_state.user_input, response
                )  # First model
                if analysis_result.get("error"):
                    st.error(f"Error in analysis: {analysis_result['error']}")
                else:
                    provided_details = analysis_result.get("provided_details", {})
                    missing_details = analysis_result.get("missing_details", [])

                    # Update session state with provided and missing details
                    st.session_state.collected_details.update(provided_details)
                    st.session_state.missing_keys = missing_details

                    # Continue with collecting missing details or showing results
                    if st.session_state.missing_keys:
                        collect_missing_details_interactive(st.session_state.missing_keys)
                    else:
                        # Handle dynamic questions for tax-related details
                        current_step = st.session_state.dynamic_step
                        handle_dynamic_questions(current_step)

                        # If dynamic questions are completed, calculate and display price
                        if current_step == 3:
                            price, overage_cost, total_price = calculate_price(
                                st.session_state.dynamic_details
                            )
                            st.session_state.price_details = {
                                "Base Price": price,
                                "Overage Cost": overage_cost,
                                "Total Price": total_price,
                            }

        else:
            # If not tax-related, only trigger the proposal model
            st.success("This proposal is not related to tax. Here's your response:")
            st.session_state.final_response = response
            st.session_state.show_final_response = True

# Display the final combined response only after details are submitted
if st.session_state.show_final_response:
    st.subheader("Final Combined Response")
    st.json(st.session_state.final_response)

    # # Only show price details for tax-related inputs
    # if is_tax_related(st.session_state.user_input):
    #     st.subheader("Final Price Details:")
    #     if st.session_state.price_details:
    #         st.write("Base Price:", st.session_state.price_details.get("Base Price", "N/A"))
    #         st.write("Overage Cost:", st.session_state.price_details.get("Overage Cost", "N/A"))
    #         st.write("Total Price:", st.session_state.price_details.get("Total Price", "N/A"))
    #     else:
    #         st.write("No price details available.")
