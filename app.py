import streamlit as st
import openai
import numpy as np
import matplotlib.pyplot as plt

# Secure API key from Streamlit Secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Streamlit AI App Generator with Dialogue", layout="centered")

st.title("🔧 AI Streamlit App Generator — Iterative Builder")

st.write("Describe what you want your app to do. You can then add more prompts to refine the app, building the code step by step. Your original description cannot be deleted.")

# Initialise conversation and code state
if "conversation" not in st.session_state:
    st.session_state.conversation = [
        {"role": "system", "content": (
            "You are an expert Python developer generating valid, concise Streamlit code to progressively build an interactive app. "
            "Your responses will be inserted dynamically using exec(), within an existing Streamlit app. "
            "The following modules are already imported: 'streamlit as st', 'numpy as np', 'matplotlib.pyplot as plt'. "
            "Do NOT include import statements. Use 'st', 'np', and 'plt' directly. "
            "Your code should: "
            "- Define Streamlit widgets if needed (e.g., st.slider) "
            "- Plot graphs using plt.figure() or plt.subplots() "
            "- Display figures with st.pyplot(plt.gcf()) or st.pyplot(fig) "
            "- Ensure all variables used are defined within your code block "
            "Output ONLY valid, executable Python code. Do not include explanations, markdown, comments, or additional text."
        )}
    ]
    st.session_state.generated_code = ""

# Get initial prompt if not already provided
if not any(msg["role"] == "user" for msg in st.session_state.conversation[1:]):
    initial_prompt = st.text_input("Describe your app's purpose (cannot be changed):", key="initial_prompt")
    if st.button("Generate Initial Code") and initial_prompt:
        st.session_state.conversation.append({"role": "user", "content": initial_prompt})
        
        with st.spinner("Generating code..."):
            client = openai.Client()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=st.session_state.conversation,
                max_tokens=800
            )
            ai_message = response.choices[0].message.content.strip()
            ai_message = ai_message.replace("```python", "").replace("```", "").strip()

            st.session_state.conversation.append({"role": "assistant", "content": ai_message})
            st.session_state.generated_code = ai_message

# Show existing code if generated
if st.session_state.generated_code:
    st.success("Current Generated Code:")
    st.code(st.session_state.generated_code, language="python")

    st.divider()
    st.subheader("Live Preview Below:")

    exec_environment = {"st": st, "np": np, "plt": plt, "__builtins__": __builtins__}

    with st.container():
        try:
            exec(st.session_state.generated_code, exec_environment)
        except Exception as e:
            st.error(f"Error running preview: {e}")

    st.divider()
    st.subheader("Refine Your App")

    follow_up = st.text_input("Add more to your app (new feature, improvement, etc.):", key="follow_up_prompt")
    if st.button("Update App with New Prompt") and follow_up:
        st.session_state.conversation.append({"role": "user", "content": follow_up})

        with st.spinner("Generating updated code..."):
            client = openai.Client()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=st.session_state.conversation,
                max_tokens=800
            )
            ai_message = response.choices[0].message.content.strip()
            ai_message = ai_message.replace("```python", "").replace("```", "").strip()

            st.session_state.conversation.append({"role": "assistant", "content": ai_message})
            st.session_state.generated_code = ai_message
