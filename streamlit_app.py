"""
AI Convolution Dashboard
Production-ready visualization layer for AI-generated analytical plots.
"""

import json
import streamlit as st
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

# ============================================================
# App Configuration
# ============================================================

st.set_page_config(
    page_title="AI Convolution Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 AI Convolution Dashboard")
st.caption("Visualization Layer for AI-Generated Analytical Queries")


# ============================================================
# Configuration
# ============================================================

PLOT_FILE = Path("plots.json")


# ============================================================
# Data Layer
# ============================================================

@st.cache_data(show_spinner=False)
def load_results(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []

    with open(path) as f:
        raw_data = json.load(f)

    if isinstance(raw_data, dict):
        raw_data = [raw_data]

    results = [r for r in raw_data if "plot" in r]

    return sorted(results, key=parse_timestamp, reverse=True)


def parse_timestamp(entry: Dict[str, Any]) -> datetime:
    ts = entry.get("timestamp")

    if not ts:
        return datetime.min.replace(tzinfo=timezone.utc)

    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


# ============================================================
# Plot Rendering Layer
# ============================================================

def build_bar(fig, trace):
    fig.add_bar(
        x=trace.get("x"),
        y=trace.get("y"),
        name=trace.get("name"),
        marker=trace.get("marker", {}),
        text=trace.get("text"),
        textposition=trace.get("textposition", "auto")
    )


def build_line(fig, trace):
    fig.add_scatter(
        x=trace.get("x"),
        y=trace.get("y"),
        mode="lines+markers",
        name=trace.get("name")
    )


def build_pie(fig, trace):
    fig.add_pie(
        labels=trace.get("labels"),
        values=trace.get("values"),
        name=trace.get("name"),
        textinfo="percent+label"
    )


TRACE_BUILDERS = {
    "bar": build_bar,
    "line": build_line,
    "scatter": build_line,
    "pie": build_pie,
}


def plotly_from_metadata(plot_spec: Dict[str, Any]) -> go.Figure:
    fig = go.Figure()

    for trace in plot_spec.get("data", []):
        trace_type = trace.get("type")
        builder = TRACE_BUILDERS.get(trace_type)

        if builder:
            builder(fig, trace)

    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=40, r=40, t=60, b=40),
        title_x=0.5
    )

    fig.update_layout(**plot_spec.get("layout", {}))

    return fig


def detect_chart_type(plot_spec: Dict[str, Any]) -> str:
    traces = plot_spec.get("data", [])
    if not traces:
        return "Unknown"

    return traces[0].get("type", "Unknown").capitalize()


# ============================================================
# Sidebar Layer
# ============================================================

def render_sidebar(results: List[Dict[str, Any]]) -> Dict[str, Any]:

    st.sidebar.header("📂 Query Explorer")

    if not results:
        st.sidebar.warning("No plots available.")
        return {}

    queries = [r.get("query", "Unnamed Query") for r in results]

    # Search
    search_term = st.sidebar.text_input("🔎 Search Query")

    filtered_indices = [
        i for i, q in enumerate(queries)
        if search_term.lower() in q.lower()
    ] if search_term else list(range(len(queries)))

    if not filtered_indices:
        st.sidebar.warning("No matches found.")
        return {}

    selected_index = st.sidebar.selectbox(
        "Select Query",
        filtered_indices,
        format_func=lambda i: queries[i]
    )

    st.sidebar.markdown("---")

    st.sidebar.metric("Total Plots", len(results))
    st.sidebar.metric("Unique Queries", len(set(queries)))

    return results[selected_index]


# ============================================================
# Main Rendering Layer
# ============================================================

def render_header(result: Dict[str, Any]):
    st.subheader(result.get("query", "Unnamed Query"))

    col1, col2, col3 = st.columns(3)

    chart_type = detect_chart_type(result.get("plot", {}))
    timestamp = result.get("timestamp", "N/A")

    col1.metric("Chart Type", chart_type)
    col2.metric("Generated At", timestamp)
    col3.metric("Traces", len(result.get("plot", {}).get("data", [])))

    st.markdown("---")


def render_visualization(result: Dict[str, Any]):
    try:
        fig = plotly_from_metadata(result["plot"])
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("Plot rendering failed.")
        st.code(str(e))


def render_tabs(result: Dict[str, Any]):

    tab1, tab2, tab3 = st.tabs(["📊 Visualization", "📄 Metadata", "🔍 JSON"])

    with tab1:
        render_visualization(result)

    with tab2:
        metadata = {
            "query": result.get("query"),
            "timestamp": result.get("timestamp"),
            "chart_type": detect_chart_type(result.get("plot", {}))
        }
        st.json(metadata)

    with tab3:
        st.json(result)


# ============================================================
# Download Section
# ============================================================

def render_download(results: List[Dict[str, Any]]):
    st.download_button(
        label="⬇ Download Full JSON",
        data=json.dumps(results, indent=2),
        file_name="ai_generated_plots.json",
        mime="application/json"
    )


# ============================================================
# Main Execution
# ============================================================

def main():
    results = load_results(PLOT_FILE)

    if not results:
        st.warning("No plot metadata found. Waiting for AI-generated plots.")
        return

    selected_result = render_sidebar(results)

    if not selected_result:
        return

    render_header(selected_result)
    render_tabs(selected_result)

    st.markdown("---")
    render_download(results)

    st.caption("AI Convolution Dashboard — Visualization Layer")


if __name__ == "__main__":
    main()