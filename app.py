import streamlit as st
import openai
import os

# Set your OpenAI API key (or use st.secrets for deployment)
openai.api_key = os.getenv("OPENAI_API_KEY")  # Or set as a string temporarily

st.title("AI Streamlit Code Generator")

# User prompt input
user_prompt = st.text_input("Describe what you want your Streamlit app to do:")

# Generate button
if st.button("Generate Code"):
    if user_prompt:
        with st.spinner("Generating code..."):
            # Call OpenAI to generate Streamlit code
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert Streamlit app generator. Respond ONLY with valid Python Streamlit code."},
                    {"role": "user", "content": f"Create Streamlit code that {user_prompt}"},
                ],
                max_tokens=500
            )

            generated_code = response.choices[0].message.content.strip()

            st.success("Code generated!")
            st.code(generated_code, language="python")
    else:
        st.warning("Please enter a prompt first.")
