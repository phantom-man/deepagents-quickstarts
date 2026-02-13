"""
Progress Box Component — Real-time activity log for every page.

Shows exactly what's loading, what completed, what errored, with timestamps
and durations.  Styled like a dark terminal console, fixed bottom-right.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

import dash_bootstrap_components as dbc
from dash import dcc, html


# ── Palette ────────────────────────────────────────────────────────
STATUS_CFG: Dict[str, Dict[str, str]] = {
    "loading":  {"color": "#58a6ff", "icon": "fas fa-circle-notch fa-spin"},
    "complete": {"color": "#3fb950", "icon": "fas fa-check-circle"},
    "error":    {"color": "#f85149", "icon": "fas fa-times-circle"},
    "warning":  {"color": "#d29922", "icon": "fas fa-exclamation-triangle"},
    "info":     {"color": "#8b949e", "icon": "fas fa-info-circle"},
    "success":  {"color": "#3fb950", "icon": "fas fa-flag-checkered"},
}

# ── Entry factory ──────────────────────────────────────────────────

def make_entry(
    status: str,
    message: str,
    timestamp: Optional[str] = None,
    duration_ms: Optional[int] = None,
    details: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a single progress-log entry dict."""
    return {
        "s": status,
        "m": message,
        "t": timestamp or datetime.now().strftime("%H:%M:%S"),
        "d": duration_ms,
        "sub": details or [],
    }


# ── Render helpers ─────────────────────────────────────────────────

def _format_duration(ms: Optional[int]) -> str:
    if ms is None:
        return ""
    return f"{ms / 1000:.1f}s" if ms >= 1000 else f"{ms}ms"


def _render_one(entry: Dict[str, Any]) -> html.Div:
    """Render a single log entry as a styled row."""
    status = entry.get("s", "info")
    cfg = STATUS_CFG.get(status, STATUS_CFG["info"])
    ts = entry.get("t", "")
    msg = entry.get("m", "")
    dur = _format_duration(entry.get("d"))
    subs = entry.get("sub", [])

    msg_color = "#e6edf3" if status in ("complete", "success") else cfg["color"]

    parts: list = [
        # timestamp
        html.Span(
            ts,
            style={
                "color": "#484f58",
                "marginRight": "10px",
                "minWidth": "62px",
                "display": "inline-block",
                "userSelect": "none",
            },
        ),
        # icon
        html.I(
            className=cfg["icon"],
            style={
                "color": cfg["color"],
                "marginRight": "8px",
                "width": "14px",
                "textAlign": "center",
                "flexShrink": "0",
            },
        ),
        # message
        html.Span(msg, style={"color": msg_color, "flex": "1"}),
    ]
    # duration badge
    if dur:
        parts.append(
            html.Span(
                dur,
                style={
                    "color": "#484f58",
                    "marginLeft": "12px",
                    "fontSize": "0.72rem",
                    "flexShrink": "0",
                    "backgroundColor": "rgba(110,118,129,0.1)",
                    "padding": "1px 6px",
                    "borderRadius": "4px",
                },
            )
        )

    children = [
        html.Div(
            parts,
            style={
                "display": "flex",
                "alignItems": "center",
                "padding": "3px 0",
            },
        )
    ]

    # sub-details
    for detail in subs:
        children.append(
            html.Div(
                f"    \u2514\u2500 {detail}",
                style={
                    "color": "#6e7681",
                    "fontSize": "0.72rem",
                    "paddingLeft": "72px",
                    "lineHeight": "1.5",
                },
            )
        )

    return html.Div(children)


def render_entries(entries: List[Dict[str, Any]]) -> html.Div:
    """Render a list of progress entries into styled HTML."""
    if not entries:
        return html.Div(
            "\u2502 Waiting for activity...",
            style={"color": "#484f58", "fontStyle": "italic", "padding": "8px 0"},
        )

    children = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        # separator
        if entry.get("s") == "separator":
            children.append(
                html.Div(
                    "\u2500" * 52,
                    style={"color": "#21262d", "margin": "6px 0", "userSelect": "none"},
                )
            )
            continue
        children.append(_render_one(entry))

    return html.Div(children)


# ── Layout factory ─────────────────────────────────────────────────

def create_progress_box(page_id: str, store_ids: List[str]) -> html.Div:
    """
    Return the full progress-box widget: hidden stores + visible card.

    Parameters
    ----------
    page_id : str
        Unique page identifier (e.g. "dash", "explore").
    store_ids : list[str]
        Full ``id`` strings for each dcc.Store that callbacks will write to.
    """
    stores = [dcc.Store(id=sid, data=None) for sid in store_ids]

    header_bar = html.Div(
        [
            html.Div(
                [
                    html.I(
                        className="fas fa-terminal",
                        style={"color": "#58a6ff", "marginRight": "8px"},
                    ),
                    html.Span(
                        "Activity Log",
                        style={"fontWeight": "600", "color": "#e6edf3", "letterSpacing": "0.3px"},
                    ),
                ],
                style={"display": "flex", "alignItems": "center"},
            ),
            dbc.Button(
                html.I(id=f"progress-icon-{page_id}", className="fas fa-chevron-down"),
                id=f"progress-toggle-{page_id}",
                color="link",
                size="sm",
                style={"color": "#8b949e", "padding": "2px 8px", "fontSize": "0.7rem"},
            ),
        ],
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "padding": "8px 14px",
            "backgroundColor": "#161b22",
            "borderRadius": "10px 10px 0 0",
            "borderBottom": "1px solid #30363d",
        },
    )

    body = dbc.Collapse(
        html.Div(
            id=f"progress-entries-{page_id}",
            style={
                "maxHeight": "320px",
                "overflowY": "auto",
                "overflowX": "hidden",
                "padding": "10px 14px",
                "backgroundColor": "#0d1117",
                "borderRadius": "0 0 10px 10px",
                "fontFamily": "'Cascadia Code', 'Fira Code', 'SF Mono', 'Consolas', monospace",
                "fontSize": "0.78rem",
                "lineHeight": "1.7",
            },
        ),
        id=f"progress-body-{page_id}",
        is_open=True,
    )

    container = html.Div(
        [header_bar, body],
        style={
            "position": "fixed",
            "bottom": "20px",
            "right": "20px",
            "width": "500px",
            "zIndex": 9998,
            "boxShadow": "0 8px 32px rgba(0,0,0,0.45)",
            "borderRadius": "10px",
            "border": "1px solid #30363d",
        },
    )

    return html.Div([*stores, container])
