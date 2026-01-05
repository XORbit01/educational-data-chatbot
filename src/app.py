"""
Educational Data Chatbot - Streamlit Application

A modern chat interface for querying educational data
using natural language. Powered by DeepSeek Coder 6.7B via Ollama.
100% offline operation.

Developer: aliawada127001@outlook.com
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from typing import Optional

from config import config
from query_processor import get_processor, get_data_manager, QueryResult
from response_formatter import generate_visualization
from logger import app_logger


# =============================================================================
# Page Configuration
# =============================================================================

st.set_page_config(
    page_title=config.ui.page_title,
    page_icon=config.ui.page_icon,
    layout=config.ui.layout,
    initial_sidebar_state=config.ui.initial_sidebar_state
)


# =============================================================================
# Custom CSS - Modern Dark Theme with Glassmorphism
# =============================================================================

st.markdown("""
<style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    /* Root variables */
    :root {
        --bg-primary: #0a0a0f;
        --bg-secondary: #12121a;
        --bg-tertiary: #1a1a24;
        --accent-primary: #6366f1;
        --accent-secondary: #8b5cf6;
        --accent-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --border-color: rgba(99, 102, 241, 0.2);
        --glass-bg: rgba(18, 18, 26, 0.8);
        --success: #10b981;
        --error: #ef4444;
        --warning: #f59e0b;
    }
    
    /* Global styles */
    .stApp {
        background: var(--bg-primary);
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Header styling */
    .app-header {
        text-align: center;
        padding: 2rem 1rem;
        margin-bottom: 2rem;
        background: linear-gradient(180deg, rgba(99, 102, 241, 0.1) 0%, transparent 100%);
        border-radius: 16px;
        border: 1px solid var(--border-color);
    }
    
    .app-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: var(--accent-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    
    .app-subtitle {
        color: var(--text-secondary);
        font-size: 1.1rem;
        font-weight: 400;
    }
    
    /* Chat container */
    .chat-container {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid var(--border-color);
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* Message bubbles */
    .message-user {
        background: var(--accent-gradient);
        color: white;
        padding: 1rem 1.25rem;
        border-radius: 16px 16px 4px 16px;
        margin: 0.75rem 0;
        margin-left: 20%;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
    }
    
    .message-assistant {
        background: var(--bg-tertiary);
        color: var(--text-primary);
        padding: 1rem 1.25rem;
        border-radius: 16px 16px 16px 4px;
        margin: 0.75rem 0;
        margin-right: 10%;
        border: 1px solid var(--border-color);
    }
    
    /* Code blocks */
    .code-block {
        background: #1e1e2e;
        border-radius: 8px;
        padding: 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        overflow-x: auto;
        border: 1px solid rgba(99, 102, 241, 0.3);
        margin: 0.5rem 0;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .status-ready {
        background: rgba(16, 185, 129, 0.15);
        color: var(--success);
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .status-error {
        background: rgba(239, 68, 68, 0.15);
        color: var(--error);
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: var(--bg-secondary);
        border-right: 1px solid var(--border-color);
    }
    
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }
    
    /* Input styling */
    .stTextInput input {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
    }
    
    .stTextInput input:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2) !important;
    }
    
    /* Button styling */
    .stButton button {
        background: var(--accent-gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4) !important;
    }
    
    /* Metric cards */
    .metric-card {
        background: var(--bg-tertiary);
        border-radius: 12px;
        padding: 1.25rem;
        border: 1px solid var(--border-color);
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        background: var(--accent-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-label {
        color: var(--text-secondary);
        font-size: 0.875rem;
        margin-top: 0.25rem;
    }
    
    /* Example queries */
    .example-query {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.2s ease;
        color: var(--text-secondary);
    }
    
    .example-query:hover {
        border-color: var(--accent-primary);
        background: rgba(99, 102, 241, 0.1);
        color: var(--text-primary);
    }
    
    /* Loading animation */
    .loading-dots {
        display: inline-flex;
        gap: 4px;
    }
    
    .loading-dots span {
        width: 8px;
        height: 8px;
        background: var(--accent-primary);
        border-radius: 50%;
        animation: bounce 1.4s ease-in-out infinite;
    }
    
    .loading-dots span:nth-child(1) { animation-delay: 0s; }
    .loading-dots span:nth-child(2) { animation-delay: 0.2s; }
    .loading-dots span:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes bounce {
        0%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-8px); }
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: var(--bg-tertiary) !important;
        border-radius: 8px !important;
        border: 1px solid var(--border-color) !important;
    }
    
    /* DataFrame styling */
    .dataframe {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-primary);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Warning/Error messages */
    .stAlert {
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Session State Initialization
# =============================================================================

def init_session_state():
    """Initialize session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'processor' not in st.session_state:
        st.session_state.processor = None
    
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = None
    
    if 'system_ready' not in st.session_state:
        st.session_state.system_ready = False
    
    if 'system_status' not in st.session_state:
        st.session_state.system_status = {}


def check_system():
    """Check system status and initialize components."""
    try:
        st.session_state.data_manager = get_data_manager()
        st.session_state.processor = get_processor()
        st.session_state.system_status = st.session_state.processor.check_system()
        st.session_state.system_ready = st.session_state.system_status.get('ready', False)
    except Exception as e:
        st.session_state.system_ready = False
        st.session_state.system_status = {'error': str(e)}
        app_logger.error("System check failed", error=str(e))


# =============================================================================
# UI Components
# =============================================================================

def render_header():
    """Render the application header."""
    st.markdown("""
    <div class="app-header">
        <div class="app-title">Educational Data Chatbot</div>
        <div class="app-subtitle">Natural language queries for student performance analysis</div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with status and examples."""
    with st.sidebar:
        st.markdown("### System Status")
        
        status = st.session_state.system_status
        
        if st.session_state.system_ready:
            st.markdown("""
            <div class="status-badge status-ready">
                All Systems Ready
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-badge status-error">
                System Not Ready
            </div>
            """, unsafe_allow_html=True)
            
            if not status.get('data_loaded'):
                st.error("Data file not loaded")
            if not status.get('ollama_connected'):
                st.error("Ollama not connected")
                st.info("Start Ollama with: `ollama serve`")
            if not status.get('model_available'):
                st.warning("Model not available")
                st.info("Pull model: `ollama pull deepseek-coder:6.7b`")
        
        st.markdown("---")
        
        # Data info
        if status.get('data_loaded') and st.session_state.data_manager:
            try:
                df = st.session_state.data_manager.df
                st.markdown("### Dataset Info")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Rows", f"{len(df):,}")
                with col2:
                    st.metric("Columns", len(df.columns))
                
                with st.expander("View Columns"):
                    for col in df.columns:
                        st.markdown(f"- `{col}`")
            except Exception:
                pass
        
        st.markdown("---")
        
        # Example queries
        st.markdown("### Example Questions")
        
        examples = [
            "Compare average scores across all courses",
            "How do male vs female students perform?",
            "Show me a pie chart of gender distribution",
            "Create a beautiful bar chart of course scores",
            "Show correlation heatmap of all numeric columns",
            "Create a sunburst chart of students by class and gender",
            "Show score distribution with a histogram",
            "Is there a correlation between attendance and scores?",
        ]
        
        for example in examples:
            if st.button(example, key=f"ex_{example[:20]}", use_container_width=True):
                st.session_state.pending_query = example
                st.rerun()
        
        st.markdown("---")
        
        # Clear chat
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


def render_message(role: str, content: str, data=None, code: str = None, viz=None, data_type: str = None):
    """Render a chat message."""
    if role == "user":
        st.markdown(f"""
        <div class="message-user">
            {content}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="message-assistant">
            {content}
        </div>
        """, unsafe_allow_html=True)
        
        # Check if data itself is a Plotly figure (AI-generated visualization)
        if isinstance(data, go.Figure):
            st.plotly_chart(data, use_container_width=True)
        # Show visualization from response_formatter if available
        elif viz and viz.figure:
            st.plotly_chart(viz.figure, use_container_width=True)
        
        # Show data table if available (but not for Plotly figures)
        if data is not None and not isinstance(data, go.Figure):
            if isinstance(data, (pd.DataFrame, pd.Series)):
                with st.expander("📊 View Data Table"):
                    st.dataframe(data, use_container_width=True)
        
        # Show code if available
        if code:
            with st.expander("💻 View Generated Code"):
                st.code(code, language="python")


def render_chat():
    """Render the chat interface."""
    # Chat messages container
    chat_container = st.container()
    
    with chat_container:
        for msg in st.session_state.messages:
            render_message(
                role=msg['role'],
                content=msg['content'],
                data=msg.get('data'),
                code=msg.get('code'),
                viz=msg.get('viz'),
                data_type=msg.get('data_type')
            )
    
    # Check for pending query from sidebar
    if 'pending_query' in st.session_state:
        query = st.session_state.pending_query
        del st.session_state.pending_query
        process_query(query)
    
    # Input area
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([6, 1])
    
    with col1:
        user_input = st.text_input(
            "Ask a question",
            placeholder="e.g., Compare the average scores between Biology and Computer Science...",
            label_visibility="collapsed",
            key="user_input"
        )
    
    with col2:
        submit = st.button("Send", use_container_width=True)
    
    if submit and user_input:
        process_query(user_input)


def process_query(query: str):
    """Process a user query and update the chat."""
    if not query.strip():
        return
    
    # Add user message
    st.session_state.messages.append({
        'role': 'user',
        'content': query,
        'timestamp': datetime.now().isoformat()
    })
    
    # Process with loading indicator
    with st.spinner("Analyzing your question..."):
        try:
            result = st.session_state.processor.process_question(query)
            
            if result.success:
                viz = None
                
                # Check if the AI generated a Plotly figure directly
                if result.has_visualization:
                    # AI generated the visualization - use it directly
                    # No need for additional viz generation
                    pass
                elif result.has_data and not isinstance(result.data, go.Figure):
                    # Generate visualization for data results
                    viz = generate_visualization(result.data, query)
                
                # Add assistant message
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': result.answer,
                    'data': result.data if result.has_data else None,
                    'data_type': result.data_type,
                    'code': result.code,
                    'viz': viz,
                    'timestamp': datetime.now().isoformat(),
                    'execution_time': result.total_time_ms
                })
            else:
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': result.answer,
                    'timestamp': datetime.now().isoformat()
                })
                
        except Exception as e:
            app_logger.error("Query processing error", error=str(e))
            st.session_state.messages.append({
                'role': 'assistant',
                'content': f"Error: {str(e)}",
                'timestamp': datetime.now().isoformat()
            })
    
    st.rerun()


def render_welcome():
    """Render welcome message for new users."""
    if not st.session_state.messages:
        st.markdown("""
        <div class="chat-container" style="text-align: center;">
            <h3 style="color: var(--text-primary); margin-bottom: 1rem;">
                Welcome to the Educational Data Chatbot
            </h3>
            <p style="color: var(--text-secondary); max-width: 600px; margin: 0 auto;">
                Analyze student performance data using natural language queries.
                Ask questions like "Compare average scores across courses" or 
                "Which students have the highest attendance?"
            </p>
            <div style="margin-top: 1.5rem; display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                <div class="metric-card" style="flex: 1; min-width: 150px; max-width: 200px;">
                    <div class="metric-value">100%</div>
                    <div class="metric-label">Offline</div>
                </div>
                <div class="metric-card" style="flex: 1; min-width: 150px; max-width: 200px;">
                    <div class="metric-value">Secure</div>
                    <div class="metric-label">Sandboxed</div>
                </div>
                <div class="metric-card" style="flex: 1; min-width: 150px; max-width: 200px;">
                    <div class="metric-value">Fast</div>
                    <div class="metric-label">Local LLM</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# Main Application
# =============================================================================

def main():
    """Main application entry point."""
    # Initialize session state
    init_session_state()
    
    # Check system on first load
    if not st.session_state.system_status:
        check_system()
    
    # Render UI
    render_header()
    render_sidebar()
    
    # Main content
    if not st.session_state.system_ready:
        st.warning("""
        **System not fully ready**
        
        Please ensure:
        1. The data file `Students_Dataset.xlsx` exists in the project folder
        2. Ollama is running (`ollama serve`)
        3. DeepSeek Coder model is installed (`ollama pull deepseek-coder:6.7b`)
        """)
        
        if st.button("Retry Connection"):
            check_system()
            st.rerun()
    else:
        render_welcome()
        render_chat()


if __name__ == "__main__":
    main()
