# utils/ui_components.py

import pandas as pd
import re
from dash import html
from config.constants import KW_RANGES, COLORS
from utils.data_processor import format_date_to_ddmmyyyy
from utils.display_handlers import (
    handle_semiannual_display,
    handle_quarterly_display,
    handle_m_months_grouping,
    create_sample_box,
    get_colors_for_state
)


def create_progress_bar(completed, total, haeufigkeit=""):
    """Create a progress bar component"""
    try:
        completed = int(completed)
        total = int(total)
        percent = int((completed / total) * 100) if total else 0
    except (TypeError, ValueError):
        completed = 0
        total = 0
        percent = 0

    is_complete = percent >= 100
    bar_color = COLORS['progress_complete'] if is_complete else COLORS['progress_incomplete']
    text_color = "#ffffff" if is_complete else "#212529"

    return html.Div([
        html.Div([
            # Filled bar
            html.Div(style={
                "width": f"{percent}%",
                "backgroundColor": bar_color,
                "height": "100%",
                "borderRadius": "4px"
            }),
            # Overlayed text
            html.Div(f"{completed}/{total} | {haeufigkeit}", style={
                "position": "absolute",
                "left": "50%",
                "top": "50%",
                "transform": "translate(-50%, -50%)",
                "fontSize": "14px",
                "fontWeight": "600",
                "color": text_color,
                "whiteSpace": "nowrap",
                "textShadow": "0 0 1px rgba(0,0,0,0.2)",
                "-webkit-font-smoothing": "antialiased",
                "letterSpacing": "0.2px"
            })
        ], style={
            "position": "relative",
            "height": "22px",
            "backgroundColor": "#e9ecef",
            "borderRadius": "4px",
            "overflow": "hidden",
            "textAlign": "center",
            "lineHeight": "22px"
        })
    ], style={"marginBottom": "6px"})


def create_month_value_display(param_data):
    """Create month value display based on frequency type"""
    if not param_data or not param_data.get("month_data"):
        return html.Div("-", style={"textAlign": "center", "color": "#999"})

    haeufigkeit = param_data.get("haeufigkeit", "").strip().lower()

    # Handle special frequency cases
    if haeufigkeit == "quartalsmäßig":
        quarterly_display = handle_quarterly_display(param_data)
        if quarterly_display is not None:
            return quarterly_display

    elif haeufigkeit == "halbjährlich":
        semiannual_display = handle_semiannual_display(param_data)
        if semiannual_display is not None:
            return semiannual_display

    # Special handling for cases where we show a grouped Jan-Dec calendar
    # Both "Unregelmäßig" and "Jährlich" with "m" values
    if haeufigkeit in ["unregelmäßig", "jährlich"]:
        month_data = param_data.get("month_data", {})
        all_m_values = True

        # Check if all months have "m" value
        for month_name, month_info in month_data.items():
            if isinstance(month_name, str) and month_name in KW_RANGES:
                col_types = month_info.get("col_type", {})
                kw_value = col_types.get("KW", "")
                if not (isinstance(kw_value, str) and kw_value.strip().lower() == "m"):
                    all_m_values = False
                    break

        if all_m_values:
            return handle_m_months_grouping(param_data)

    # Default month rendering logic
    return _original_month_rendering_logic(param_data)


