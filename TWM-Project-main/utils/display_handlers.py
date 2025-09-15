# utils/display_handlers.py

import pandas as pd
import re
from dash import html
from config.constants import KW_RANGES, COLORS, QUARTERS, HALFYEARS
from utils.data_processor import format_date_to_ddmmyyyy


def get_colors_for_state(taken, required, pn_type):
    """Get color scheme based on sample state"""
    if taken > required:
        return COLORS['excess']['bg'], COLORS['excess']['text'], COLORS['excess']['border']
    elif taken == required:
        return COLORS['completed']['bg'], COLORS['completed']['text'], COLORS['completed']['border']
    else:
        if pn_type == "E":
            return COLORS['missing_external']['bg'], COLORS['missing_external']['text'], COLORS['missing_external'][
                'border']
        else:
            return COLORS['missing_internal']['bg'], COLORS['missing_internal']['text'], COLORS['missing_internal'][
                'border']


def handle_semiannual_display(param_data):
    """Special handling for 'Halbjährlich' frequency."""
    if not param_data or not param_data.get("month_data"):
        return None

    haeufigkeit = param_data.get("haeufigkeit", "").strip().lower()
    if haeufigkeit != "halbjährlich":
        return None

    month_data = param_data["month_data"]
    pn_type = param_data.get("pn_type", "").strip()
    proben_gesamt = param_data.get("proben_gesamt", 0)
    completed = param_data.get("completed", 0)

    halfyear_divs = []

    # Go through each half-year
    for halfyear in HALFYEARS:
        # Check if any samples were taken in this half-year
        halfyear_months = [m for m in halfyear["months"] if m in month_data]

        samples_taken = 0
        dates = []

        for month in halfyear_months:
            month_info = month_data[month]
            col_types = month_info.get("col_type", {})

            ist_value = col_types.get("Ist", "")
            datum_val = col_types.get("Datum", "")

            # Count samples
            if isinstance(ist_value, (int, float)) and not pd.isna(ist_value):
                samples_taken += int(ist_value)
            elif isinstance(ist_value, str):
                ist_t_values = re.findall(r'T?(\d+)', ist_value)
                samples_taken += len(ist_t_values)

            # Collect dates
            if isinstance(datum_val, str) and ";" in datum_val:
                dates.extend([format_date_to_ddmmyyyy(d.strip()) for d in datum_val.split(";")])
            elif isinstance(datum_val, pd.Timestamp):
                dates.append(format_date_to_ddmmyyyy(datum_val))
            elif datum_val and not pd.isna(datum_val):
                dates.append(format_date_to_ddmmyyyy(datum_val))

        # If no explicit data for this half-year, decide if we should show it
        if not halfyear_months:
            # Show still-to-do half-years if there are remaining samples
            if completed < proben_gesamt:
                samples_taken = 0
                required = 1
                bg_color, text_color, border_color = get_colors_for_state(samples_taken, required, pn_type)

                halfyear_divs.append(create_sample_box(
                    halfyear["name"], samples_taken, required, [], bg_color, text_color, border_color, "120px"
                ))
            continue

        # Define box colors based on whether samples were taken
        required = 1  # One sample per half-year
        bg_color, text_color, border_color = get_colors_for_state(samples_taken, required, pn_type)

        # Create the half-year box
        halfyear_divs.append(create_sample_box(
            halfyear["name"], samples_taken, required, dates if samples_taken > 0 else [],
            bg_color, text_color, border_color, "120px"
        ))

    return html.Div(halfyear_divs, style={"display": "flex", "flexWrap": "wrap", "gap": "6px", "padding": "8px 0"})


