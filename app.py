import streamlit as st

st.set_page_config(page_title="Streamlit App Code Generator", layout="centered")

st.title("🔧 AI Streamlit Code Generator (Test Mode)")

st.write("Describe what you want your Streamlit app to do. The AI will generate Streamlit code based on your prompt.")

user_prompt = st.text_input("What do you want the app to do?", placeholder="e.g., create a graph of sine and cosine")

if st.button("Generate Streamlit Code"):
    if user_prompt:
        with st.spinner("Pretending to generate code..."):
            # Simulate generated code
            generated_code = f"""
import streamlit as st

st.title("Example App: {user_prompt}")

st.write("This is a placeholder Streamlit app based on your description.")
"""
            st.success("Here's your generated Streamlit code (test output):")
            st.code(generated_code, language="python")

    else:
        st.warning("Please enter a prompt to continue.")
