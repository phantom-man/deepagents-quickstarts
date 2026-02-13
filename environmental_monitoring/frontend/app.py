"""
Environmental Monitoring Dashboard

A comprehensive data exploration and analytics dashboard for environmental data
from 24+ public APIs.

Features:
- Real-time data exploration with date/time range filtering
- Cross-domain data linking and dataset joining
- Advanced analytics (correlation, anomaly detection, trend analysis)
- Comprehensive reporting with multiple export formats
- Interactive maps and visualizations
"""
import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from flask import Flask

# Import layout components
from components.layout import create_header, create_sidebar, create_footer

# Import page layouts
from pages.dashboard import create_dashboard_layout
from pages.explore import create_explore_layout
from pages.analyze import create_analyze_layout
from pages.reports import create_reports_layout

# Import configuration
from config import DASHBOARD_TITLE, THEME

# Import global callbacks (registers them with Dash)
import callbacks


# Initialize Flask server
server = Flask(__name__)

# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.FONT_AWESOME,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
    ],
    suppress_callback_exceptions=True,
    title=DASHBOARD_TITLE,
    update_title="Loading...",
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# Custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            :root {
                --primary-color: #2E86AB;
                --secondary-color: #A23B72;
                --success-color: #28A745;
                --warning-color: #F18F01;
                --danger-color: #C73E1D;
            }
            
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                background-color: #F8F9FA;
            }
            
            .sidebar {
                position: sticky;
                top: 80px;
                height: calc(100vh - 100px);
                overflow-y: auto;
            }
            
            .sidebar-content {
                background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
            }
            
            .category-checklist label {
                display: block;
                padding: 8px 12px;
                margin-bottom: 4px;
                border-radius: 6px;
                cursor: pointer;
                transition: background-color 0.2s;
            }
            
            .category-checklist label:hover {
                background-color: rgba(46, 134, 171, 0.1);
            }
            
            .card {
                border: none;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                transition: box-shadow 0.2s;
            }
            
            .card:hover {
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            
            .card-header {
                background-color: white;
                border-bottom: 1px solid #e9ecef;
                font-weight: 600;
            }
            
            .nav-link.active {
                background-color: var(--primary-color) !important;
                color: white !important;
                border-radius: 6px;
            }
            
            .btn-primary {
                background-color: var(--primary-color);
                border-color: var(--primary-color);
            }
            
            .btn-primary:hover {
                background-color: #236b8e;
                border-color: #236b8e;
            }
            
            .text-primary {
                color: var(--primary-color) !important;
            }
            
            /* Custom scrollbar */
            ::-webkit-scrollbar {
                width: 8px;
                height: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #c1c1c1;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #a8a8a8;
            }
            
            /* Animation for loading states */
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            .loading-pulse {
                animation: pulse 1.5s ease-in-out infinite;
            }
            
            /* Date picker styling */
            .DateInput_input {
                font-size: 14px !important;
                padding: 8px !important;
            }
            
            /* Table styling */
            .table-sm td, .table-sm th {
                padding: 0.5rem;
            }
            
            /* Badge styling */
            .badge {
                font-weight: 500;
            }
            
            /* Alert styling */
            .alert {
                border: none;
                border-radius: 8px;
            }
            
            /* Tab styling */
            .nav-tabs .nav-link {
                border-radius: 8px 8px 0 0;
                font-weight: 500;
            }
            
            /* Range slider styling */
            .rc-slider-track {
                background-color: var(--primary-color);
            }
            
            .rc-slider-handle {
                border-color: var(--primary-color);
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Main layout
app.layout = html.Div([
    # URL routing
    dcc.Location(id='url', refresh=False),
    
    # Header/Navbar
    create_header(),
    
    # Main content area
    dbc.Container([
        dbc.Row([
            # Sidebar
            create_sidebar(),
            
            # Main content
            dbc.Col([
                html.Div(id='page-content')
            ], width=10, className="main-content")
        ])
    ], fluid=True),
    
    # Footer
    create_footer(),
    
    # Global stores
    dcc.Store(id='global-data-store', storage_type='session'),
    dcc.Store(id='user-preferences', storage_type='local'),
    dcc.Store(id='location-updated-trigger'),
    dcc.Store(id='linked-datasets-store', storage_type='session'),
    
    # Interval for auto-refresh
    dcc.Interval(
        id='refresh-interval',
        interval=5*60*1000,  # 5 minutes
        n_intervals=0,
        disabled=True
    ),
    
    # Toast notifications
    html.Div(id='toast-container', style={'position': 'fixed', 'top': '80px', 'right': '20px', 'zIndex': 9999}),
    
    # Export toast
    dbc.Toast(
        "Data exported successfully! Check your downloads folder.",
        id="export-toast",
        header="Export Complete",
        icon="success",
        duration=4000,
        is_open=False,
        dismissable=True,
        style={'position': 'fixed', 'top': 100, 'right': 20, 'zIndex': 9999}
    ),
    
    # Share toast
    dbc.Toast(
        "Share link copied to clipboard!",
        id="share-toast",
        header="Link Copied",
        icon="info",
        duration=4000,
        is_open=False,
        dismissable=True,
        style={'position': 'fixed', 'top': 170, 'right': 20, 'zIndex': 9999}
    ),
    
    # Link datasets toast
    dbc.Toast(
        "",
        id="link-datasets-toast",
        header="Cross-Domain Link",
        icon="success",
        duration=6000,
        is_open=False,
        dismissable=True,
        style={'position': 'fixed', 'top': 240, 'right': 20, 'zIndex': 9999}
    ),
    
    # Category data toast (hidden, just for callback target)
    html.Div(id="category-data-toast", style={"display": "none"}),
    
    # Search feedback toast
    dbc.Toast(
        "",
        id="search-feedback-toast",
        header="Location Search",
        icon="info",
        duration=5000,
        is_open=False,
        dismissable=True,
        style={'position': 'fixed', 'top': 250, 'right': 20, 'zIndex': 9999}
    ),
    
    # Settings Modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Dashboard Settings")),
        dbc.ModalBody([
            html.H6("Display Options"),
            dbc.Checklist(
                id="settings-display-options",
                options=[
                    {"label": "Show map tooltips", "value": "tooltips"},
                    {"label": "Auto-refresh data", "value": "auto_refresh"},
                    {"label": "Dark mode (coming soon)", "value": "dark_mode", "disabled": True}
                ],
                value=["tooltips", "auto_refresh"]
            ),
            html.Hr(),
            html.H6("Data Preferences"),
            dbc.Label("Default Radius (km)"),
            dbc.Input(id="settings-default-radius", type="number", value=50, min=1, max=500),
            dbc.Label("Refresh Interval (minutes)", className="mt-2"),
            dbc.Input(id="settings-refresh-interval", type="number", value=5, min=1, max=60),
        ]),
        dbc.ModalFooter([
            dbc.Button("Save", id="settings-save-btn", color="primary"),
            dbc.Button("Cancel", id="settings-cancel-btn", color="secondary")
        ])
    ], id="settings-modal", is_open=False)
])