def _original_month_rendering_logic(param_data):
    """Original month rendering logic for standard cases"""
    proben_gesamt = param_data.get("proben_gesamt", 0)
    completed = param_data.get("completed", 0)
    month_data = param_data["month_data"]
    pn_type = param_data.get("pn_type", "").strip()
    haeufigkeit = param_data.get("haeufigkeit", "").strip().lower()

    month_order = list(KW_RANGES.keys())
    sorted_months = sorted(
        [m for m in month_data if isinstance(m, str) and m in KW_RANGES],
        key=lambda m: month_order.index(m)
    )

    month_divs = []

    for month in sorted_months:
        month_info = month_data[month]
        col_types = month_info.get("col_type", {})

        # Extract values for this month
        kw_value_raw = col_types.get("KW", "")
        ist_value_raw = col_types.get("Ist", "")
        datum_val = col_types.get("Datum", "")

        # Determine number of samples required
        required_samples = _calculate_required_samples(kw_value_raw)

        # Determine actual samples taken
        actual_samples_taken = _calculate_actual_samples(ist_value_raw)

        # Determine if this month should be shown
        sample_expected = actual_samples_taken > 0 or (isinstance(datum_val, str) and datum_val.strip()) or isinstance(
            datum_val, pd.Timestamp)
        should_show_month = (completed >= proben_gesamt and sample_expected) or (completed < proben_gesamt)

        if not should_show_month:
            continue

        # Determine dates for this month
        dates = _extract_dates(datum_val)

        # Handle different KW formats
        if "kw" in str(kw_value_raw).lower():
            month_divs.extend(_handle_kw_format(month, kw_value_raw, actual_samples_taken, dates, haeufigkeit, pn_type))
        elif 'T' in str(kw_value_raw):
            month_divs.extend(
                _handle_t_day_format(month, kw_value_raw, actual_samples_taken, dates, haeufigkeit, pn_type))
        else:
            month_divs.append(
                _handle_standard_month(month, actual_samples_taken, required_samples, dates, haeufigkeit, pn_type))

    return html.Div(month_divs, style={"display": "flex", "flexWrap": "wrap", "gap": "6px", "padding": "8px 0"})


def _calculate_required_samples(kw_value_raw):
    """Calculate required number of samples from KW value"""
    required_samples = 1  # Default value
    try:
        if isinstance(kw_value_raw, (int, float)) and not pd.isna(kw_value_raw):
            required_samples = int(kw_value_raw)
        elif isinstance(kw_value_raw, str):
            if kw_value_raw.strip().lower() == "m":
                required_samples = 1
            elif kw_value_raw.strip().isdigit():
                required_samples = int(kw_value_raw.strip())
            elif "kw" in kw_value_raw.lower():
                # Handle KW format
                match = re.findall(r'KW[\s:]*([\d;]+)', kw_value_raw)
                if match:
                    kw_numbers = [k.strip() for k in match[0].split(';') if k.strip().isdigit()]
                    required_samples = len(kw_numbers) if len(kw_numbers) > 0 else 1
            elif 't' in kw_value_raw.lower():
                # Handle T-day format
                t_days = re.findall(r'T(\d+)', kw_value_raw)
                required_samples = len(t_days) if len(t_days) > 0 else 1
            else:
                # Try to extract any numbers
                match = re.findall(r'\d+', kw_value_raw)
                if match:
                    if len(match) == 1:
                        required_samples = int(match[0])
                    elif ';' in kw_value_raw:
                        required_samples = len(match)
    except:
        required_samples = 1

    return required_samples


def _calculate_actual_samples(ist_value_raw):
    """Calculate actual number of samples taken"""
    actual_samples_taken = 0
    try:
        if isinstance(ist_value_raw, (int, float)) and not pd.isna(ist_value_raw):
            actual_samples_taken = int(ist_value_raw)
        elif isinstance(ist_value_raw, str):
            if ist_value_raw.strip().isdigit():
                actual_samples_taken = int(ist_value_raw.strip())
            else:
                # Count T occurrences or extract numbers
                ist_t_values = re.findall(r'T?(\d+)', ist_value_raw)
                actual_samples_taken = len(ist_t_values) if ist_t_values else 0
    except:
        actual_samples_taken = 0

    return actual_samples_taken


