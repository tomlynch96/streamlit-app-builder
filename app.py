import streamlit as st
import openai

# Secure API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Streamlit App Code Generator with AI", layout="centered")

st.title("🔧 AI Streamlit Code Generator with Live Preview")

st.write("Describe what you want your Streamlit app to do. The AI will generate valid Streamlit code based on your prompt.")

# User input
user_prompt = st.text_input("What do you want the app to do?", placeholder="e.g., create a graph of sine and cosine")

# Generate button
if st.button("Generate Streamlit Code"):

    if user_prompt:
        with st.spinner("Generating code with AI..."):

            try:
                # New OpenAI 1.0+ syntax
                client = openai.Client()

                response = client.chat.completions.create(
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

                st.divider()
                st.subheader("Live Preview Below:")

                # Extract only runnable code (skip imports)
                safe_preview = "\n".join([
                    line for line in generated_code.split("\n")
                    if not line.strip().startswith("import")
                ])

                with st.container():
                    try:
                        exec(safe_preview)
                    except Exception as e:
                        st.error(f"Error running preview: {e}")

            except Exception as e:
                st.error(f"Error generating code: {e}")

    else:
        st.warning("Please enter a prompt to continue.")
