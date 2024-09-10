import os
import streamlit as st
import openai
from dotenv import load_dotenv
import time
import chardet

# Load environment variables
load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")
assistant_id = os.environ.get("ASSISTANT_ID")

# Initialize OpenAI client
client = openai.OpenAI()

def main():
    st.title("Contract Checking Assistant")

    # Validate API key and assistant ID
    if not openai.api_key or not assistant_id:
        st.error("Please ensure that OPENAI_API_KEY and ASSISTANT_ID are set in your environment variables.")
        return

    # Upload contract file
    uploaded_file = st.file_uploader("Upload Contract File")
    user_message = st.text_input("Enter your message with the contract:")

    if uploaded_file is not None and user_message:
        try:
            # Detect file encoding
            raw_data = uploaded_file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            
            if encoding is None:
                raise ValueError("Encoding could not be detected. Trying common encodings.")
            
            contract_text = raw_data.decode(encoding)
        except Exception as e:
            # Try common encodings if detection fails
            for enc in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    contract_text = raw_data.decode(enc)
                    break
                except Exception:
                    continue
            else:
                st.error(f"Error reading the file: {e}")
                return

        # Check usage limit
        usage_limit = check_usage_limit()
        if usage_limit == 0:
            st.error("Usage limit reached. Please try again later.")
            return

        # Create a thread
        st.write("Creating a thread...")
        thread = client.beta.threads.create()
        st.write(f"Thread created with ID: {thread.id}")

        # Send the contract text and user message to the thread
        st.write("Sending contract text and user message to the thread...")
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"{user_message}\n\n{contract_text}"
        )
        st.write("Message sent to the thread.")

        # Call the assistant's function
        st.write("Calling the assistant's function...")
        response = client.beta.assistants.runs.create(
            assistant_id=assistant_id,
            thread_id=thread.id,
            function_call={"name": "contract_check", "arguments": {"contract_text": contract_text}}
        )
        st.write("Assistant's function called.")

        # Wait for the response
        while response.status != "completed":
            time.sleep(1)
            response = client.beta.assistants.runs.retrieve(
                assistant_id=assistant_id,
                run_id=response.id
            )

        # Display the assistant's response
        st.text_area("Assistant Response", value=response.outputs[0].text)

        # Chat with the assistant
        while True:
            user_message = st.text_input("Enter your message:")
            if user_message:
                st.write("Sending user message to the thread...")
                message = client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=user_message
                )
                st.write("User message sent to the thread.")

                # Wait for the response
                while response.status != "completed":
                    time.sleep(1)
                    response = client.beta.assistants.runs.retrieve(
                        assistant_id=assistant_id,
                        run_id=response.id
                    )

                # Display the assistant's response
                st.text_area("Assistant Response", value=response.outputs[0].text)

def check_usage_limit():
    # Placeholder function to check usage limit
    # Replace with actual implementation to check usage limit from OpenAI API
    return 1  # Assume usage limit is not zero for this example

if __name__ == "__main__":
    main()
