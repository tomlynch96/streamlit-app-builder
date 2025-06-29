import streamlit as st
import openai
import numpy as np
import matplotlib.pyplot as plt
import uuid

# Secure API key from Streamlit Secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="AI Streamlit App Builder", layout="centered")

st.title("🔧 AI Streamlit App Generator — Iterative, Safe, User-Friendly")

# --------------------------
# Initialise session state
# --------------------------
if "conversation" not in st.session_state:
    st.session_state.conversation = [
        {"role": "system", "content": (
            "You are an expert Python developer generating valid, concise Streamlit code to progressively build an interactive app. "
            "Your responses will be inserted dynamically using exec(), within an existing Streamlit app. "
            "The following modules are already imported: 'streamlit as st', 'numpy as np', 'matplotlib.pyplot as plt'. "
            "Do NOT include import statements. Use 'st', 'np', and 'plt' directly. "
            "When defining Streamlit widgets (e.g., st.slider, st.number_input, st.text_input), you MUST include a unique key argument for each widget, "
            "such as key='slider_damping_abc123'. You may use random or descriptive suffixes to ensure keys are unique. "
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
    st.session_state.initial_prompt_locked = False

# --------------------------
# Define helper functions
# --------------------------
def generate_ai_code():
    """Generates AI code based on full conversation."""
    client = openai.Client()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=st.session_state.conversation,
        max_tokens=800
    )
    code = response.choices[0].message.content.strip()
    code = code.replace("```python", "").replace("```", "").strip()
    return code

def attempt_run_code(code):
    """Attempts to execute code safely. Returns True if successful."""
    exec_environment = {"st": st, "np": np, "plt": plt, "__builtins__": __builtins__}
    try:
        with st.container():
            exec(code, exec_environment)
        return True
    except Exception as e:
        st.error(f"Error in generated code: {e}")
        return False

# --------------------------
# Step 1: Initial Prompt
# --------------------------
if not st.session_state.initial_prompt_locked:
    st.subheader("Step 1: Describe Your App")
    initial_prompt = st.text_input("Describe your app's purpose (cannot be changed):", key="initial_prompt_input")

    if st.button("Generate Initial App") and initial_prompt:
        st.session_state.conversation.append({"role": "user", "content": initial_prompt})
        code = generate_ai_code()
        st.session_state.new_code_attempt = code

        if attempt_run_code(code):
            st.session_state.generated_code = code
            st.session_state.conversation.append({"role": "assistant", "content": code})
            st.session_state.initial_prompt_locked = True
            st.success("Initial app generated successfully.")
        else:
            st.warning("Please revise your prompt and try again.")

# --------------------------
# Step 2: Main Iterative Builder
# --------------------------
if st.session_state.generated_code:
    st.divider()
    st.success("Current Working App Code:")
    st.code(st.session_state.generated_code, language="python")

    st.divider()
    st.subheader("Live App Preview:")

    if attempt_run_code(st.session_state.generated_code):
        st.info("You can refine your app using additional prompts.")

    st.divider()
    st.subheader("Step 3: Refine Your App")

    follow_up = st.text_input("Add features, improvements, or fixes:", key="follow_up_prompt")

    if st.button("Update App with Prompt") and follow_up:
        st.session_state.conversation.append({"role": "user", "content": follow_up})
        code = generate_ai_code()
        st.session_state.new_code_attempt = code

        if attempt_run_code(code):
            st.session_state.generated_code = code
            st.session_state.conversation.append({"role": "assistant", "content": code})
            st.success("App updated successfully.")
        else:
            st.warning("Automatically sending error to AI for correction...")
            st.session_state.conversation.append({
                "role": "user",
                "content": f"The last version failed with an error. Please fix it. Error details: {code[:100]}..."
            })
            code = generate_ai_code()
            st.session_state.new_code_attempt = code

            if attempt_run_code(code):
                st.session_state.generated_code = code
                st.session_state.conversation.append({"role": "assistant", "content": code})
                st.success("AI corrected the error and updated the app.")
            else:
                st.error("Second attempt also failed. Keeping last working version.")

# --------------------------
# Optional: Reset Button
# --------------------------
st.divider()
with st.expander("⚙️ Reset App (Start Over)"):
    if st.button("Reset All Progress"):
        st.session_state.clear()
        st.experimental_rerun()
