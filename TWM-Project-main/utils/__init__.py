# utils/__init__.py

from .data_processor import transform_data, format_date_to_ddmmyyyy
from .ui_components import (
    create_progress_bar,
    create_month_value_display,
    create_customer_header,
    create_legend,
    create_customer_table_with_scroll
)
from .display_handlers import (
    handle_semiannual_display,
    handle_quarterly_display,
    handle_m_months_grouping,
    get_colors_for_state
)

__all__ = [
    'transform_data',
    'format_date_to_ddmmyyyy',
    'create_progress_bar',
    'create_month_value_display',
    'create_customer_header',
    'create_legend',
    'create_customer_table_with_scroll',
    'handle_semiannual_display',
    'handle_quarterly_display',
    'handle_m_months_grouping',
    'get_colors_for_state'
]