# Page routing callback
@callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    """Route to the appropriate page based on URL."""
    if pathname == '/' or pathname == '/dashboard':
        return create_dashboard_layout()
    elif pathname == '/explore':
        return create_explore_layout()
    elif pathname == '/analyze':
        return create_analyze_layout()
    elif pathname == '/reports':
        return create_reports_layout()
    else:
        # 404 page
        return html.Div([
            html.H1("404", className="display-1 text-muted"),
            html.H3("Page Not Found"),
            html.P("The page you're looking for doesn't exist."),
            dbc.Button("Go to Dashboard", href="/", color="primary")
        ], className="text-center py-5")


# Auto-refresh toggle callback
@callback(
    Output('refresh-interval', 'disabled'),
    Input('refresh-button', 'n_clicks'),
    State('refresh-interval', 'disabled'),
    prevent_initial_call=True
)
def toggle_auto_refresh(n_clicks, is_disabled):
    """Toggle auto-refresh on/off."""
    return not is_disabled


# Toast notification callback
@callback(
    Output('toast-container', 'children'),
    Input('refresh-interval', 'n_intervals'),
    prevent_initial_call=True
)
def show_refresh_toast(n_intervals):
    """Show toast when data is auto-refreshed."""
    return dbc.Toast(
        "Data refreshed automatically",
        header="Auto-Refresh",
        icon="info",
        duration=3000,
        is_open=True,
        dismissable=True
    )


# Note: custom-date-div callback is in callbacks.py (handles all time buttons)


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8050))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run_server(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