def _extract_dates(datum_val):
    """Extract dates from datum value"""
    dates = []
    if isinstance(datum_val, str) and ";" in datum_val:
        dates = [format_date_to_ddmmyyyy(d.strip()) for d in datum_val.split(";")]
    elif isinstance(datum_val, pd.Timestamp):
        dates = [format_date_to_ddmmyyyy(datum_val)]
    elif datum_val and not pd.isna(datum_val):
        dates = [format_date_to_ddmmyyyy(datum_val)]
    return dates


def _handle_kw_format(month, kw_value_raw, actual_samples_taken, dates, haeufigkeit, pn_type):
    """Handle KW format display"""
    month_divs = []
    match = re.findall(r'KW[\s:]*([\d;]+)', str(kw_value_raw))
    if match:
        kw_numbers = [k.strip() for k in match[0].split(';') if k.strip().isdigit()]
        for idx, kw in enumerate(kw_numbers):
            header_text = f"{month} KW{kw}"

            if len(kw_numbers) == 1:
                taken = actual_samples_taken
            else:
                taken = 1 if idx < actual_samples_taken else 0

            details = []
            if haeufigkeit.lower() not in ["täglich", "zweimalig pro woche"]:
                details = [dates[idx]] if idx < len(dates) else []

            bg_color, text_color, border_color = get_colors_for_state(taken, 1, pn_type)

            month_divs.append(create_sample_box(
                header_text, taken, 1, details, bg_color, text_color, border_color
            ))

    return month_divs


def _handle_t_day_format(month, kw_value_raw, actual_samples_taken, dates, haeufigkeit, pn_type):
    """Handle T-day format display"""
    month_divs = []
    t_days = re.findall(r'T(\d+)', str(kw_value_raw))
    for idx, t_day in enumerate(t_days):
        # Modified header format to show day first, then month
        header_text = f"{t_day} {month}"

        if len(t_days) == 1:
            taken = actual_samples_taken
        else:
            taken = 1 if idx < actual_samples_taken else 0

        details = []
        if haeufigkeit.lower() not in ["täglich", "zweimalig pro woche"]:
            details = [dates[idx]] if idx < len(dates) else []

        bg_color, text_color, border_color = get_colors_for_state(taken, 1, pn_type)

        month_divs.append(create_sample_box(
            header_text, taken, 1, details, bg_color, text_color, border_color
        ))

    return month_divs


def _handle_standard_month(month, actual_samples_taken, required_samples, dates, haeufigkeit, pn_type):
    """Handle standard month display"""
    bg_color, text_color, border_color = get_colors_for_state(actual_samples_taken, required_samples, pn_type)

    details = [] if haeufigkeit.lower() in ["täglich", "zweimalig pro woche"] else dates

    return create_sample_box(
        month, actual_samples_taken, required_samples, details, bg_color, text_color, border_color
    )


def create_customer_table_with_scroll(table_body_rows, sorted_params):
    """Create complete table (header + body) with horizontal scroll container"""
    # Create header cells
    header_cells = [
        _create_header_cell("Messstelle", "column-messstelle"),
        _create_header_cell("Zapfstelle", "column-zapfstelle")
    ]
    header_cells.extend([
        _create_header_cell(param, "column-parameter") for param in sorted_params
    ])

    # Create table body rows
    formatted_rows = []
    for row_data in table_body_rows:
        table_cells = [
            html.Td(row_data["Messstelle"], className="table-cell-location column-messstelle"),
            html.Td(row_data["Zapfstelle"], className="table-cell-location column-zapfstelle")
        ]

        for param in sorted_params:
            if param in row_data:
                param_data = row_data[param]
                completed = param_data.get("completed", 0)
                total = param_data.get("proben_gesamt", 0)

                # Skip parameters that are empty or 0/0
                if (total == 0 and completed == 0) or param.lower() in ["", "nan", "none"]:
                    table_cells.append(html.Td("-", className="table-cell-empty column-parameter"))
                    continue

                haeufigkeit = param_data.get("haeufigkeit", "")

                cell_content = html.Div([
                    create_progress_bar(completed, total, haeufigkeit),
                    create_month_value_display(param_data)
                ])

                table_cells.append(html.Td(
                    cell_content,
                    className="table-cell-data column-parameter"
                ))
            else:
                table_cells.append(html.Td("-", className="table-cell-empty column-parameter"))

        formatted_rows.append(html.Tr(table_cells))

    # Create complete table with both header and body
    complete_table = html.Table([
        html.Thead(html.Tr(header_cells)),
        html.Tbody(formatted_rows)
    ], className="customer-table")

    # Wrap the entire table in scroll container
    return html.Div(
        complete_table,
        className="table-scroll-container"
    )