def handle_quarterly_display(param_data):
    """Special handling for 'Quartalsmäßig' frequency."""
    if not param_data or not param_data.get("month_data"):
        return None

    haeufigkeit = param_data.get("haeufigkeit", "").strip().lower()
    if haeufigkeit != "quartalsmäßig":
        return None

    month_data = param_data["month_data"]
    pn_type = param_data.get("pn_type", "").strip()
    proben_gesamt = param_data.get("proben_gesamt", 0)
    completed = param_data.get("completed", 0)

    quarter_divs = []

    # Go through each quarter
    for quarter in QUARTERS:
        # Check if any samples were taken in this quarter
        quarter_months = [m for m in quarter["months"] if m in month_data]

        samples_taken = 0
        dates = []

        for month in quarter_months:
            month_info = month_data[month]
            col_types = month_info.get("col_type", {})

            ist_value = col_types.get("Ist", "")
            datum_val = col_types.get("Datum", "")

            # Count samples
            if isinstance(ist_value, (int, float)) and not pd.isna(ist_value):
                samples_taken += int(ist_value)
            elif isinstance(ist_value, str):
                ist_t_values = re.findall(r'T?(\d+)', ist_value)
                samples_taken += len(ist_t_values)

            # Collect dates
            if isinstance(datum_val, str) and ";" in datum_val:
                dates.extend([format_date_to_ddmmyyyy(d.strip()) for d in datum_val.split(";")])
            elif isinstance(datum_val, pd.Timestamp):
                dates.append(format_date_to_ddmmyyyy(datum_val))
            elif datum_val and not pd.isna(datum_val):
                dates.append(format_date_to_ddmmyyyy(datum_val))

        # If no explicit data for this quarter, decide if we should show it
        if not quarter_months:
            # Show still-to-do quarters if there are remaining samples
            if completed < proben_gesamt:
                samples_taken = 0
                required = 1
                bg_color, text_color, border_color = get_colors_for_state(samples_taken, required, pn_type)

                quarter_divs.append(create_sample_box(
                    quarter["name"], samples_taken, required, [], bg_color, text_color, border_color, "100px"
                ))
            continue

        # Define box colors based on whether samples were taken
        required = 1  # One sample per quarter
        bg_color, text_color, border_color = get_colors_for_state(samples_taken, required, pn_type)

        # Create the quarter box
        quarter_divs.append(create_sample_box(
            quarter["name"], samples_taken, required, dates if samples_taken > 0 else [],
            bg_color, text_color, border_color, "100px"
        ))

    return html.Div(quarter_divs, style={"display": "flex", "flexWrap": "wrap", "gap": "6px", "padding": "8px 0"})


def handle_m_months_grouping(param_data):
    """
    Special handler for frequencies with "m" values that should group to "Jan - Dec"
    Works for both "Unregelmäßig" and "Jährlich" frequencies
    """
    if not param_data or not param_data.get("month_data"):
        return html.Div("-", style={"textAlign": "center", "color": "#999"})

    month_data = param_data["month_data"]
    pn_type = param_data.get("pn_type", "").strip()
    haeufigkeit = param_data.get("haeufigkeit", "").strip().lower()
    proben_gesamt = param_data.get("proben_gesamt", 0)
    completed = param_data.get("completed", 0)
    month_order = list(KW_RANGES.keys())

    # First, identify which months have samples taken
    months_with_samples = set()
    all_months = []

    for month in sorted([m for m in month_data if isinstance(m, str) and m in KW_RANGES],
                        key=lambda m: month_order.index(m)):
        all_months.append(month)
        month_info = month_data[month]
        col_types = month_info.get("col_type", {})

        # Check if this month has samples
        ist_value = col_types.get("Ist", "")
        actual_samples_taken = 0

        if isinstance(ist_value, (int, float)) and not pd.isna(ist_value):
            actual_samples_taken = int(ist_value)
        elif isinstance(ist_value, str):
            ist_t_values = re.findall(r'T?(\d+)', ist_value)
            actual_samples_taken = len(ist_t_values)

        if actual_samples_taken > 0:
            months_with_samples.add(month)

    # If no samples taken for any month, create a single "Jan - Dec" box
    if not months_with_samples:
        return create_month_range_box(all_months, 0, 1, pn_type)

    # For "Jährlich", once a sample is taken, only show that month
    if haeufigkeit == "jährlich" and months_with_samples:
        month_divs = []
        sample_month = next(iter(sorted(months_with_samples, key=lambda m: month_order.index(m))))

        # Get sample details for the month with sample
        month_info = month_data[sample_month]
        col_types = month_info.get("col_type", {})

        # Get sample details
        ist_value = col_types.get("Ist", "")
        actual_samples_taken = 0

        if isinstance(ist_value, (int, float)) and not pd.isna(ist_value):
            actual_samples_taken = int(ist_value)
        elif isinstance(ist_value, str):
            ist_t_values = re.findall(r'T?(\d+)', ist_value)
            actual_samples_taken = len(ist_t_values)

        # Get dates if any
        datum_val = col_types.get("Datum", "")
        dates = []
        if isinstance(datum_val, str) and ";" in datum_val:
            dates = [format_date_to_ddmmyyyy(d.strip()) for d in datum_val.split(";")]
        elif isinstance(datum_val, pd.Timestamp):
            dates = [format_date_to_ddmmyyyy(datum_val)]
        elif datum_val and not pd.isna(datum_val):
            dates = [format_date_to_ddmmyyyy(datum_val)]

        # Create individual month box for the sample month
        month_divs.append(create_individual_month_box(sample_month, actual_samples_taken, 1, dates, pn_type))

        return html.Div(month_divs, style={"display": "flex", "flexWrap": "wrap", "gap": "6px", "padding": "8px 0"})

    # For "Unregelmäßig", check if required samples are already achieved
    if haeufigkeit == "unregelmäßig":
        month_divs = []

        # Show individual months with samples
        for month in all_months:
            if month in months_with_samples:
                # Create individual month box
                month_info = month_data[month]
                col_types = month_info.get("col_type", {})

                # Get sample details
                ist_value = col_types.get("Ist", "")
                actual_samples_taken = 0

                if isinstance(ist_value, (int, float)) and not pd.isna(ist_value):
                    actual_samples_taken = int(ist_value)
                elif isinstance(ist_value, str):
                    ist_t_values = re.findall(r'T?(\d+)', ist_value)
                    actual_samples_taken = len(ist_t_values)

                # Get dates if any
                datum_val = col_types.get("Datum", "")
                dates = []
                if isinstance(datum_val, str) and ";" in datum_val:
                    dates = [format_date_to_ddmmyyyy(d.strip()) for d in datum_val.split(";")]
                elif isinstance(datum_val, pd.Timestamp):
                    dates = [format_date_to_ddmmyyyy(datum_val)]
                elif datum_val and not pd.isna(datum_val):
                    dates = [format_date_to_ddmmyyyy(datum_val)]

                # Create individual month box
                month_divs.append(create_individual_month_box(month, actual_samples_taken, 1, dates, pn_type))

        # CRITICAL FIX: Only show remaining months if required samples are NOT yet achieved
        if completed < proben_gesamt:
            # Find the last month with samples
            last_sample_month_index = -1
            if months_with_samples:
                for i, month in enumerate(all_months):
                    if month in months_with_samples:
                        last_sample_month_index = i

            # Only group months that come AFTER the last month with samples
            remaining_months = []
            if last_sample_month_index >= 0:
                # Only include months after the last sample month
                for i in range(last_sample_month_index + 1, len(all_months)):
                    month = all_months[i]
                    if month not in months_with_samples:
                        remaining_months.append(month)
            else:
                # If no samples taken, group all months
                remaining_months = [m for m in all_months if m not in months_with_samples]

            # If there are remaining months, create a grouped box
            if remaining_months:
                month_divs.append(create_month_range_box(remaining_months, 0, 1, pn_type))

        return html.Div(month_divs, style={"display": "flex", "flexWrap": "wrap", "gap": "6px", "padding": "8px 0"})

    # Default fallback (should not reach here)
    return create_month_range_box(all_months, 0, 1, pn_type)


