import streamlit as st
import openai
import numpy as np
import matplotlib.pyplot as plt

# Secure API key from Streamlit Secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Streamlit AI App Generator with Safe Keys", layout="centered")

st.title("🔧 AI Streamlit App Generator — Unique Keys, Auto-Correction")

st.write("Describe what you want your app to do. You can iteratively refine your app. Errors are automatically sent to AI for correction. All widgets will have unique keys to prevent errors.")

# Initialise session state
if "conversation" not in st.session_state:
    st.session_state.conversation = [
        {"role": "system", "content": (
            "You are an expert Python developer generating valid, concise Streamlit code to progressively build an interactive app. "
            "Your responses will be inserted dynamically using exec(), within an existing Streamlit app. "
            "The following modules are already imported: 'streamlit as st', 'numpy as np', 'matplotlib.pyplot as plt'. "
            "Do NOT include import statements. Use 'st', 'np', and 'plt' directly. "
            "When defining Streamlit widgets (e.g., st.slider, st.number_input, st.text_input), you MUST include a unique key argument for each widget, "
            "such as key='slider_damping', key='input_speed', or key='my_unique_slider'. Do not reuse the same key for multiple widgets. "
            "Your code should: "
            "- Define Streamlit widgets with unique keys "
            "- Plot graphs using plt.figure() or plt.subplots() "
            "- Display figures with st.pyplot(plt.gcf()) or st.pyplot(fig) "
            "- Ensure all variables used are defined within your code block "
            "Output ONLY valid, executable Python code. Do not include explanations, markdown, comments, or additional text."
        )}
    ]
    st.session_state.generated_code = ""
    st.session_state.new_code_attempt = ""

# Get initial prompt if not provided
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
            st.session_state.new_code_attempt = ai_message

            exec_environment = {"st": st, "np": np, "plt": plt, "__builtins__": __builtins__}
            with st.container():
                try:
                    exec(st.session_state.new_code_attempt, exec_environment)
                    st.session_state.generated_code = st.session_state.new_code_attempt
                    st.session_state.conversation.append({"role": "assistant", "content": ai_message})
                    st.success("App generated successfully.")
                except Exception as e:
                    st.error(f"Error in generated code: {e}")
                    st.warning("Fix your prompt and try again. Last working version retained.")

# Show last working version
if st.session_state.generated_code:
    st.success("Current Working Code:")
    st.code(st.session_state.generated_code, language="python")

    st.divider()
    st.subheader("Live Preview Below:")

    exec_environment = {"st": st, "np": np, "plt": plt, "__builtins__": __builtins__}
    with st.container():
        try:
            exec(st.session_state.generated_code, exec_environment)
        except Exception as e:
            st.error(f"Unexpected error running last working version: {e}")

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
            st.session_state.new_code_attempt = ai_message

        with st.container():
            try:
                exec(st.session_state.new_code_attempt, exec_environment)
                st.session_state.generated_code = st.session_state.new_code_attempt
                st.session_state.conversation.append({"role": "assistant", "content": ai_message})
                st.success("App updated successfully.")
            except Exception as e:
                st.error(f"Error in generated code: {e}")
                st.warning("Automatically sending error to AI for correction...")

                st.session_state.conversation.append({
                    "role": "user",
                    "content": f"The last version failed with this error: {e}. Please fix it."
                })

                with st.spinner("AI attempting automatic correction..."):
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=st.session_state.conversation,
                        max_tokens=800
                    )
                    ai_message = response.choices[0].message.content.strip()
                    ai_message = ai_message.replace("```python", "").replace("```", "").strip()
                    st.session_state.new_code_attempt = ai_message

                try:
                    exec(st.session_state.new_code_attempt, exec_environment)
                    st.session_state.generated_code = st.session_state.new_code_attempt
                    st.session_state.conversation.append({"role": "assistant", "content": ai_message})
                    st.success("AI corrected the error and updated the app.")
                except Exception as e2:
                    st.error(f"Second attempt also failed: {e2}")
                    st.warning("Last working version retained. Please refine manually.")
