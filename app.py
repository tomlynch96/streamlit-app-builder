import streamlit as st
import openai
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import uuid
import time
import ast
import re
import traceback
from functools import wraps
from datetime import datetime

# Secure API key from Streamlit Secrets
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    st.error("⚠️ OpenAI API key not found in secrets. Please configure OPENAI_API_KEY in your Streamlit secrets.")
    st.stop()

st.set_page_config(
    page_title="AI Streamlit App Builder", 
    layout="centered",
    page_icon="🔧",
    initial_sidebar_state="expanded"
)

# --------------------------
# Security & Validation Functions
# --------------------------

def validate_code_safety(code):
    """Validate generated code for safety and allowed operations"""
    if not code or not isinstance(code, str):
        return False
    
    # Check for critically dangerous patterns only
    dangerous_patterns = [
        r'import\s+os\b', r'import\s+sys\b', r'import\s+subprocess\b',
        r'import\s+requests\b', r'import\s+urllib\b', r'import\s+socket\b',
        r'__import__\s*\(', r'eval\s*\(', r'exec\s*\(', 
        r'compile\s*\(', r'exit\s*\(', r'quit\s*\('
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return False
    
    # Check for standalone import statements (not part of strings or comments)
    lines = code.split('\n')
    for line in lines:
        stripped = line.strip()
        # Skip comments and strings
        if stripped.startswith('#') or stripped.startswith('"') or stripped.startswith("'"):
            continue
        
        # Check for dangerous imports
        if re.match(r'^\s*import\s+(os|sys|subprocess|requests|urllib|socket)\b', stripped, re.IGNORECASE):
            return False
        if re.match(r'^\s*from\s+(os|sys|subprocess|requests|urllib|socket)\b', stripped, re.IGNORECASE):
            return False
    
    # Basic AST validation for syntax
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def rate_limit(max_calls_per_minute=15):
    """Rate limiting decorator for API calls"""
    def decorator(func):
        if not hasattr(func, 'calls'):
            func.calls = []
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            func.calls[:] = [call for call in func.calls if now - call < 60]
            
            if len(func.calls) >= max_calls_per_minute:
                st.error(f"⏱️ Rate limit exceeded. Please wait before making more requests.")
                return None
            
            func.calls.append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator

# --------------------------
# Session State Management
# --------------------------

def initialize_session_state():
    """Initialize session state with safe defaults"""
    defaults = {
        "conversation": [create_system_message()],
        "generated_code": "",
        "code_history": [],
        "app_metadata": {
            "created_at": datetime.now().isoformat(),
            "version": 1,
            "total_iterations": 0
        },
        "initial_prompt_locked": False,
        "last_successful_code": "",
        "api_calls_made": 0
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def create_system_message():
    """Create system message for AI with safety guidelines"""
    return {
        "role": "system", 
        "content": f"""You are an expert Streamlit developer creating safe, interactive apps.

STRICT RULES:
- Use ONLY these modules: streamlit (st), numpy (np), matplotlib.pyplot (plt), pandas (pd)
- NO import statements whatsoever
- ALL widgets MUST have unique keys using format: key='widget_name_{uuid.uuid4().hex[:8]}'
- Use st.pyplot(fig) for matplotlib plots, always create figure with plt.figure() or plt.subplots()
- Handle all errors gracefully with try/except blocks
- Use st.session_state for persistent data
- Keep code clean, readable, and under 100 lines when possible
- Add helpful comments for complex logic
- Use descriptive variable names

ABSOLUTELY FORBIDDEN:
- File operations, network requests, system calls
- eval(), exec(), __import__(), open(), file()
- Global variables outside functions
- Dangerous operations or security risks

WIDGET KEY EXAMPLES:
- st.slider("Label", min_val, max_val, key=f'slider_{uuid.uuid4().hex[:8]}')
- st.text_input("Label", key=f'input_{uuid.uuid4().hex[:8]}')

OUTPUT: Only clean, executable Python code with no explanations or markdown."""
    }

# --------------------------
# AI Code Generation
# --------------------------

@rate_limit(max_calls_per_minute=12)
def generate_ai_code():
    """Generate AI code with error handling and validation"""
    try:
        client = openai.Client()
        
        # Limit conversation history to prevent token overflow
        limited_conversation = st.session_state.conversation[-10:]  # Last 10 messages
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=limited_conversation,
            max_tokens=1200,
            temperature=0.1,  # Lower temperature for more consistent code
            top_p=0.9
        )
        
        code = response.choices[0].message.content.strip()
        
        # Clean up the code
        code = code.replace("```python", "").replace("```", "").strip()
        
        # Remove markdown formatting but keep comments with 'key=' or other important info
        lines = code.split('\n')
        cleaned_lines = []
        for line in lines:
            # Keep all lines except pure comment lines without code context
            if line.strip() and not (line.strip().startswith('#') and 'key=' not in line and len(line.strip()) > 50):
                cleaned_lines.append(line)
        
        code = '\n'.join(cleaned_lines)
        
        st.session_state.api_calls_made += 1
        return code
        
    except Exception as e:
        st.error(f"🔴 OpenAI API Error: {str(e)}")
        return None

# --------------------------
# Code Execution
# --------------------------

def attempt_run_code(code):
    """Safely execute generated code with restricted environment"""
    if not code:
        return False
    
    # Validate code safety first
    if not validate_code_safety(code):
        st.error("🚨 Generated code contains potentially unsafe operations and was blocked.")
        st.info("💡 This usually happens when the AI tries to use forbidden imports or operations.")
        
        # Show what was blocked for debugging
        with st.expander("🔍 Debug: What was blocked?"):
            st.code(code, language="python")
            st.write("**Common issues:**")
            st.write("- Trying to import forbidden modules (os, sys, subprocess, etc.)")
            st.write("- Using eval(), exec(), or other dangerous functions")
            st.write("- Malformed code syntax")
        
        return False
    
    # Create restricted execution environment
    exec_environment = {
        "st": st,
        "np": np,
        "plt": plt,
        "pd": pd,
        "uuid": uuid,
        "time": time,
        "datetime": datetime,
        "__builtins__": {
            "range": range,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "min": min,
            "max": max,
            "sum": sum,
            "abs": abs,
            "round": round,
            "enumerate": enumerate,
            "zip": zip,
            "isinstance": isinstance,
            "type": type,
            "print": print
        }
    }
    
    try:
        # Execute in a container for better error isolation
        with st.container():
            exec(code, exec_environment)
        return True
        
    except Exception as e:
        st.error(f"💥 Code Execution Error: {str(e)}")
        
        # Show debugging info in expander
        with st.expander("🔍 Debug Information"):
            st.code(traceback.format_exc(), language="python")
            st.subheader("Problematic Code:")
            st.code(code, language="python")
        
        return False

# --------------------------
# UI Helper Functions
# --------------------------

def save_code_to_history(code, prompt=""):
    """Save code version to history"""
    if code and code != st.session_state.get("last_successful_code", ""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.code_history.append({
            "timestamp": timestamp,
            "code": code,
            "prompt": prompt,
            "version": len(st.session_state.code_history) + 1
        })
        st.session_state.last_successful_code = code
        
        # Limit history to last 10 versions
        if len(st.session_state.code_history) > 10:
            st.session_state.code_history = st.session_state.code_history[-10:]

def display_app_stats():
    """Display app statistics in sidebar"""
    with st.sidebar:
        st.subheader("📊 App Statistics")
        stats = st.session_state.app_metadata
        
        st.metric("Versions Created", len(st.session_state.code_history))
        st.metric("API Calls Made", st.session_state.api_calls_made)
        st.metric("Current Version", stats.get("version", 1))
        
        if st.session_state.code_history:
            st.write("**Latest Update:**")
            st.write(st.session_state.code_history[-1]["timestamp"])

def show_code_history():
    """Display code history with revert functionality"""
    if st.session_state.code_history:
        with st.expander("📝 Version History", expanded=False):
            for i, entry in enumerate(reversed(st.session_state.code_history)):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Version {entry['version']}** - {entry['timestamp']}")
                    if entry['prompt']:
                        st.write(f"*Prompt: {entry['prompt'][:50]}...*")
                    st.code(entry['code'][:200] + "..." if len(entry['code']) > 200 else entry['code'], 
                           language="python")
                
                with col2:
                    if st.button(f"Revert", key=f"revert_{i}"):
                        st.session_state.generated_code = entry['code']
                        st.success(f"✅ Reverted to Version {entry['version']}")
                        st.rerun()

# --------------------------
# Main Application
# --------------------------

def main():
    # Initialize session state
    initialize_session_state()
    
    # Title and description
    st.title("🔧 AI Streamlit App Generator")
    st.markdown("### *Iterative, Safe, User-Friendly*")
    
    # Sidebar with stats and controls
    display_app_stats()
    
    with st.sidebar:
        st.divider()
        if st.button("🔄 Reset All", type="secondary"):
            st.session_state.clear()
            st.rerun()
        
        st.divider()
        with st.expander("ℹ️ How to Use"):
            st.markdown("""
            1. **Describe** your app idea
            2. **Generate** initial version
            3. **Refine** with additional prompts
            4. **Iterate** until perfect!
            
            **Safe Features:**
            - Code validation
            - Rate limiting
            - Error handling
            - Version history
            """)
    
    # --------------------------
    # Step 1: Initial Prompt
    # --------------------------
    if not st.session_state.initial_prompt_locked:
        st.subheader("🎯 Step 1: Describe Your App")
        st.markdown("*What kind of interactive app would you like to create?*")
        
        # Example prompts
        with st.expander("💡 Example Prompts"):
            examples = [
                "Create a calculator with basic math operations",
                "Build a data visualization dashboard with sample data",
                "Make an interactive plot with sliders for parameters",
                "Create a simple game or quiz app",
                "Build a form with validation and results display"
            ]
            for example in examples:
                if st.button(f"📝 {example}", key=f"example_{hash(example)}"):
                    st.session_state.temp_prompt = example
        
        initial_prompt = st.text_area(
            "Describe your app's purpose:",
            value=st.session_state.get("temp_prompt", ""),
            placeholder="E.g., Create a mortgage calculator with sliders for loan amount, interest rate, and term...",
            height=100,
            key="initial_prompt_input"
        )
        
        col1, col2 = st.columns([2, 1])
        with col1:
            generate_button = st.button("🚀 Generate Initial App", type="primary", disabled=not initial_prompt)
        with col2:
            st.write(f"**Characters:** {len(initial_prompt)}/500")
        
        if generate_button and initial_prompt:
            with st.spinner("🤖 AI is generating your app..."):
                st.session_state.conversation.append({"role": "user", "content": initial_prompt})
                code = generate_ai_code()
                
                if code:
                    if attempt_run_code(code):
                        st.session_state.generated_code = code
                        st.session_state.conversation.append({"role": "assistant", "content": code})
                        st.session_state.initial_prompt_locked = True
                        st.session_state.app_metadata["version"] = 1
                        save_code_to_history(code, initial_prompt)
                        st.success("✅ Initial app generated successfully!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Generated code had issues. Please try a different description.")
                else:
                    st.error("❌ Failed to generate code. Please check your API key and try again.")
    
    # --------------------------
    # Step 2: Main App Display
    # --------------------------
    if st.session_state.generated_code:
        st.divider()
        
        # Show current code
        with st.expander("💻 Current App Code", expanded=False):
            st.code(st.session_state.generated_code, language="python")
            
            # Copy to clipboard button
            st.markdown("```python\n" + st.session_state.generated_code + "\n```")
        
        st.divider()
        
        # Live preview
        st.subheader("🎨 Live App Preview")
        preview_container = st.container()
        
        with preview_container:
            with st.spinner("Rendering your app..."):
                success = attempt_run_code(st.session_state.generated_code)
                if success:
                    st.success("✅ App is running perfectly!")
                else:
                    st.error("❌ App encountered an error")
        
        st.divider()
        
        # --------------------------
        # Step 3: Iterative Refinement
        # --------------------------
        st.subheader("🔧 Step 3: Refine Your App")
        st.markdown("*Add features, fix issues, or improve functionality*")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            follow_up = st.text_area(
                "What would you like to change or add?",
                placeholder="E.g., Add a chart showing the results, change the color scheme, add input validation...",
                height=80,
                key="follow_up_prompt"
            )
        
        with col2:
            st.write("**Quick Actions:**")
            if st.button("🎨 Improve UI", key="improve_ui"):
                st.session_state.temp_followup = "Make the UI more attractive with better colors and layout"
            if st.button("📊 Add Charts", key="add_charts"):
                st.session_state.temp_followup = "Add meaningful data visualizations and charts"
            if st.button("🔧 Fix Issues", key="fix_issues"):
                st.session_state.temp_followup = "Fix any bugs or improve error handling"
        
        # Use temp followup if set
        if st.session_state.get("temp_followup"):
            follow_up = st.session_state.temp_followup
            st.session_state.temp_followup = ""
        
        if st.button("🔄 Update App", type="primary", disabled=not follow_up) and follow_up:
            with st.spinner("🤖 AI is updating your app..."):
                st.session_state.conversation.append({"role": "user", "content": follow_up})
                code = generate_ai_code()
                
                if code:
                    if attempt_run_code(code):
                        st.session_state.generated_code = code
                        st.session_state.conversation.append({"role": "assistant", "content": code})
                        st.session_state.app_metadata["version"] += 1
                        save_code_to_history(code, follow_up)
                        st.success("✅ App updated successfully!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Update failed. Trying auto-correction...")
                        
                        # Auto-correction attempt
                        correction_prompt = f"The last code update failed with errors. Please fix the issues and provide working code. The user requested: {follow_up}"
                        st.session_state.conversation.append({"role": "user", "content": correction_prompt})
                        
                        corrected_code = generate_ai_code()
                        if corrected_code and attempt_run_code(corrected_code):
                            st.session_state.generated_code = corrected_code
                            st.session_state.conversation.append({"role": "assistant", "content": corrected_code})
                            save_code_to_history(corrected_code, f"Auto-fix: {follow_up}")
                            st.success("✅ AI auto-corrected the issues!")
                            st.rerun()
                        else:
                            st.error("❌ Auto-correction failed. Keeping previous working version.")
                else:
                    st.error("❌ Failed to generate updated code.")
        
        # Show version history
        show_code_history()

# --------------------------
# Run the application
# --------------------------
if __name__ == "__main__":
    main()
