import streamlit as st
import openai
import numpy as np
import matplotlib.pyplot as plt

# Secure API key from Streamlit Secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Streamlit App Code Generator with AI", layout="centered")

st.title("🔧 AI Streamlit Code Generator with Live Preview")

st.write("Describe what you want your Streamlit app to do. The AI will generate valid, minimal Streamlit code based on your prompt.")

# User prompt input
user_prompt = st.text_input("What do you want the app to do?", placeholder="e.g., create a graph of sine and cosine")

if st.button("Generate Streamlit Code"):

    if user_prompt:
        with st.spinner("Generating concise, context-aware code with AI..."):

            try:
                client = openai.Client()

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": (
                            "You are an expert Python developer generating concise, valid Streamlit code for use inside an existing app. "
                            "Your code will be inserted dynamically using exec(), within an already running Streamlit app. "
                            "The following modules are already imported and available: "
                            "'import streamlit as st', 'import numpy as np', 'import matplotlib.pyplot as plt'. "
                            "Do NOT include import statements. Use 'st', 'np', and 'plt' directly as they are pre-defined. "
                            "Your code should: "
                            "- Define Streamlit widgets if needed (e.g., st.slider) "
                            "- Plot graphs using plt.figure() or plt.subplots() "
                            "- Display figures with st.pyplot(plt.gcf()) or st.pyplot(fig) "
                            "- Ensure all variables used are defined within your code block "
                            "Output ONLY valid, executable Python code. Do not include explanations, markdown, comments, or additional text."
                        )},
                        {"role": "user", "content": f"Write Streamlit code that {user_prompt}"},
                    ],
                    max_tokens=800
                )

                generated_code = response.choices[0].message.content.strip()

                # Clean up unintended markdown formatting
                generated_code = generated_code.replace("```python", "").replace("```", "").strip()

                st.success("Here's your generated Streamlit code:")
                st.code(generated_code, language="python")

                st.divider()
                st.subheader("Live Preview Below:")

                # Provide existing modules for execution
                exec_environment = {
                    "st": st,
                    "np": np,
                    "plt": plt,
                    "__builtins__": __builtins__,
                }

                with st.container():
                    try:
                        exec(generated_code, exec_environment)
                    except Exception as e:
                        st.error(f"Error running preview: {e}")

            except Exception as e:
                st.error(f"Error generating code: {e}")

    else:
        st.warning("Please enter a prompt to continue.")
