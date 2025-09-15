# dashboard_app.py - Separate Dashboard Application

import dash
from dash import html, dcc, Input, Output, State, callback_context
import flask

# Import the dashboard module
from dashboard_module import process_dashboard_data, create_dashboard_content

# Initialize Flask server and Dash app
server = flask.Flask(__name__)
app = dash.Dash(__name__, server=server, suppress_callback_exceptions=True)
app.title = "Probenplanung Dashboard"

# Global variables
DASHBOARD_DATA = None
CONTENT_CACHE = {
    'dashboard': None,
    'data_version': 0
}

# Map application URL (change port if needed)
MAP_APP_URL = "http://127.0.0.1:5002"

# Dashboard-only app layout
app.layout = html.Div([
    # Header section
    html.Div([
        # Logo and title row
        html.Div([
            html.Img(src="/assets/logo.png", className="logo-compact"),
            html.H2("Probenplanung Dashboard", className="main-title-compact")
        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginBottom': '15px'}),

        # Upload and map link row
        html.Div([
            # Upload component
            dcc.Upload(
                id='upload-data',
                children=html.Div(['📄 Drag & Drop Excel File']),
                className="upload-area-compact",
                multiple=False
            ),

            # Map application button
            html.Div([
                html.A(
                    "🗺️ Open Map App",
                    href=MAP_APP_URL,
                    target="_blank",
                    className="nav-button nav-button-primary",
                    style={
                        'textDecoration': 'none',
                        'display': 'inline-block',
                        'padding': '8px 16px',
                        'backgroundColor': '#007bff',
                        'color': 'white',
                        'borderRadius': '6px',
                        'fontSize': '12px',
                        'fontWeight': '600',
                        'border': 'none',
                        'cursor': 'pointer',
                        'transition': 'all 0.3s ease',
                        'textTransform': 'uppercase',
                        'letterSpacing': '0.5px',
                        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'
                    },
                    title="Opens separate map application in new tab"
                )
            ], style={'marginLeft': '20px'})

        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginBottom': '10px'}),

        # Upload status
        html.Div(id='upload-status', style={'textAlign': 'center', 'marginBottom': '10px'}),

    ], className="header-section"),

    # Content area - dashboard only
    html.Div(id='main-content', style={'height': 'calc(100vh - 140px)'}),

    # Hidden stores
    html.Div(id='cache-invalidator', style={'display': 'none'}),

], className="main-container-redesigned")


@app.callback(
    [Output('upload-status', 'children'),
     Output('cache-invalidator', 'children')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def handle_file_upload(contents, filename):
    """Handle file upload for dashboard only"""
    global DASHBOARD_DATA, CONTENT_CACHE

    if contents is None:
        return "", ""

    try:
        # Process data for dashboard
        DASHBOARD_DATA, dashboard_error = process_dashboard_data(contents)

        # Invalidate cache when new data is uploaded
        CONTENT_CACHE['data_version'] += 1
        CONTENT_CACHE['dashboard'] = None

        if DASHBOARD_DATA is not None:
            success_msg = html.Div([
                html.Span("✅", style={'fontSize': '14px', 'marginRight': '6px'}),
                html.Span(f"'{filename}' uploaded successfully! Dashboard ready.",
                          style={'color': '#28a745', 'fontSize': '12px', 'fontWeight': '500'}),
                html.Br(),
                html.Small(
                    f"Loaded data for {len(set([item.get('kunde', 'Unknown') for item in DASHBOARD_DATA]))} customers.",
                    style={'color': '#6c757d', 'fontSize': '11px'})
            ])

            return success_msg, str(CONTENT_CACHE['data_version'])
        else:
            raise Exception(dashboard_error or "Unknown error processing dashboard data")

    except Exception as e:
        error_msg = html.Div([
            html.Span("❌", style={'fontSize': '14px', 'marginRight': '6px'}),
            html.Span(f"Error: {str(e)[:50]}...", style={'color': '#dc3545', 'fontSize': '12px'})
        ])
        return error_msg, ""


@app.callback(
    Output('main-content', 'children'),
    [Input('cache-invalidator', 'children')],
    prevent_initial_call=False
)
def render_dashboard_content(cache_version):
    """Render dashboard content with caching"""
    global DASHBOARD_DATA, CONTENT_CACHE

    # Check cache first
    if CONTENT_CACHE['dashboard'] is not None:
        print("🚀 Loading dashboard from cache")
        return CONTENT_CACHE['dashboard']

    print("⏳ Generating dashboard content...")
    if DASHBOARD_DATA is not None:
        dashboard_content = create_dashboard_content(DASHBOARD_DATA)
    else:
        dashboard_content = html.Div([
            html.Div([
                html.H3("📊 Welcome to Probenplanung Dashboard",
                        style={'color': '#2c3e50', 'textAlign': 'center', 'marginBottom': '20px'}),
                html.P("Please upload an Excel file to view your dashboard data.",
                       style={'textAlign': 'center', 'color': '#6c757d', 'marginBottom': '15px'}),
                html.P("For map visualization, use the 'Open Map App' button above.",
                       style={'textAlign': 'center', 'color': '#6c757d', 'fontSize': '12px'})
            ], style={'padding': '50px', 'textAlign': 'center'})
        ])

    # Cache the content
    CONTENT_CACHE['dashboard'] = dashboard_content
    print("💾 Dashboard content cached")
    return dashboard_content


def clear_content_cache():
    """Manually clear the content cache"""
    global CONTENT_CACHE
    CONTENT_CACHE['dashboard'] = None
    print("🗑️ Content cache cleared")


if __name__ == '__main__':
    print("=" * 60)
    print("📊 STARTING DASHBOARD APPLICATION")
    print("=" * 60)
    print(f"Dashboard URL: http://127.0.0.1:8050")
    print(f"Map App URL: {MAP_APP_URL}")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=8050)