def _create_header_cell(text, column_class=""):
    """Create a standardized header cell with optional column class"""
    return html.Th(text, className=f"table-header-cell {column_class}", style={
        "backgroundColor": COLORS['header_bg'],
        "color": "white",
        "fontWeight": "600",
        "fontSize": "16px",
        "padding": "12px",
        "border": "1px solid #ddd",
        "textAlign": "center",
        "whiteSpace": "normal",
        "wordBreak": "break-word",
        "-webkit-font-smoothing": "antialiased",
        "textRendering": "optimizeLegibility",
        "letterSpacing": "0.1px"
    })


def create_customer_header(kunde_name):
    """Create customer header with sticky positioning"""
    return html.Div([
        html.H3(kunde_name, style={
            "margin": "0",
            "fontWeight": "bold",
            "padding": "15px 20px",
            "color": "#2c3e50",
            "backgroundColor": "#f8f9fa",
            "borderBottom": "2px solid #3498db"
        })
    ], style={
        "position": "sticky",
        "top": "0",
        "backgroundColor": "#ffffff",
        "zIndex": "30"
    })


def create_legend():
    """Create the legend component"""
    return html.Div([
        html.Div("", style={
            "fontWeight": "bold",
            "marginBottom": "10px",
            "fontSize": "18px"
        }),
        html.Div([
            html.H4("Legende", style={"textAlign": "center", "marginBottom": "15px", "fontWeight": "bold"}),

            html.Div([
                html.Div([
                    html.Div(
                        style={"width": "16px", "height": "16px", "backgroundColor": "#B4E380", "borderRadius": "4px",
                               "marginRight": "10px"}),
                    html.Span("Probe genommen", style={"fontSize": "15px"})
                ], style={"display": "flex", "alignItems": "center", "marginBottom": "8px"}),

                html.Div([
                    html.Div(
                        style={"width": "16px", "height": "16px", "backgroundColor": "#1F7D53", "borderRadius": "4px",
                               "marginRight": "10px"}),
                    html.Span("Mehr Proben als nötig", style={"fontSize": "15px"})
                ], style={"display": "flex", "alignItems": "center", "marginBottom": "8px"}),

                html.Div([
                    html.Div(
                        style={"width": "16px", "height": "16px", "backgroundColor": "#CB0404", "borderRadius": "4px",
                               "marginRight": "10px"}),
                    html.Span("Probe nicht genommen (intern)", style={"fontSize": "15px"})
                ], style={"display": "flex", "alignItems": "center", "marginBottom": "8px"}),

                html.Div([
                    html.Div(
                        style={"width": "16px", "height": "16px", "backgroundColor": "#7F55B1", "borderRadius": "4px",
                               "marginRight": "10px"}),
                    html.Span("Probe nicht genommen (extern)", style={"fontSize": "15px"})
                ], style={"display": "flex", "alignItems": "center"})
            ], style={"display": "flex", "flexDirection": "column", "alignItems": "flex-start", "gap": "6px"})

        ], style={
            "padding": "15px 25px",
            "backgroundColor": "#f8f9fa",
            "borderRadius": "10px",
            "margin": "20px auto",
            "maxWidth": "300px",
            "boxShadow": "0 2px 5px rgba(0,0,0,0.1)",
            "textAlign": "left"
        })
    ])