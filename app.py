import streamlit as st
import openai
import os

# Optional: Pull API key from Streamlit secrets if deploying later
# openai.api_key = st.secrets["OPENAI_API_KEY"]

# For local testing - replace with your actual key temporarily
openai.api_key = os.getenv("OPENAI_API_KEY")  # Recommended: set as environment variable

st.set_page_config(page_title="Streamlit App Code Generator", layout="centered")

st.title("🔧 AI Streamlit Code Generator")

st.write("Describe what you want your Streamlit app to do. The AI will generate Streamlit code based on your prompt.")

# User input
user_prompt = st.text_input("What do you want the app to do?", placeholder="e.g., create a graph of sine and cosine")

# Generate button
if st.button("Generate Streamlit Code"):
    if user_prompt:
        with st.spinner("Generating code..."):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are an expert at writing valid, complete Streamlit Python code. Only output the code, no explanations."},
                        {"role": "user", "content": f"Write Streamlit code that {user_prompt}"},
                    ],
                    max_tokens=500
                )
                generated_code = response.choices[0].message.content.strip()
                
                st.success("Here's your generated Streamlit code:")
                st.code(generated_code, language="python")
            
            except Exception as e:
                st.error(f"Error generating code: {e}")
    else:
        st.warning("Please enter a prompt to continue.")
