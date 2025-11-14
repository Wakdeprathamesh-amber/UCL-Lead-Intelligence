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

from query_tools import LeadQueryTools
from aggregate_query_tools import AggregateQueryTools
from ai_agent import LeadIntelligenceAgent


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
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e293b;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-size: 1.1rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 2rem;
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
    
    /* Section Headers */
    .section-header {
        font-size: 0.875rem;
        font-weight: 600;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }
    
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
    
    /* Chat Input - Larger and More Visible */
    .stChatInputContainer {
        padding: 1.5rem 0;
    }
    
    .stChatInputContainer textarea {
        font-size: 1.1rem !important;
        min-height: 80px !important;
        padding: 1rem !important;
        border: 2px solid #cbd5e1 !important;
        border-radius: 0.5rem !important;
    }
    
    .stChatInputContainer textarea:focus {
        border-color: #1e293b !important;
        box-shadow: 0 0 0 3px rgba(30, 41, 59, 0.1) !important;
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
    
    # Header with improved styling
    st.markdown('<div class="main-header">🎓 UCL Lead Intelligence AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Your intelligent assistant for student lead insights and analytics</div>', unsafe_allow_html=True)
    
    # Sidebar - Professional Dashboard
    with st.sidebar:
        # Mode Toggle
        st.markdown("### 🔄 Data Mode")
        mode_options = {
            "detailed": "💬 Detailed (19 leads)",
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
        
        st.markdown(f"**Current Mode**: {mode_options[st.session_state.mode]}")
        st.caption("💡 Switch modes to analyze different datasets")
        st.markdown("---")
        
        # Dashboard Header
        st.markdown("## 📊 Dashboard")
        st.markdown("---")
        
        # Get aggregations
        aggs = st.session_state.query_tools.get_aggregations()
        
        # Section 1: Key Metrics (2x2 grid)
        st.markdown("### Overview")
        
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
        
        # Section 2: Status Distribution with Progress Bars
        st.markdown("### Status Distribution")
        status_breakdown = aggs['status_breakdown']
        
        # Sort by count descending
        for status, count in sorted(status_breakdown.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / aggs['total_leads'] * 100) if aggs['total_leads'] > 0 else 0
            
            # Status row with progress bar
            st.markdown(f"**{status}**")
            st.progress(percentage / 100, text=f"{count} leads ({percentage:.0f}%)")
        
        st.markdown("---")
        
        # Section 3: Mode-specific content
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
            # Detailed mode specific sections
            if 'average_budget' in aggs and aggs['average_budget']:
                st.markdown("### Budget")
                for currency, avg in aggs['average_budget'].items():
                    st.metric(
                        label=f"Average ({currency})",
                        value=f"£{avg:.2f}",
                        help="Average weekly budget"
                    )
            
            st.markdown("---")
            
            if 'location_breakdown' in aggs and aggs['location_breakdown']:
                st.markdown("### Locations")
                for location, count in sorted(aggs['location_breakdown'].items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / aggs['total_leads'] * 100) if aggs['total_leads'] > 0 else 0
                    st.markdown(f"📍 **{location}**: {count} ({percentage:.0f}%)")
            
            st.markdown("---")
            
            if 'move_in_month_breakdown' in aggs and aggs['move_in_month_breakdown']:
                st.markdown("### Move-in Timeline")
                for month, count in sorted(aggs['move_in_month_breakdown'].items()):
                    st.markdown(f"📅 **{month}**: {count} lead(s)")
            
            st.markdown("---")
            
            if 'room_type_breakdown' in aggs and aggs['room_type_breakdown']:
                st.markdown("### Room Types")
                total_room_pref = sum(aggs['room_type_breakdown'].values())
                for room_type, count in sorted(aggs['room_type_breakdown'].items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / total_room_pref * 100) if total_room_pref > 0 else 0
                    st.markdown(f"🏠 **{room_type}**: {count} ({percentage:.0f}%)")
    
    # Check if agent is ready
    if not st.session_state.agent_ready:
        st.error(f"⚠️ Agent initialization failed: {st.session_state.get('agent_error', 'Unknown error')}")
        st.info("💡 **Tip**: Make sure you've created a `.env` file with your OpenAI API key:\n```\nOPENAI_API_KEY=your_key_here\n```")
        return
    
    # Organized demo questions by category
    st.markdown("#### 💡 Demo Questions")
    st.caption("Click any question below to try it")
    
    # Category 1: Lead Lookup & Filtering
    st.markdown('<div class="section-header">🔍 Lead Lookup & Filtering</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 All Won Leads", key="won_leads", use_container_width=True):
            st.session_state.suggested_query = "Show me all Won leads with their details"
    
    with col2:
        if st.button("💰 Budget < £400", key="budget_filter", use_container_width=True):
            st.session_state.suggested_query = "Show me leads with budget less than 400 pounds"
    
    with col3:
        if st.button("📅 January 2026 Move-ins", key="jan_moveins", use_container_width=True):
            st.session_state.suggested_query = "Show me leads moving in January 2026"
    
    # Category 2: Analytics & Trends
    st.markdown('<div class="section-header">📈 Analytics & Insights</div>', unsafe_allow_html=True)
    col4, col5, col6 = st.columns(3)
    
    with col4:
        if st.button("📊 Lead Statistics", key="stats", use_container_width=True):
            st.session_state.suggested_query = "What are our total lead statistics and breakdown by status?"
    
    with col5:
        if st.button("💷 Average Budget", key="avg_budget", use_container_width=True):
            st.session_state.suggested_query = "What's the average budget across all leads?"
    
    with col6:
        if st.button("🏆 Top Trends", key="trends", use_container_width=True):
            st.session_state.suggested_query = "What are the top trends and patterns in our lead data?"
    
    # Category 3: Specific Lead Queries
    st.markdown('<div class="section-header">👤 Specific Lead Information</div>', unsafe_allow_html=True)
    col7, col8, col9 = st.columns(3)
    
    with col7:
        if st.button("👩 Laia's Details", key="laia", use_container_width=True):
            st.session_state.suggested_query = "What are Laia's accommodation requirements and current status?"
    
    with col8:
        if st.button("🔎 Search by Name", key="search_name", use_container_width=True):
            st.session_state.suggested_query = "Show me all information about Haoran Wang"
    
    with col9:
        if st.button("📋 Lead Tasks", key="tasks", use_container_width=True):
            st.session_state.suggested_query = "What tasks are associated with Won leads?"
    
    # Category 4: Comparative Analysis
    st.markdown('<div class="section-header">⚖️ Comparative Analysis</div>', unsafe_allow_html=True)
    col10, col11, col12 = st.columns(3)
    
    with col10:
        if st.button("✅ Won vs ❌ Lost", key="won_vs_lost", use_container_width=True):
            st.session_state.suggested_query = "Compare Won leads versus Lost leads - what are the key differences?"
    
    with col11:
        if st.button("🎯 Conversion Insights", key="conversion", use_container_width=True):
            st.session_state.suggested_query = "What factors contribute to successful lead conversion?"
    
    with col12:
        if st.button("📊 Monthly Comparison", key="monthly", use_container_width=True):
            st.session_state.suggested_query = "Compare leads by move-in month - which months are most popular?"
    
    st.divider()
    
    # Display chat history with copy buttons
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Add copy button for assistant messages
            if message["role"] == "assistant":
                col_copy, col_spacer = st.columns([1, 10])
                with col_copy:
                    if st.button("📋 Copy", key=f"copy_{idx}", help="Copy to clipboard"):
                        # Store in session state for copying
                        st.session_state.copied_text = message["content"]
                        st.success("✅ Copied!", icon="✅")
    
    st.divider()
    
    # Chat input section - larger and more prominent
    st.markdown("### 💬 Ask Me Anything")
    query = None
    if 'suggested_query' in st.session_state:
        query = st.session_state.suggested_query
        del st.session_state.suggested_query
    else:
        query = st.chat_input("Type your question here... (e.g., 'Show me all Won leads')", key="main_chat_input")
    
    if query:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
        
        # Get response from agent with progress indicator
        with st.chat_message("assistant"):
            with st.spinner("🤔 Analyzing your query..."):
                result = st.session_state.agent.query(query)
                
                if result['success']:
                    response = result['answer']
                    
                    # Add sources if available
                    if result.get('intermediate_steps'):
                        response += "\n\n---\n### 🔍 **Data Sources**\n"
                        tools_used = set()
                        for action, observation in result['intermediate_steps']:
                            tools_used.add(action.tool)
                        for tool in sorted(tools_used):
                            response += f"- ✓ `{tool}`\n"
                    
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # Copy button for new response
                    col_copy, col_spacer = st.columns([1, 10])
                    with col_copy:
                        if st.button("📋 Copy", key="copy_latest", help="Copy to clipboard"):
                            st.session_state.copied_text = response
                            st.success("✅ Copied!", icon="✅")
                else:
                    error_msg = f"⚠️ **Error**: {result.get('error', 'Unknown error')}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Action buttons at the bottom
    st.divider()
    
    action_col1, action_col2, action_col3 = st.columns([6, 1, 1])
    
    with action_col1:
        st.empty()  # Spacer
    
    with action_col2:
        if st.button("🗑️ Clear Chat", help="Clear all chat history", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    with action_col3:
        if st.button("🔄 Refresh Data", help="Reload dashboard metrics", use_container_width=True):
            st.rerun()


if __name__ == "__main__":
    main()

