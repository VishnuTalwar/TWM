# dashboard_module.py

from dash import html
import traceback

# Import your existing utilities
from utils import (
    transform_data,
    create_customer_header,
    create_legend,
    create_customer_table_with_scroll
)


def process_dashboard_data(contents):
    """Process uploaded Excel data for dashboard functionality"""
    try:
        transformed_data = transform_data(contents)
        return transformed_data, None
    except Exception as e:
        return None, str(e)


def create_dashboard_content(processed_data):
    """Create dashboard content from processed data"""
    if processed_data is None:
        return html.Div("Please upload a file first", style={'textAlign': 'center', 'padding': '50px'})

    try:
        customer_sections = []

        # Add legend
        customer_sections.append(create_legend())

        for kunde_data in processed_data:
            # Customer heading
            customer_header = create_customer_header(kunde_data["Kunde"])

            if kunde_data["Rows"]:
                # Get all parameters
                all_params = set()
                for row in kunde_data["Rows"]:
                    for key in row.keys():
                        if key not in ["Messstelle", "Zapfstelle"]:
                            if isinstance(key, str) and key.strip().lower() not in ["", "nan", "none"]:
                                all_params.add(key.strip())

                # Convert and sort parameters
                str_params = [str(param) for param in all_params]
                sorted_params = sorted(str_params)

                # Create table body rows
                table_body_rows = []
                for row_data in kunde_data["Rows"]:
                    table_body_rows.append(row_data)

                # Create complete table with scroll
                complete_table_with_scroll = create_customer_table_with_scroll(table_body_rows, sorted_params)

                # Wrap in customer section
                customer_section = html.Div([
                    customer_header,
                    complete_table_with_scroll
                ], className="customer-group-container")

                customer_sections.append(customer_section)
            else:
                # If no rows, just add the customer header
                customer_sections.append(html.Div([customer_header], style={"marginBottom": "20px"}))

        return html.Div(customer_sections, className="output-container")

    except Exception as e:
        return html.Div([
            html.H4("❌ Error rendering dashboard:", style={"color": "red"}),
            html.Pre(str(e), style={"backgroundColor": "#f8d7da", "padding": "15px", "borderRadius": "5px"})
        ])


def get_dashboard_layout():
    """Return the dashboard-specific layout components"""
    return html.Div([
        # Dashboard content will be populated by callback
        html.Div(id='dashboard-content')
    ])