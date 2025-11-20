"""
Whitelabel Lead Intelligence - Main Streamlit App
UCL Student Lead Intelligence AI Assistant
"""

import streamlit as st
import os
import sys
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Ensure databases exist on first run
try:
    from init_databases import ensure_databases_exist
    ensure_databases_exist()
except Exception as e:
    print(f"⚠️  Database initialization warning: {str(e)}")

from query_tools import LeadQueryTools
from aggregate_query_tools import AggregateQueryTools
from ai_agent import LeadIntelligenceAgent
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

if 'agent' not in st.session_state or 'agent_mode' not in st.session_state or st.session_state.agent_mode != st.session_state.mode:
    with st.spinner(f"🚀 Initializing AI Agent ({'Aggregate Analytics' if st.session_state.mode == 'aggregate' else 'Detailed Conversation'} mode)..."):
        try:
            st.session_state.agent = LeadIntelligenceAgent(mode=st.session_state.mode)
            st.session_state.agent_ready = True
            st.session_state.agent_mode = st.session_state.mode
            # Clear chat history when switching modes
            st.session_state.messages = []
        except Exception as e:
            st.session_state.agent_ready = False
            st.session_state.agent_error = str(e)

if 'query_tools' not in st.session_state or 'query_tools_mode' not in st.session_state or st.session_state.query_tools_mode != st.session_state.mode:
    if st.session_state.mode == "aggregate":
        st.session_state.query_tools = AggregateQueryTools()
    else:
        st.session_state.query_tools = LeadQueryTools()
    st.session_state.query_tools_mode = st.session_state.mode


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
    
    # Sidebar - Professional Dashboard
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
        
        st.markdown("---")
        
        # Dashboard Header
        st.markdown("## 📊 Dashboard")
        
        # Get aggregations (with error handling for first run)
        try:
            aggs = st.session_state.query_tools.get_aggregations()
        except Exception as e:
            st.error(f"⚠️ Database not ready yet. Initializing...")
            st.info("💡 The app is setting up databases on first run. Please refresh the page in a moment.")
            # Return empty aggregations to prevent crash
            aggs = {
                "total_leads": 0,
                "won_count": 0,
                "won_leads": 0,
                "lost_count": 0,
                "lost_leads": 0,
                "status_breakdown": {},
                "conversion_rate": 0
            }
        
        # Section 1: Key Metrics (2x2 grid)
        
        # Row 1
        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric(
                label="Total Leads",
                value=aggs['total_leads'],
                help="All leads in database"
            )
        with metric_col2:
            # Handle both modes - aggregate uses won_count, detailed uses won_leads
            won_count = aggs.get('won_count', aggs.get('won_leads', 0))
            win_rate = (won_count / aggs['total_leads'] * 100) if aggs['total_leads'] > 0 else 0
            # Aggregate mode has conversion_rate pre-calculated
            if 'conversion_rate' in aggs:
                win_rate = aggs['conversion_rate']
            st.metric(
                label="Win Rate",
                value=f"{win_rate:.1f}%",
                delta=f"{won_count} won",
                help="Percentage of won leads"
            )
        
        # Row 2
        metric_col3, metric_col4 = st.columns(2)
        with metric_col3:
            won_count = aggs.get('won_count', aggs.get('won_leads', 0))
            st.metric(
                label="Won",
                value=won_count,
                delta="positive" if won_count > 0 else None,
                help="Successfully converted"
            )
        with metric_col4:
            lost_count = aggs.get('lost_count', aggs.get('lost_leads', 0))
            st.metric(
                label="Lost",
                value=lost_count,
                delta="negative" if lost_count > 0 else None,
                delta_color="inverse",
                help="Not converted"
            )
        
        st.markdown("---")
        
        # Section 2: Status Distribution (simplified)
        status_breakdown = aggs['status_breakdown']
        for status, count in sorted(status_breakdown.items(), key=lambda x: x[1], reverse=True)[:3]:
            percentage = (count / aggs['total_leads'] * 100) if aggs['total_leads'] > 0 else 0
            st.markdown(f"**{status}**: {count} ({percentage:.0f}%)")
        
        st.markdown("---")
        
        # Section 3: Mode-specific content (simplified)
        if st.session_state.mode == "aggregate":
            # Aggregate mode specific sections
            if 'lost_reasons' in aggs and aggs['lost_reasons']:
                st.markdown("### Top Lost Reasons")
                for reason, count in list(aggs['lost_reasons'].items())[:5]:
                    st.markdown(f"❌ **{reason}**: {count}")
            
            st.markdown("---")
            
            if 'country_breakdown' in aggs and aggs['country_breakdown']:
                st.markdown("### Top Source Countries")
                for country, count in list(sorted(aggs['country_breakdown'].items(), key=lambda x: x[1], reverse=True))[:5]:
                    percentage = (count / aggs['total_leads'] * 100) if aggs['total_leads'] > 0 else 0
                    st.markdown(f"🌍 **{country}**: {count} ({percentage:.1f}%)")
            
            st.markdown("---")
            
            if 'repeat_rate' in aggs:
                st.markdown("### Repeat Leads")
                st.metric(
                    label="Repeat Rate",
                    value=f"{aggs['repeat_rate']:.1f}%",
                    delta=f"{aggs.get('repeat_count', 0)} leads",
                    help="Percentage of repeat leads"
                )
            
            st.markdown("---")
            
            if 'monthly_trends' in aggs and aggs['monthly_trends']:
                st.markdown("### Monthly Trends")
                for month, count in list(sorted(aggs['monthly_trends'].items(), reverse=True))[:6]:
                    st.markdown(f"📅 **{month}**: {count} lead(s)")
        else:
            # Detailed mode - minimal info
            if 'average_budget' in aggs and aggs['average_budget']:
                for currency, avg in aggs['average_budget'].items():
                    st.metric(label="Avg Budget", value=f"£{avg:.0f}")
    
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
                
                # Call agent query with explicit parameters
                try:
                    result = st.session_state.agent.query(
                        question=str(query),
                        user_id=user_id_str,
                        session_id=session_id_str
                    )
                except TypeError as e:
                    # Fallback: try with minimal parameters
                    result = st.session_state.agent.query(
                        question=str(query)
                    )
                
                if result['success']:
                    response = result['answer']
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    error_msg = f"⚠️ **Error**: {result.get('error', 'Unknown error')}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})


if __name__ == "__main__":
    main()

