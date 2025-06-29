import streamlit as st

st.set_page_config(page_title="Streamlit App Code Generator", layout="centered")

st.title("🔧 AI Streamlit Code Generator with Live Preview (Test Mode)")

st.write("Describe what you want your Streamlit app to do. The AI will generate Streamlit code based on your prompt.")

# User input
user_prompt = st.text_input("What do you want the app to do?", placeholder="e.g., create a graph of sine and cosine")

# Button to trigger code generation
if st.button("Generate Streamlit Code"):

    if user_prompt:
        with st.spinner("Generating code..."):
            
            # Simulated AI-generated code for testing
            generated_code = f"""
import streamlit as st

st.title("Example App: {user_prompt}")

st.write("This is a preview based on your description.")
"""
            st.success("Here's your generated Streamlit code:")
            st.code(generated_code, language="python")

            st.divider()
            st.subheader("Live Preview Below:")

            # Extract only the runnable part to avoid re-imports
            preview_code = f"""
st.title("Example App: {user_prompt}")
st.write("This is a preview based on your description.")
"""

            with st.container():
                try:
                    exec(preview_code)
                except Exception as e:
                    st.error(f"Error running preview: {e}")

    else:
        st.warning("Please enter a prompt to continue.")
