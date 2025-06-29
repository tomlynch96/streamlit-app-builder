import streamlit as st
import openai
import numpy as np
import matplotlib.pyplot as plt
import re

# Secure API key from Streamlit Secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Streamlit App Code Generator with AI", layout="centered")

st.title("🔧 AI Streamlit Code Generator with Live Preview")

st.write("Describe what you want your Streamlit app to do. The AI will generate valid, minimal Streamlit code based on your prompt.")

# User prompt input
user_prompt = st.text_input("What do you want the app to do?", placeholder="e.g., create a graph of sine and cosine")

if st.button("Generate Streamlit Code"):

    if user_prompt:
        with st.spinner("Generating concise code with AI..."):

            try:
                client = openai.Client()

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": (
                            "You are an expert at writing short, complete, valid Streamlit Python apps. "
                            "Your responses are strictly limited in token count, so prioritise concise, minimal code that runs correctly. "
                            "Only output valid Python code. Do not include explanations, comments, or extra text."
                        )},
                        {"role": "user", "content": f"Write Streamlit code that {user_prompt}"},
                    ],
                    max_tokens=800
                )

                generated_code = response.choices[0].message.content.strip()

                st.success("Here's your generated Streamlit code:")
                st.code(generated_code, language="python")

                st.divider()
                st.subheader("Live Preview Below:")

                # Auto-fix common AI mistakes before running preview
                corrected_code = generated_code

                # Fix incorrect st.pyplot(plt) calls
                corrected_code = re.sub(r'st\.pyplot\s*\(\s*plt\s*\)', 'st.pyplot(plt.gcf())', corrected_code)

                # Provide existing modules for execution
                exec_environment = {
                    "st": st,
                    "np": np,
                    "plt": plt,
                    "__builtins__": __builtins__,
                }

                with st.container():
                    try:
                        exec(corrected_code, exec_environment)
                    except Exception as e:
                        st.error(f"Error running preview: {e}")

            except Exception as e:
                st.error(f"Error generating code: {e}")

    else:
        st.warning("Please enter a prompt to continue.")