def create_sample_box(header_text, taken, required, dates, bg_color, text_color, border_color, min_width="100px"):
    """Helper to create a standardized sample box"""
    detail_elements = []

    if taken > required:
        detail_elements.append(html.Div("Mehr Proben als nötig", style={
            "fontSize": "12px", "color": "#28a745", "fontWeight": "bold", "padding": "2px 0"
        }))

    detail_elements += [
        html.Div(date, style={"fontSize": "12px", "color": "#6c757d", "padding": "1px 0"})
        for date in dates
    ]

    return html.Div([
        html.Div(header_text, style={
            "fontWeight": "bold", "backgroundColor": bg_color, "padding": "4px 8px",
            "borderRadius": "4px 4px 0 0", "border": f"1px solid {border_color}",
            "color": text_color, "textAlign": "center"
        }),
        html.Div([
            html.Div(f"{taken} / {required}", style={"fontSize": "13px", "padding": "2px 0"}),
            *detail_elements
        ], style={
            "backgroundColor": "#f8f9fa", "padding": "4px 8px",
            "border": f"1px solid {border_color}",
            "borderTop": "none", "borderRadius": "0 0 4px 4px", "textAlign": "center"
        })
    ], style={"margin": "4px", "minWidth": min_width, "flex": "0 0 auto"})


def create_individual_month_box(month, taken, required, dates, pn_type):
    """Helper to create an individual month box with sample counts"""
    bg_color, text_color, border_color = get_colors_for_state(taken, required, pn_type)
    return create_sample_box(month, taken, required, dates, bg_color, text_color, border_color)


def create_month_range_box(months, taken, required, pn_type):
    """Helper to create a grouped month range box (e.g., Jan - Dec)"""
    if not months:
        return None

    # Sort months by their order
    month_order = list(KW_RANGES.keys())
    sorted_months = sorted(months, key=lambda m: month_order.index(m))

    # Create range label
    if len(sorted_months) == 1:
        header_text = sorted_months[0]
    else:
        header_text = f"{sorted_months[0]} - {sorted_months[-1]}"

    bg_color, text_color, border_color = get_colors_for_state(taken, required, pn_type)
    return create_sample_box(header_text, taken, required, [], bg_color, text_color, border_color)