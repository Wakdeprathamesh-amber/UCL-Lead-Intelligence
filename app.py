"""
Whitelabel Lead Intelligence - Main Streamlit App
UCL Student Lead Intelligence AI Assistant
"""

import streamlit as st
import os
import sys
import json
import subprocess
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import modules
from init_databases import ensure_databases_exist
from ai_agent_simple import SimpleLeadIntelligenceAgent
from auth import get_auth, show_login_page
from audit_logger import get_audit_logger


# Page config
st.set_page_config(
    page_title="UCL Lead Intelligence AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Minimalistic CSS with proper contrast
st.markdown("""
<style>
    /* Main Header */
    .main-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1e293b;
        text-align: left;
        margin-bottom: 1rem;
        padding: 0.5rem 0;
    }
    
    /* Sidebar Styling - Dark Theme */
    [data-testid="stSidebar"] {
        background-color: #1e293b;
        border-right: 1px solid #334155;
        padding: 1rem 1.5rem;
    }
    
    /* Sidebar Headers */
    [data-testid="stSidebar"] h2 {
        color: #ffffff;
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    [data-testid="stSidebar"] h3 {
        color: #e2e8f0;
        font-size: 1.1rem;
        font-weight: 600;
        margin-top: 1rem;
        margin-bottom: 0.75rem;
    }
    
    /* Sidebar Text */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown {
        color: #cbd5e1 !important;
    }
    
    /* Sidebar Metric Cards - Lighter boxes on dark bg */
    [data-testid="stSidebar"] div[data-testid="metric-container"] {
        background-color: #334155;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #475569;
        margin-bottom: 0.5rem;
    }
    
    [data-testid="stSidebar"] div[data-testid="metric-container"] label {
        color: #cbd5e1 !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stSidebar"] div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 1.75rem !important;
        font-weight: 700 !important;
    }
    
    /* Progress Bars in Sidebar - Light on dark */
    [data-testid="stSidebar"] .stProgress {
        margin-bottom: 1rem;
    }
    
    [data-testid="stSidebar"] .stProgress > div {
        background-color: #475569 !important;
    }
    
    [data-testid="stSidebar"] .stProgress > div > div {
        background-color: #60a5fa !important;
    }
    
    /* Sidebar Dividers */
    [data-testid="stSidebar"] hr {
        border-color: #475569 !important;
        opacity: 0.3;
    }
    
    /* Button Styling - Primary */
    .stButton>button {
        width: 100%;
        background-color: #1e293b;
        color: white;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
        border-radius: 0.375rem;
        transition: all 0.2s;
    }
    
    .stButton>button:hover {
        background-color: #334155;
        box-shadow: 0 2px 8px rgba(30, 41, 59, 0.15);
    }
    
    /* Clean chat interface */
    .stChatMessage {
        padding: 1rem 0;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Metric Enhancement */
    div[data-testid="metric-container"] {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
    }
    
    div[data-testid="metric-container"] label {
        color: #64748b !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
    }
    
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #1e293b !important;
        font-size: 1.875rem !important;
        font-weight: 700 !important;
    }
    
    /* Status Badge */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .badge-won { background-color: #dcfce7; color: #166534; }
    .badge-lost { background-color: #fee2e2; color: #991b1b; }
    .badge-opportunity { background-color: #fef3c7; color: #92400e; }
    .badge-contacted { background-color: #dbeafe; color: #1e40af; }
    
    /* Clean Divider */
    hr {
        margin: 1.5rem 0;
        border: none;
        height: 1px;
        background-color: #e2e8f0;
    }
    
    /* Copy Button */
    .copy-button {
        background-color: #10b981 !important;
        color: white !important;
        font-size: 0.875rem !important;
        padding: 0.4rem 0.8rem !important;
    }
    
    /* Chat Input - Clean and Simple */
    .stChatInputContainer {
        padding: 1rem 0;
    }
    
    .stChatInputContainer textarea {
        font-size: 1rem !important;
        min-height: 60px !important;
        padding: 0.75rem !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 0.5rem !important;
    }
    
    .stChatInputContainer textarea:focus {
        border-color: #1e293b !important;
        box-shadow: 0 0 0 2px rgba(30, 41, 59, 0.1) !important;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'mode' not in st.session_state:
    st.session_state.mode = "detailed"  # Default to detailed mode


def get_deployment_version():
    """Get deployment version from VERSION.txt or git"""
    version_file = os.path.join(os.path.dirname(__file__), 'VERSION.txt')
    
    # Try reading from VERSION.txt first (works on Streamlit Cloud)
    if os.path.exists(version_file):
        try:
            with open(version_file, 'r') as f:
                lines = f.read().strip().split('\n')
                if len(lines) >= 1:
                    commit_hash = lines[0].strip()
                    commit_msg = lines[1].strip() if len(lines) > 1 else "unknown"
                    return commit_hash, commit_msg
        except Exception:
            pass
    
    # Fallback: Try git (works locally)
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),
            timeout=2
        )
        if result.returncode == 0:
            commit_hash = result.stdout.strip()
            # Try to get commit message
            try:
                result2 = subprocess.run(
                    ['git', 'log', '-1', '--pretty=format:%s'],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(__file__),
                    timeout=2
                )
                commit_msg = result2.stdout.strip() if result2.returncode == 0 else "unknown"
            except Exception:
                commit_msg = "unknown"
            return commit_hash, commit_msg
    except Exception:
        pass
    
    return "unknown", "unknown"

# Initialize databases and agent
if 'agent' not in st.session_state:
    # First, ensure databases exist
    db_initialized = False
    with st.spinner("📊 Initializing databases..."):
        try:
            ensure_databases_exist()
            # Verify database was created (check both paths)
            db_path = None
            for path in ["data/leads.db", "Data/leads.db"]:
                if os.path.exists(path):
                    db_path = path
                    break
            
            if not db_path:
                raise FileNotFoundError(
                    "Database file not found after initialization. "
                    "Checked: data/leads.db and Data/leads.db"
                )
            
            db_initialized = True
            st.session_state.db_path = db_path
        except Exception as e:
            st.session_state.agent_ready = False
            st.session_state.agent_error = f"Database initialization failed: {str(e)}"
            import traceback
            error_details = traceback.format_exc()
            st.error(f"⚠️ **Database initialization failed**")
            st.code(str(e), language=None)
            st.info("💡 **Tip**: The database should be created automatically from the data files. "
                   "If this error persists, check the deployment logs in Streamlit Cloud dashboard.")
            st.stop()
    
    # Then initialize agent (only if database was initialized)
    if db_initialized:
        with st.spinner("🚀 Initializing AI Agent..."):
            try:
                db_path = st.session_state.get('db_path', 'data/leads.db')
                st.session_state.agent = SimpleLeadIntelligenceAgent(db_path=db_path)
                st.session_state.agent_ready = True
                st.session_state.messages = []
            except Exception as e:
                st.session_state.agent_ready = False
                st.session_state.agent_error = str(e)
                import traceback
                st.error(f"⚠️ **Agent initialization failed**: {str(e)}")
                st.code(traceback.format_exc(), language='python')

def main():
    """Main app function"""
    
    # Check authentication
    auth = get_auth()
    if not auth.is_authenticated():
        show_login_page()
        return
    
    # Log access
    audit_logger = get_audit_logger()
    audit_logger.log_access(
        action="app_access",
        resource="main_app",
        success=True,
        user_id=auth.get_username() or "anonymous",
        session_id=auth.get_session_id()
    )
    
    # Minimal header with logout
    col1, col2 = st.columns([10, 1])
    with col1:
        st.markdown('<div class="main-header">UCL Lead Intelligence</div>', unsafe_allow_html=True)
    with col2:
        if st.button("🚪 Logout"):
            auth.logout()
            st.rerun()
    
    # Sidebar - Mode Selection
    with st.sidebar:
        # Mode Toggle
        st.markdown("### 🔄 Data Mode")
        mode_options = {
            "detailed": "💬 Detailed (402 leads)",
            "aggregate": "📊 Aggregate (1,525 leads)"
        }
        
        current_mode_label = mode_options[st.session_state.mode]
        new_mode = st.radio(
            "Select data mode:",
            options=["detailed", "aggregate"],
            format_func=lambda x: mode_options[x],
            index=0 if st.session_state.mode == "detailed" else 1,
            key="mode_selector"
        )
        
        if new_mode != st.session_state.mode:
            st.session_state.mode = new_mode
            # Force re-initialization
            if 'agent' in st.session_state:
                del st.session_state.agent
            if 'agent_mode' in st.session_state:
                del st.session_state.agent_mode
            if 'query_tools' in st.session_state:
                del st.session_state.query_tools
            if 'query_tools_mode' in st.session_state:
                del st.session_state.query_tools_mode
            st.rerun()
        
        # Version Display
        st.markdown("---")
        st.markdown("### 📦 Deployment Info")
        commit_hash, commit_msg = get_deployment_version()
        
        st.markdown(f"**Commit:** `{commit_hash}`")
        if commit_msg != "unknown":
            st.caption(f"_{commit_msg[:50]}{'...' if len(commit_msg) > 50 else ''}_")
        
        # Check if this matches latest on GitHub (only works locally)
        try:
            result = subprocess.run(
                ['git', 'fetch', 'origin', 'main', '--quiet'],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__),
                timeout=5
            )
            result2 = subprocess.run(
                ['git', 'rev-parse', '--short', 'origin/main'],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__),
                timeout=2
            )
            if result2.returncode == 0:
                remote_hash = result2.stdout.strip()
                if commit_hash == remote_hash:
                    st.success("✅ Up to date with GitHub")
                else:
                    st.warning(f"⚠️ Local: `{commit_hash}`\nRemote: `{remote_hash}`")
        except Exception:
            # On Streamlit Cloud, show info about checking dashboard
            st.info("💡 Check Streamlit Cloud dashboard for latest commit")
    
    # Check if agent is ready
    if not st.session_state.agent_ready:
        st.error(f"⚠️ Agent initialization failed: {st.session_state.get('agent_error', 'Unknown error')}")
        st.info("💡 **Tip**: Make sure you've created a `.env` file with your OpenAI API key:\n```\nOPENAI_API_KEY=your_key_here\n```")
        return
    
    # Display chat history (clean, no copy buttons)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input (clean, ChatGPT-like)
    query = st.chat_input("Message UCL Lead Intelligence...")
    
    if query:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
        
        # Get response from agent with progress indicator
        with st.chat_message("assistant"):
            with st.spinner("🤔 Analyzing your query..."):
                # Get auth info for audit logging
                auth = get_auth()
                try:
                    username = auth.get_username()
                    session_id = auth.get_session_id()
                    
                    # Ensure proper types for query method
                    user_id_str = str(username) if username else "anonymous"
                    session_id_str = str(session_id) if session_id else None
                except Exception as auth_error:
                    # Fallback if auth methods fail
                    user_id_str = "anonymous"
                    session_id_str = None
                
                # Convert chat history to LangChain format
                chat_history_langchain = []
                if 'messages' in st.session_state and len(st.session_state.messages) > 0:
                    # Get last 10 messages for context (to avoid token limits)
                    recent_messages = st.session_state.messages[-10:]
                    for msg in recent_messages:
                        if msg["role"] == "user":
                            from langchain.schema import HumanMessage
                            chat_history_langchain.append(HumanMessage(content=msg["content"]))
                        elif msg["role"] == "assistant":
                            from langchain.schema import AIMessage
                            chat_history_langchain.append(AIMessage(content=msg["content"]))
                
                # Call agent query with explicit parameters and chat history
                try:
                    result = st.session_state.agent.query(
                        question=str(query),
                        chat_history=chat_history_langchain,
                        user_id=user_id_str,
                        session_id=session_id_str
                    )
                except TypeError as e:
                    # Fallback: try with minimal parameters
                    result = st.session_state.agent.query(
                        question=str(query),
                        chat_history=chat_history_langchain
                    )
                
                if result['success']:
                    response = result['answer']
                    st.markdown(response)
                    
                    # Show reasoning steps if available (collapsible)
                    if result.get('reasoning_steps') and len(result['reasoning_steps']) > 0:
                        with st.expander("🔍 View Reasoning Steps", expanded=False):
                            st.markdown("### Reasoning Process")
                            for step in result['reasoning_steps']:
                                step_num = step.get('step', '?')
                                tool = step.get('tool', 'unknown')
                                validation = step.get('validation', {})
                                
                                # Status icon
                                if validation.get('valid', True):
                                    status_icon = "✅"
                                else:
                                    status_icon = "⚠️"
                                
                                st.markdown(f"**Step {step_num}**: {status_icon} {tool}")
                                
                                if step.get('input'):
                                    st.code(f"Input: {json.dumps(step.get('input'), indent=2)}", language="json")
                                
                                validation_msg = validation.get('message', '')
                                if validation_msg:
                                    if validation.get('valid', True):
                                        st.info(f"Validation: {validation_msg}")
                                    else:
                                        st.warning(f"Validation: {validation_msg}")
                            
                            # Show tools used summary
                            if result.get('tools_used'):
                                st.markdown(f"**Tools Used**: {', '.join(result['tools_used'])}")
                            
                            if result.get('execution_time_ms'):
                                st.caption(f"⏱️ Execution time: {result['execution_time_ms']:.0f}ms")
                    
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    error_msg = f"⚠️ **Error**: {result.get('error', 'Unknown error')}"
                    st.error(error_msg)
                    
                    # Offer help if error occurs
                    with st.expander("💡 Need Help?", expanded=False):
                        st.markdown("""
                        **I encountered an error. Here's how I can help:**
                        
                        1. **Try rephrasing your question** - Sometimes a different wording helps
                        2. **Break it into smaller parts** - Ask simpler questions first
                        3. **Check if the data exists** - I can only work with data that's been ingested
                        4. **Provide more context** - If referring to a previous question, include that context
                        
                        **Example**: Instead of "What about those leads?", try "What about the high-budget leads we discussed earlier?"
                        """)
                    
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})


if __name__ == "__main__":
    main()

