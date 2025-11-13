# app.py
"""
Flask app that serves:
- '/' -> your original Jinja template (templates/index.html)
- '/y_predict' -> form POST handler (keeps original behavior)
Also embeds a Dash app at '/dash/' that reuses the same prediction logic.

Ensure:
- static/ contains: css/style.css, giphy2.gif, giphy3.gif
- templates/index.html exists (below provided)
"""

import os
from flask import Flask, render_template, request
from predict_wrapper import predict_text  # wrapper that imports your real model if present

# --- Flask app (main) ---
server = Flask(__name__, static_folder="static", template_folder="templates")

@server.route("/", methods=["GET"])
def index():
    # render the Jinja template you provided
    return render_template("index.html")

@server.route("/y_predict", methods=["POST"])
def y_predict():
    """
    Called by your original form:
    - Reads 'Sentence' from form
    - Calls predict_text(text) and returns index.html with appropriate template flags
    predict_text must return (label_str, is_positive_bool, display_text_str)
    """
    text = request.form.get("Sentence", "").strip()
    if not text:
        # No text — re-render without images (keeps original UI behavior)
        return render_template("index.html")

    label, is_positive, display_text = predict_text(text)

    # Set flags used by your template
    if is_positive:
        # show positive gif (image variable)
        return render_template("index.html", image=True, image2=False, prediction_text=display_text)
    else:
        # show negative gif (image2 variable)
        return render_template("index.html", image=False, image2=True, prediction_text=display_text)

# --- Dash app (embedded) ---
from dash import Dash, html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from datetime import datetime

# Create Dash app but use the existing Flask server so both apps run on same port
dash_app = Dash(
    __name__,
    server=server,
    url_base_pathname="/dash/",
    external_stylesheets=[dbc.themes.BOOTSTRAP, "/static/css/style.css"],
)

# In-memory history for the Dash UI
SENTIMENT_HISTORY = []  # each item: {"time": datetime, "label": str, "text": str}

def add_history(label, text):
    SENTIMENT_HISTORY.append({"time": datetime.utcnow(), "label": label, "text": text})
    # keep last 500
    if len(SENTIMENT_HISTORY) > 500:
        del SENTIMENT_HISTORY[:-500]

dash_app.layout = dbc.Container(
    [
        dbc.Row(dbc.Col(html.H2("💬 Tweet Sentiment Analyzer (Dash)"))),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Input(
                            id="tweet-input",
                            type="text",
                            placeholder="Type a tweet or sentence...",
                            style={"width": "100%", "padding": "12px", "fontSize": "16px"},
                        ),
                        html.Div(style={"height": "8px"}),
                        dbc.Button("Analyze", id="analyze-btn", color="primary"),
                        dbc.Button("Clear history", id="clear-history", color="secondary", className="ms-2"),
                        html.Div(id="result-area", className="mt-3"),
                        dcc.Store(id="history-store"),
                    ],
                    md=6,
                ),
                dbc.Col(
                    [
                        dcc.Graph(id="sentiment-history", config={"displayModeBar": False}),
                        html.Div("Sentiment distribution (last 100 predictions)", className="mt-2"),
                    ],
                    md=6,
                ),
            ],
            className="align-items-start",
        ),
        html.Hr(),
        dbc.Row(dbc.Col(html.Div("Dash UI integrated with Flask • Static assets served from /static"))),
    ],
    fluid=True,
)

# Analyze callback
@dash_app.callback(
    Output("result-area", "children"),
    Output("history-store", "data"),
    Input("analyze-btn", "n_clicks"),
    State("tweet-input", "value"),
    State("history-store", "data"),
    prevent_initial_call=True,
)
def analyze(n_clicks, text, history_data):
    if not text or not text.strip():
        return html.Div("Please enter text to analyze.", style={"color": "#999"}), history_data

    label, is_positive, display_text = predict_text(text)
    gif = "/static/giphy3.gif" if is_positive else "/static/giphy2.gif"

    result_ui = dbc.Card(
        dbc.CardBody(
            [
                html.Img(src=gif, style={"width": "220px", "borderRadius": "10px", "display": "block", "margin": "0 auto"}),
                html.H4(display_text, className="text-center mt-2", style={"color": "#2ecc71" if is_positive else "#e74c3c"}),
                html.P(f"Label: {label}", className="text-center", style={"opacity": 0.85, "marginTop": "4px"}),
            ]
        ),
        className="mt-3",
    )

    add_history(label, text)
    recent = SENTIMENT_HISTORY[-100:]
    pos_count = sum(1 for r in recent if r["label"].lower().startswith("pos"))
    neg_count = len(recent) - pos_count
    history_payload = {"recent": recent, "pos_count": pos_count, "neg_count": neg_count}

    return result_ui, history_payload

# Chart update & clear history
@dash_app.callback(
    Output("sentiment-history", "figure"),
    Input("history-store", "data"),
    Input("clear-history", "n_clicks"),
    prevent_initial_call=False,
)
def update_history_chart(history_data, clear_clicks):
    triggered = ctx.triggered_id
    if triggered == "clear-history":
        SENTIMENT_HISTORY.clear()
        fig = go.Figure()
        fig.update_layout(title="No data (history cleared)")
        return fig

    if not history_data or "recent" not in history_data:
        fig = go.Figure(data=[go.Pie(labels=["Positive", "Negative"], values=[0, 0])])
        fig.update_layout(title="Sentiment distribution (last 100)")
        return fig

    pos = history_data.get("pos_count", 0)
    neg = history_data.get("neg_count", 0)
    fig = go.Figure(data=[go.Pie(labels=["Positive", "Negative"], values=[pos, neg], hole=0.36)])
    fig.update_layout(title="Sentiment distribution (last 100 predictions)", legend=dict(orientation="h"))
    return fig

# Run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    server.run(debug=True, port=port)
