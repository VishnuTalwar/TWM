import pandas as pd
import base64
import io
from dash import html, dcc

try:
    import dash_leaflet as dl

    LEAFLET_AVAILABLE = True
except ImportError:
    LEAFLET_AVAILABLE = False
    print("Warning: dash_leaflet not available. Install with: pip install dash-leaflet")

# Category colors for map
CATEGORY_COLORS = {
    "BB": "#e63946", "DEA": "#e9ef29", "DMS": "#f1faee",
    "GW/B": "#6a0dad", "GW/P": "#ff5722", "HB": "#3f51b5",
    "INF": "#e9c46a", "INS": "#7fb069", "MS": "#2ecc71",
    "PRD": "#6d597a", "TWN": "#b5838d", "UFH": "#4a4e69",
    "WGA": "#457b9d", "WW": "#22223b"
}

#  Label display thresholds
LABEL_ZOOM_THRESHOLD = 10
DETAILED_LABEL_ZOOM_THRESHOLD = 12


def parse_excel_data_for_map(contents):
    """Parse uploaded Excel file for map functionality with MULTIPLE PARAMETERS support"""
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_excel(io.BytesIO(decoded), engine='openpyxl')

        # Check if this file has geographical data
        if "Gebiet" not in df.columns:
            return None, "No geographical data found"

        # Check required columns for map
        required_columns = ["Gebiet", "Bereich", "Messstelle", "Zapfstelle", "Parameter", "Proben\nGesamt",
                            "Aktuell\nGesamt"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            return None, f"Missing columns for map: {missing_columns}"

        # Clean and process data
        # Only require Gebiet and Messstelle, allow missing Zapfstelle
        df_clean = df.dropna(subset=["Gebiet", "Messstelle"])
        # Fill missing Zapfstelle with a default value
        df_clean = df_clean.copy()
        df_clean["Zapfstelle"] = df_clean["Zapfstelle"].fillna("Not Specified")

        # Group by coordinates, messstelle, and other identifying info to handle duplicates
        # Group by Gebiet and Messstelle, handle Zapfstelle separately
        grouped = df_clean.groupby(["Gebiet", "Messstelle"])

        processed_data = []
        coordinate_clusters = {}  # Track items at same coordinates

        for (gebiet, messstelle), group in grouped:
            # Get zapfstelle from the first row, or use default
            zapfstelle = group["Zapfstelle"].iloc[0] if not group["Zapfstelle"].isna().all() else "Not Specified"
            try:
                # Parse coordinates
                koordinaten_str = str(gebiet).replace(' ', '').replace('\n', '').replace('\r', '')
                if ',' not in koordinaten_str:
                    continue
                lat, lon = map(float, koordinaten_str.split(','))
                coord_key = f"{lat},{lon}"

                # Check completion - now checking ALL parameters for this location
                vollständig = all(
                    row.get("Aktuell\nGesamt", 0) >= row.get("Proben\nGesamt", 0)
                    for _, row in group.iterrows()
                )

                # Calculate totals - sum ALL parameters for this location
                total_proben = sum(row.get("Proben\nGesamt", 0) for _, row in group.iterrows() if
                                   pd.notna(row.get("Proben\nGesamt", 0)))
                total_aktuell = sum(row.get("Aktuell\nGesamt", 0) for _, row in group.iterrows() if
                                    pd.notna(row.get("Aktuell\nGesamt", 0)))

                # Get additional filter info - collect ALL unique values
                def safe_str_convert(value, default="Unknown"):
                    if pd.isna(value) or value is None:
                        return default
                    return str(value).strip()

                kunde = safe_str_convert(group["Kunde"].iloc[0] if "Kunde" in group.columns else None)

                # ENHANCED: Collect ALL parameters, frequencies, categories, and PN types
                all_parameters = []
                all_frequencies = []
                all_pn_types = []
                all_categories = []

                for _, row in group.iterrows():
                    param = safe_str_convert(row.get('Parameter', ''))
                    freq = safe_str_convert(row.get('Häufigkeit', ''))
                    pn_type_detail = safe_str_convert(row.get('PN (I/E)', ''))
                    category = safe_str_convert(row.get('Bereich', ''))

                    if param != "Unknown" and param.strip():
                        all_parameters.append(param)
                    if freq != "Unknown" and freq.strip():
                        all_frequencies.append(freq)
                    if pn_type_detail != "Unknown" and pn_type_detail.strip():
                        all_pn_types.append(pn_type_detail)
                    if category != "Unknown" and category.strip():
                        all_categories.append(category)

                # Create aggregated strings for backward compatibility
                parameter = ', '.join(list(dict.fromkeys(all_parameters))) if all_parameters else "Unknown"
                häufigkeit = ', '.join(list(dict.fromkeys(all_frequencies))) if all_frequencies else "Unknown"
                pn_type = ', '.join(list(dict.fromkeys(all_pn_types))) if all_pn_types else "Unknown"

                # Use first category for map coloring (backward compatibility)
                bereich = all_categories[0] if all_categories else "Unknown"

                # ENHANCED: Get sample details with FULL parameter info for ALL parameters
                parameter_details = []
                for _, row in group.iterrows():
                    zap = safe_str_convert(row.get('Zapfstelle', ''))
                    param = safe_str_convert(row.get('Parameter', ''))
                    category = safe_str_convert(row.get('Bereich', ''))
                    frequency = safe_str_convert(row.get('Häufigkeit', ''))
                    pn_type_detail = safe_str_convert(row.get('PN (I/E)', ''))
                    aktuell = row.get('Aktuell\nGesamt', 0) if pd.notna(row.get('Aktuell\nGesamt', 0)) else 0
                    proben = row.get('Proben\nGesamt', 0) if pd.notna(row.get('Proben\nGesamt', 0)) else 0

                    if param != "Unknown" and param.strip():
                        parameter_details.append({
                            'parameter': param,
                            'category': category,
                            'frequency': frequency,
                            'type': 'Internal' if pn_type_detail == 'I' else 'External' if pn_type_detail == 'E' else pn_type_detail,
                            'zapfstelle': zap,
                            'current': aktuell,
                            'total': proben,
                            'completion_rate': (aktuell / proben * 100) if proben > 0 else 0
                        })

                item_data = {
                    'lat': lat,
                    'lon': lon,
                    'messstelle': safe_str_convert(messstelle),
                    'zapfstelle': safe_str_convert(zapfstelle),
                    'bereich': bereich,  # Primary category for map coloring
                    'kunde': kunde,
                    'parameter': parameter,  # All parameters concatenated
                    'häufigkeit': häufigkeit,  # All frequencies concatenated
                    'pn_type': pn_type,  # All PN types concatenated
                    'vollständig': vollständig,
                    'total_samples': total_proben,
                    'completed_samples': total_aktuell,
                    'completion_rate': (total_aktuell / total_proben * 100) if total_proben > 0 else 0,
                    'parameter_details': parameter_details,  # ENHANCED: Full details for ALL parameters
                    'details': parameter_details,  # All details, not limited to 5
                    # NEW: Additional fields for enhanced popup display
                    'parameter_count': len(parameter_details),
                    'all_parameters': all_parameters,
                    'all_frequencies': all_frequencies,
                    'all_categories': all_categories,
                    'all_pn_types': all_pn_types,
                    'is_zero_sample': (total_proben == 0 and total_aktuell == 0)  # Zero sample detection
                }

                # Handle coordinate clustering
                if coord_key not in coordinate_clusters:
                    coordinate_clusters[coord_key] = []
                coordinate_clusters[coord_key].append(item_data)

                processed_data.append(item_data)

            except (ValueError, IndexError):
                continue

        # Mark clustered items
        for coord_key, items in coordinate_clusters.items():
            if len(items) > 1:
                for i, item in enumerate(items):
                    item['is_clustered'] = True
                    item['cluster_size'] = len(items)
                    item['cluster_index'] = i
                    # Slightly offset coordinates to make markers visible
                    offset = 0.0001 * i  # Small offset
                    item['lat'] += offset
                    item['lon'] += offset
            else:
                items[0]['is_clustered'] = False
                items[0]['cluster_size'] = 1
                items[0]['cluster_index'] = 0

        return processed_data, None

    except Exception as e:
        return None, f"Error processing file for map: {str(e)}"


def create_map_pin_icon(color, is_complete, cluster_info=None):
    """Create map pin icon with clustering support"""
    if not LEAFLET_AVAILABLE:
        return None

    symbol = "✓" if is_complete else "✗"
    symbol_color = "#000000"

    # Add cluster indicator if needed
    if cluster_info and cluster_info.get('is_clustered', False):
        cluster_size = cluster_info.get('cluster_size', 1)
        if cluster_size > 1:
            # Add small cluster indicator
            cluster_text = f"<text x='24' y='8' text-anchor='middle' fill='white' font-size='8' font-weight='bold'>{cluster_size}</text>"
        else:
            cluster_text = ""
    else:
        cluster_text = ""

    icon_svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="45" viewBox="0 0 32 45">
        <ellipse cx="16" cy="42" rx="8" ry="3" fill="rgba(0,0,0,0.2)"/>
        <path d="M16 2 C8 2, 2 8, 2 16 C2 24, 16 42, 16 42 S30 24, 30 16 C30 8, 24 2, 16 2 Z" 
              fill="{color}" stroke="#ffffff" stroke-width="2"/>
        <circle cx="16" cy="16" r="9" fill="#ffffff" stroke="rgba(0,0,0,0.2)" stroke-width="1"/>
        <text x="16" y="21" text-anchor="middle" 
              fill="{symbol_color}" font-size="14" font-weight="bold" font-family="Arial">{symbol}</text>
        {cluster_text}
    </svg>
    """

    return {
        "iconUrl": f"data:image/svg+xml;base64,{base64.b64encode(icon_svg.encode()).decode()}",
        "iconSize": [32, 45],
        "iconAnchor": [16, 45],
        "popupAnchor": [0, -45]
    }


def create_enhanced_popup(item):
    """Create enhanced popup content with simple parameter table for multiple parameters"""
    status_icon = "✅" if item['vollständig'] else "❌"
    status_text = "Complete" if item['vollständig'] else "Incomplete"
    status_color = "#28a745" if item['vollständig'] else "#dc3545"

    def safe_truncate(text, max_length=100):
        if not text or text == "Unknown":
            return "Not specified"
        text_str = str(text)
        return f"{text_str[:max_length]}{'...' if len(text_str) > max_length else ''}"

    # Format numbers without decimals
    def format_number(num):
        if isinstance(num, float) and num.is_integer():
            return str(int(num))
        elif isinstance(num, float):
            return f"{num:.0f}"
        return str(num)

    # Add cluster info if applicable
    cluster_info = ""
    if item.get('is_clustered', False) and item.get('cluster_size', 1) > 1:
        cluster_info = html.Div([
            html.Div(f"📍 Location has {item['cluster_size']} measurement points",
                     style={'fontSize': '12px', 'color': '#17a2b8', 'fontWeight': 'bold', 'marginBottom': '8px',
                            'padding': '5px', 'backgroundColor': '#d1ecf1', 'borderRadius': '4px'})
        ])

    # Zero sample info
    zero_sample_info = ""
    if item.get('is_zero_sample', False):
        zero_sample_info = html.Div([
            html.Div("⚠️ Zero Sample Point (0/0)",
                     style={'fontSize': '12px', 'color': '#856404', 'fontWeight': 'bold', 'marginBottom': '8px',
                            'padding': '5px', 'backgroundColor': '#fff3cd', 'borderRadius': '4px'})
        ])

    # Format completion rate without decimals
    completion_rate = int(item['completion_rate']) if item['completion_rate'] == int(item['completion_rate']) else item[
        'completion_rate']

    # Create simple parameter table
    parameter_table = ""
    if item.get('parameter_details') and len(item['parameter_details']) > 0:
        # Create table headers
        table_headers = html.Tr([
            html.Th("Parameter", style={'padding': '8px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6',
                                        'fontWeight': 'bold'}),
            html.Th("Frequency", style={'padding': '8px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6',
                                        'fontWeight': 'bold'}),
            html.Th("Progress", style={'padding': '8px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6',
                                       'fontWeight': 'bold', 'textAlign': 'center'}),
            html.Th("Type", style={'padding': '8px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6',
                                   'fontWeight': 'bold', 'textAlign': 'center'})
        ])

        # Sort parameters alphabetically
        sorted_params = sorted(item['parameter_details'], key=lambda x: x['parameter'])

        # Create table rows
        table_rows = []
        for i, param in enumerate(sorted_params):
            progress_percent = (param['current'] / param['total'] * 100) if param['total'] > 0 else 0
            progress_color = '#28a745' if progress_percent >= 100 else '#ffc107' if progress_percent > 0 else '#dc3545'
            type_color = '#007bff' if param['type'] == 'Internal' else '#dc3545'
            type_text = param['type']
            bg_color = '#fff' if i % 2 == 0 else '#f8f9fa'

            table_rows.append(
                html.Tr([
                    html.Td(param['parameter'],
                            style={'padding': '8px', 'border': '1px solid #dee2e6', 'backgroundColor': bg_color,
                                   'fontWeight': '500'}),
                    html.Td(param['frequency'],
                            style={'padding': '8px', 'border': '1px solid #dee2e6', 'backgroundColor': bg_color}),
                    html.Td([
                        html.Span(f"{param['current']}/{param['total']}",
                                  style={'fontWeight': 'bold', 'color': progress_color, 'marginRight': '8px'}),
                        html.Span(f"({int(progress_percent)}%)",
                                  style={'fontSize': '11px', 'color': progress_color, 'fontWeight': 'bold'})
                    ], style={'padding': '8px', 'border': '1px solid #dee2e6', 'backgroundColor': bg_color,
                              'textAlign': 'center'}),
                    html.Td(
                        html.Span(type_text,
                                  style={'padding': '3px 8px', 'borderRadius': '4px', 'fontSize': '11px',
                                         'fontWeight': 'bold', 'color': 'white', 'backgroundColor': type_color}),
                        style={'padding': '8px', 'border': '1px solid #dee2e6', 'backgroundColor': bg_color,
                               'textAlign': 'center'}
                    )
                ])
            )

        parameter_table = html.Div([
            html.H6("📊 Parameters at this Messstelle",
                    style={'margin': '15px 0 10px 0', 'color': '#2c3e50', 'fontSize': '14px',
                           'borderBottom': '2px solid #007bff', 'paddingBottom': '5px'}),
            html.Table([
                html.Thead(table_headers),
                html.Tbody(table_rows)
            ], style={'width': '100%', 'borderCollapse': 'collapse', 'fontSize': '12px'})
        ])

    return html.Div([
        # Cluster and zero sample info
        cluster_info,
        zero_sample_info,

        # Header
        html.Div([
            html.H3(f"{status_icon} {item['messstelle']}",
                    style={'margin': '0', 'color': 'white', 'fontSize': '18px'}),
            html.P(f"Customer: {item['kunde']}",
                   style={'margin': '5px 0 0 0', 'color': 'rgba(255,255,255,0.9)', 'fontSize': '13px'}),
            html.P(f"Zapfstelle: {item['zapfstelle']}" if item['zapfstelle'] != "Not Specified" else "",
                   style={'margin': '3px 0 0 0', 'color': 'rgba(255,255,255,0.9)', 'fontSize': '13px'})
        ], style={
            'background': f'linear-gradient(135deg, {CATEGORY_COLORS.get(item["bereich"], "#007bff")} 0%, #495057 100%)',
            'padding': '12px', 'borderRadius': '8px 8px 0 0', 'color': 'white'
        }),

        # Overall Status Summary
        html.Div([
            html.Div([
                html.Span("Overall Status:", style={'fontWeight': 'bold', 'fontSize': '14px'}),
                html.Span(f" {status_text}",
                          style={'color': status_color, 'fontWeight': 'bold', 'fontSize': '14px', 'marginLeft': '10px'})
            ], style={'marginBottom': '5px'}),
            html.Div([
                html.Span("Total Progress:", style={'fontWeight': 'bold', 'fontSize': '13px'}),
                html.Span(
                    f" {format_number(item['completed_samples'])}/{format_number(item['total_samples'])} ({format_number(completion_rate)}%)",
                    style={'fontWeight': 'bold', 'fontSize': '13px', 'marginLeft': '10px'})
            ])
        ], style={'padding': '10px', 'backgroundColor': '#f8f9fa', 'borderRadius': '6px', 'margin': '8px 0',
                  'border': '1px solid #dee2e6'}),

        # Parameter table
        parameter_table

    ], style={
        'fontFamily': 'Arial, sans-serif',
        'minWidth': '400px',
        'maxWidth': '600px',
        'border': '1px solid #dee2e6',
        'borderRadius': '8px',
        'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
    })


def create_text_label_marker(item, zoom_level):
    """Simple popup-based labels instead of separate markers"""
    # Don't create separate label markers anymore
    # Labels will be handled as popups that show/hide based on zoom
    return None


# If the JavaScript approach still doesn't work, use this simpler version:

# Extract only the create_map function that needs to be updated
def create_map(data, show_complete=True, show_incomplete=True, selected_categories=None,
               selected_customers=None, selected_parameters=None, selected_frequencies=None,
               selected_pn_types=None, use_satellite=False, zoom_level=9):
    """
    Create Leaflet map with zoom-based label visibility
    """
    if not LEAFLET_AVAILABLE:
        return html.Div([
            html.Div([
                html.H3("🗺️ Map Not Available", style={'color': '#dc3545', 'marginBottom': '10px'}),
                html.P("dash-leaflet is not installed. Install it with:", style={'marginBottom': '10px'}),
                html.Code("pip install dash-leaflet", style={'backgroundColor': '#f8f9fa', 'padding': '5px'}),
                html.P("Then restart your application.", style={'marginTop': '10px'})
            ], style={'textAlign': 'center', 'padding': '50px', 'border': '2px dashed #dc3545', 'borderRadius': '8px'})
        ])

    if not data:
        return html.Div([
            html.Div("🗺️ No map data available", className="map-loading")
        ])

    # Set default filter values
    if selected_categories is None:
        selected_categories = list(CATEGORY_COLORS.keys())
    if selected_customers is None:
        selected_customers = []
    if selected_parameters is None:
        selected_parameters = []
    if selected_frequencies is None:
        selected_frequencies = []
    if selected_pn_types is None:
        selected_pn_types = []

    # Filter data
    filtered_data = []
    for item in data:
        if item['bereich'] not in selected_categories:
            continue
        if not show_complete and item['vollständig']:
            continue
        if not show_incomplete and not item['vollständig']:
            continue
        if selected_customers and item['kunde'] not in selected_customers:
            continue
        if selected_parameters and item['parameter'] not in selected_parameters:
            continue
        if selected_frequencies and item['häufigkeit'] not in selected_frequencies:
            continue
        if selected_pn_types and item['pn_type'] not in selected_pn_types:
            continue
        filtered_data.append(item)

    if not filtered_data:
        return html.Div([
            html.Div([
                html.H3("🔍 No data matches current filters", style={'color': '#6c757d', 'marginBottom': '10px'}),
                html.P("Try adjusting your filter settings to see map points.", style={'color': '#6c757d'})
            ], style={'textAlign': 'center', 'padding': '50px'})
        ])

    markers = []

    # Determine if we should show labels based on zoom
    show_labels = zoom_level >= LABEL_ZOOM_THRESHOLD

    for item in filtered_data:
        color = CATEGORY_COLORS.get(item['bereich'], '#0000FF')

        # Create cluster info for icon
        cluster_info = {
            'is_clustered': item.get('is_clustered', False),
            'cluster_size': item.get('cluster_size', 1)
        }

        icon = create_map_pin_icon(color, item['vollständig'], cluster_info)

        # Create marker with both hover tooltip and conditional permanent label
        marker_children = [
            # Popup for detailed info
            dl.Popup(create_enhanced_popup(item), closeButton=True, className="custom-popup")
        ]

        # Add hover tooltip
        marker_children.append(
            dl.Tooltip(
                item['messstelle'],
                direction="top",
                offset=[0, -25],
                permanent=False,  # This is the hover tooltip
                className="hover-tooltip"
            )
        )

        # Add permanent label if zoomed in enough
        if show_labels:
            marker_children.append(
                dl.Tooltip(
                    html.Div(item['messstelle'], style={
                        'fontSize': '12px',
                        'fontWeight': 'bold',
                        'padding': '4px 8px',
                        'background': 'rgba(255,255,255,0.95)',
                        'borderRadius': '4px',
                        'border': '1px solid #ccc',
                        'color': '#333',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.2)'
                    }),
                    permanent=True,  # This is the permanent label
                    direction="top",
                    offset=[0, -35],
                    className="permanent-messstelle-label"
                )
            )

        marker = dl.Marker(
            position=[item['lat'], item['lon']],
            icon=icon,
            children=marker_children,
            id=f"marker-{item['messstelle']}-{item['lat']}-{item['lon']}"
        )
        markers.append(marker)

    print(
        f"📍 Created {len(markers)} markers at zoom level {zoom_level} (labels {'shown' if show_labels else 'hidden'})")

    # Choose map tiles
    if use_satellite:
        base_layer = dl.TileLayer(
            url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
            attribution="© Google",
            id="google-hybrid"
        )
    else:
        base_layer = dl.TileLayer(
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attribution="© OpenStreetMap contributors",
            id="osm-base"
        )

    # Create the map component
    map_component = dl.Map(
        children=[base_layer] + markers,
        style={'width': '100%', 'height': '70vh'},
        center=[52.318417, 11.567817],
        zoom=zoom_level,
        id="main-map",
        className="enhanced-map",
        zoomControl=True,
        attributionControl=True
    )

    return html.Div([map_component])


# Alternative: If you want permanent labels, you can create separate label markers:
def create_map_with_permanent_labels(data, show_complete=True, show_incomplete=True,
                                     selected_categories=None, use_satellite=False, zoom_level=9):
    """Alternative with permanent label markers (always visible)"""
    if not LEAFLET_AVAILABLE or not data:
        return html.Div("Map not available")

    # Set defaults
    if selected_categories is None:
        selected_categories = list(CATEGORY_COLORS.keys())

    # Filter data (same logic as main function)
    filtered_data = []
    for item in data:
        if item['bereich'] not in selected_categories:
            continue
        if not show_complete and item['vollständig']:
            continue
        if not show_incomplete and not item['vollständig']:
            continue
        filtered_data.append(item)

    if not filtered_data:
        return html.Div("No data matches filters")

    # Choose base layer
    if use_satellite:
        base_layer = dl.TileLayer(
            url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
            attribution="© Google"
        )
    else:
        base_layer = dl.TileLayer(
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attribution="© OpenStreetMap contributors"
        )

    markers = []
    labels = []

    for item in filtered_data:
        color = CATEGORY_COLORS.get(item['bereich'], '#0000FF')

        # Regular marker
        marker = dl.Marker(
            position=[item['lat'], item['lon']],
            icon=create_map_pin_icon(color, item['vollständig']),
            children=[dl.Popup(create_enhanced_popup(item))]
        )
        #markers.append(marker)

        # Label marker (only at high zoom)
        if zoom_level >= 12:
            # Simple text label using divIcon
            label = dl.Marker(
                position=[item['lat'], item['lon']],
                icon={
                    "iconUrl": "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==",
                    # Transparent pixel
                    "iconSize": [1, 1],
                    "iconAnchor": [0, 0]
                },
                children=[
                    dl.Tooltip(
                        item['messstelle'],
                        permanent=True,
                        direction="top",
                        className="permanent-label"
                    )
                ]
            )
            labels.append(label)

    # Create complete map
    return dl.Map(
        children=[base_layer] + markers + labels,
        style={'width': '100%', 'height': '70vh'},
        center=[52.318417, 11.567817],
        zoom=zoom_level,
        id="main-map",
        className="enhanced-map"
    )


# Keep all other functions as they were...
def create_filter_options(data, column_name):
    """Create filter options for dropdown"""
    if not data:
        return []

    values = []
    for item in data:
        value = item.get(column_name)
        if value is not None and str(value).strip() and str(value).lower() != 'nan':
            str_value = str(value).strip()
            if str_value:
                values.append(str_value)

    unique_values = list(set(values))
    unique_values.sort()

    return [{'label': value, 'value': value} for value in unique_values]


def create_pn_type_filter_options(data):
    """Create PN type filter options with counts"""
    if not data:
        return []

    pn_type_counts = {}
    for item in data:
        pn_type = item.get('pn_type', 'Unknown')
        if pn_type and str(pn_type).strip():
            pn_type_counts[pn_type] = pn_type_counts.get(pn_type, 0) + 1

    options = []
    for pn_type in sorted(pn_type_counts.keys()):
        count = pn_type_counts[pn_type]
        label = f"{'Internal' if pn_type == 'I' else 'External' if pn_type == 'E' else pn_type} ({count})"

        options.append({
            'label': html.Div([
                html.Div(style={
                    'width': '16px', 'height': '16px',
                    'backgroundColor': '#007bff' if pn_type == 'I' else '#dc3545' if pn_type == 'E' else '#6c757d',
                    'border': '2px solid white', 'borderRadius': '3px',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.3)', 'marginRight': '8px',
                    'display': 'inline-block', 'verticalAlign': 'middle'
                }),
                html.Span(label, style={
                    'fontSize': '14px', 'fontWeight': '500', 'verticalAlign': 'middle'
                })
            ], style={'display': 'flex', 'alignItems': 'center'}),
            'value': pn_type
        })

    return options


def create_enhanced_category_options(data):
    """Create category options with colors and counts - side by side layout"""
    if not data:
        return []

    category_counts = {}
    for item in data:
        category_counts[item['bereich']] = category_counts.get(item['bereich'], 0) + 1

    options = []
    for category in sorted(category_counts.keys()):
        color = CATEGORY_COLORS.get(category, '#000000')
        count = category_counts[category]

        # NEW: Create side-by-side layout with color indicator and text
        options.append({
            'label': html.Div([
                # Container for the entire category item
                html.Div([
                    # Color indicator (comes after checkbox, before text)
                    html.Div(style={
                        'width': '14px',
                        'height': '14px',
                        'backgroundColor': color,
                        'border': '2px solid white',
                        'borderRadius': '3px',
                        'boxShadow': '0 1px 3px rgba(0,0,0,0.3)',
                        'marginRight': '6px',
                        'marginLeft': '2px',
                        'flexShrink': '0',
                        'display': 'inline-block'
                    }, className='category-color-indicator'),

                    # Category text with count
                    html.Span(f"{category} ({count})",
                              className='category-text',
                              style={
                                  'fontSize': '11px',
                                  'fontWeight': '500',
                                  'overflow': 'hidden',
                                  'textOverflow': 'ellipsis',
                                  'whiteSpace': 'nowrap',
                                  'flex': '1'
                              }
                              )
                ], className='category-item-container', style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'width': '100%'
                })
            ]),
            'value': category
        })

    return options


def create_enhanced_category_options_for_dropdown(data):
    """Create category options for dropdown (not checklist)"""
    if not data:
        return []

    category_counts = {}
    for item in data:
        category_counts[item['bereich']] = category_counts.get(item['bereich'], 0) + 1

    options = []
    for category in sorted(category_counts.keys()):
        color = CATEGORY_COLORS.get(category, '#000000')
        count = category_counts[category]

        options.append({
            'label': f"● {category} ({count})",  # Simple colored bullet
            'value': category
        })

    return options


def create_cascading_filter_options_enhanced(data, selected_filters):
    """Create filter options based on current selections with proper cascading"""
    if not data:
        return {
            'customers': [],
            'parameters': [],
            'categories': [],
            'frequencies': [],
            'pn_types': []
        }

    # Start with all data
    filtered_data = data.copy()

    # Apply filters in order: customer -> parameter -> category -> frequency -> pn_type
    if selected_filters.get('customers'):
        filtered_data = [item for item in filtered_data if item['kunde'] in selected_filters['customers']]

    if selected_filters.get('parameters'):
        filtered_data = [item for item in filtered_data if item['parameter'] in selected_filters['parameters']]

    if selected_filters.get('categories'):
        filtered_data = [item for item in filtered_data if item['bereich'] in selected_filters['categories']]

    if selected_filters.get('frequencies'):
        filtered_data = [item for item in filtered_data if item['häufigkeit'] in selected_filters['frequencies']]

    if selected_filters.get('pn_types'):
        filtered_data = [item for item in filtered_data if item['pn_type'] in selected_filters['pn_types']]

    return {
        'customers': create_filter_options(filtered_data, 'kunde'),
        'parameters': create_filter_options(filtered_data, 'parameter'),
        'categories': create_enhanced_category_options_for_dropdown(filtered_data),
        'frequencies': create_filter_options(filtered_data, 'häufigkeit'),
        'pn_types': create_pn_type_filter_options(filtered_data)
    }




def create_statistics(data, filtered_data):
    """Create statistics panel for map"""
    total = len(filtered_data)
    complete = sum(1 for item in filtered_data if item['vollständig'])
    incomplete = total - complete
    total_samples = sum(item['total_samples'] for item in filtered_data)
    completed_samples = sum(item['completed_samples'] for item in filtered_data)

    # Additional stats
    unique_customers = len(set([item['kunde'] for item in filtered_data]))
    unique_parameters = len(set([item['parameter'] for item in filtered_data]))

    # PN type statistics
    internal_count = sum(1 for item in filtered_data if item['pn_type'] == 'I')
    external_count = sum(1 for item in filtered_data if item['pn_type'] == 'E')

    stats_items = [
        {"icon": "📍", "value": str(total), "label": "Total Points", "color": "#007bff"},
        {"icon": "✅", "value": str(complete), "label": "Complete", "color": "#28a745"},
        {"icon": "❌", "value": str(incomplete), "label": "Incomplete", "color": "#dc3545"},
        {"icon": "📊", "value": f"{complete / total * 100:.1f}%" if total > 0 else "0%", "label": "Success Rate",
         "color": "#17a2b8"},
        {"icon": "🔢", "value": f"{completed_samples}/{total_samples}", "label": "Samples", "color": "#6c757d"},
        {"icon": "👥", "value": str(unique_customers), "label": "Customers", "color": "#fd7e14"},
        {"icon": "🧪", "value": str(unique_parameters), "label": "Parameters", "color": "#6f42c1"},
        {"icon": "🏢", "value": str(internal_count), "label": "Internal", "color": "#007bff"},
        {"icon": "🌐", "value": str(external_count), "label": "External", "color": "#dc3545"}
    ]

    stats_cards = []
    for stat in stats_items:
        stats_cards.append(
            html.Div([
                html.Div(stat["icon"], className="stats-icon"),
                html.Div(stat["value"], className="stats-value", style={'color': stat["color"]}),
                html.Div(stat["label"], className="stats-label")
            ], className="stats-card")
        )

    return html.Div([
        html.H4("📊 Statistics", style={
            'margin': '0 0 15px 0', 'color': '#2c3e50', 'fontSize': '16px',
            'fontWeight': '600', 'borderBottom': '2px solid #17a2b8', 'paddingBottom': '8px'
        }),
        html.Div(stats_cards, style={'display': 'grid', 'gridTemplateColumns': '1fr', 'gap': '8px'})
    ], className='map-control-section stats-section')


def get_map_layout(map_data):
    """Return the map-specific layout components with enhanced filters and compact sidebar"""
    if map_data is None:
        return html.Div([
            html.H3("Map View Not Available", style={'textAlign': 'center', 'color': '#6c757d'}),
            html.P("The uploaded file doesn't contain geographical data (coordinates) required for map visualization.",
                   style={'textAlign': 'center', 'color': '#6c757d'})
        ], style={'padding': '50px'})

    return html.Div([
        # Advanced Filters Section - CASCADING DROPDOWNS
        html.Div([
            html.H4("🔍 Filters", style={
                'margin': '0 0 12px 0', 'color': '#2c3e50', 'fontSize': '18px',
                'textAlign': 'center', 'fontWeight': '600',
                'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                'webkitBackgroundClip': 'text',
                'webkitTextFillColor': 'transparent',
                'backgroundClip': 'text',
                'borderBottom': '2px solid transparent',
                'borderImage': 'linear-gradient(90deg, #667eea, #764ba2) 1',
                'paddingBottom': '6px'
            }),

            # Single row with all cascading filters
            html.Div([
                # Customer Filter
                html.Div([
                    html.Label("👥 Customer:", style={
                        'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block',
                        'fontSize': '12px', 'color': '#495057'
                    }),
                    dcc.Dropdown(
                        id='map-customer-filter',
                        options=create_filter_options(map_data, 'kunde'),
                        value=[],
                        multi=True,
                        placeholder="All customers...",
                        style={'fontSize': '12px', 'minHeight': '32px'},
                        className='enhanced-dropdown',
                        clearable=True
                    )
                ], style={'flex': '1', 'marginRight': '12px'}),

                # Parameter Filter - will update based on customer selection
                html.Div([
                    html.Label("🧪 Parameter:", style={
                        'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block',
                        'fontSize': '12px', 'color': '#495057'
                    }),
                    dcc.Dropdown(
                        id='map-parameter-filter',
                        options=create_filter_options(map_data, 'parameter'),
                        value=[],
                        multi=True,
                        placeholder="All parameters...",
                        style={'fontSize': '12px', 'minHeight': '32px'},
                        className='enhanced-dropdown',
                        clearable=True
                    )
                ], style={'flex': '1', 'marginRight': '12px'}),

                # Category Filter - will update based on previous selections
                html.Div([
                    html.Label("📍 Category:", style={
                        'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block',
                        'fontSize': '12px', 'color': '#495057'
                    }),
                    dcc.Dropdown(
                        id='map-category-dropdown',
                        options=create_enhanced_category_options_for_dropdown(map_data),
                        value=[],
                        multi=True,
                        placeholder="All categories...",
                        style={'fontSize': '12px', 'minHeight': '32px'},
                        className='enhanced-dropdown',
                        clearable=True
                    )
                ], style={'flex': '1', 'marginRight': '12px'}),

                # Frequency Filter - will update based on previous selections
                html.Div([
                    html.Label("📅 Frequency:", style={
                        'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block',
                        'fontSize': '12px', 'color': '#495057'
                    }),
                    dcc.Dropdown(
                        id='map-frequency-filter',
                        options=create_filter_options(map_data, 'häufigkeit'),
                        value=[],
                        multi=True,
                        placeholder="All frequencies...",
                        style={'fontSize': '12px', 'minHeight': '32px'},
                        className='enhanced-dropdown',
                        clearable=True
                    )
                ], style={'flex': '1', 'marginRight': '12px'}),

                # PN Type Filter - will update based on previous selections
                html.Div([
                    html.Label("🏢 PN Type:", style={
                        'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block',
                        'fontSize': '12px', 'color': '#495057'
                    }),
                    dcc.Dropdown(
                        id='map-pn-type-filter',
                        options=create_pn_type_filter_options(map_data),
                        value=[],
                        multi=True,
                        placeholder="All types...",
                        style={'fontSize': '12px', 'minHeight': '32px'},
                        className='enhanced-dropdown',
                        clearable=True
                    )
                ], style={'flex': '1'})

            ], style={'display': 'flex', 'gap': '12px', 'alignItems': 'flex-end'}),

            # Clear all filters button
            html.Div([
                html.Button("Clear All Filters",
                            id="clear-all-filters-btn",
                            n_clicks=0,
                            className='map-button map-button-secondary',
                            style={'marginTop': '10px', 'fontSize': '11px'})
            ], style={'textAlign': 'center', 'marginTop': '8px'})

        ], className='advanced-filters-container', style={'zIndex': '1000', 'position': 'relative'}),

        # Main Content Area with Compact Sidebar
        html.Div([
            # Left Sidebar - NOW MUCH MORE COMPACT (200px instead of 280px)
            html.Div([
                # Basic Controls
                html.Div([
                    html.H4("⚙️ Controls", style={
                        'margin': '0 0 8px 0', 'color': '#2c3e50', 'fontSize': '13px',
                        'fontWeight': '600', 'borderBottom': '2px solid #007bff', 'paddingBottom': '5px'
                    }),

                    # Map Style
                    html.Div([
                        html.Label("🗺️ Map Style:", style={
                            'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block',
                            'fontSize': '11px', 'color': '#495057'
                        }),
                        dcc.RadioItems(
                            id='map-style-radio',
                            options=[
                                {'label': ' Street Map', 'value': 'street'},
                                {'label': ' Satellite + Streets', 'value': 'satellite'}
                            ],
                            value='street',
                            inline=False,
                            inputStyle={'marginRight': '6px'},
                            labelStyle={'marginBottom': '3px', 'display': 'block', 'fontSize': '11px'},
                            className='map-radio'
                        )
                    ], style={'marginBottom': '10px'}),

                    # Status Filter
                    html.Div([
                        html.Label("✅ Status Filter:", style={
                            'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block',
                            'fontSize': '11px', 'color': '#495057'
                        }),
                        dcc.Checklist(
                            id='map-status-filter',
                            options=[
                                {'label': ' ✅ Complete', 'value': 'complete'},
                                {'label': ' ❌ Incomplete', 'value': 'incomplete'}
                            ],
                            value=['complete', 'incomplete'],
                            inline=False,
                            inputStyle={'marginRight': '6px'},
                            labelStyle={'marginBottom': '3px', 'display': 'block', 'fontSize': '11px'},
                            className='map-checklist'
                        )
                    ], style={'marginBottom': '10px'}),

                ], className='map-control-section basic-controls-section'),

                # Categories with enhanced styling and side-by-side layout
                html.Div([
                    html.H4("📍 Categories", style={
                        'margin': '0 0 8px 0', 'color': '#2c3e50', 'fontSize': '13px',
                        'fontWeight': '600', 'borderBottom': '2px solid #28a745', 'paddingBottom': '5px'
                    }),
                    html.Div([
                        html.Button("Select All", id="map-select-all-btn", n_clicks=0,
                                    className='map-button map-button-primary'),
                        html.Button("Clear All", id="map-clear-all-btn", n_clicks=0,
                                    className='map-button map-button-secondary')
                    ], style={'marginBottom': '6px'}),
                    dcc.Checklist(
                        id='map-category-filter',
                        options=create_enhanced_category_options(map_data),
                        value=[item['bereich'] for item in map_data] if map_data else [],
                        inline=False,
                        inputStyle={'marginRight': '6px'},
                        labelStyle={'marginBottom': '4px', 'display': 'block', 'cursor': 'pointer', 'fontSize': '11px'},
                        className='map-checklist'
                    )
                ], className='map-control-section category-section'),

                # Statistics Panel
                html.Div(id='map-stats-container')

            ], className='map-sidebar', style={
                'width': '200px',  # REDUCED from 280px to 200px
                'padding': '0 12px',  # Reduced padding
                'height': '80vh',
                'overflowY': 'auto'
            }),

            # Map Container - Now gets more space
            html.Div([
                # Map zoom level storage
                dcc.Store(id='map-zoom-store', data=9),
                html.Div(id='map-display')
            ], style={'flex': '1', 'height': '80vh', 'marginLeft': '10px'})  # Reduced margin

        ], style={'display': 'flex', 'flexDirection': 'row', 'height': '80vh'})
    ])


def create_cascading_filter_options(data, selected_filters):
    """Create filter options based on current selections"""
    filtered_data = data.copy()

    # Apply current filters to get available options
    if selected_filters.get('customers'):
        filtered_data = [item for item in filtered_data if item['kunde'] in selected_filters['customers']]
    if selected_filters.get('categories'):
        filtered_data = [item for item in filtered_data if item['bereich'] in selected_filters['categories']]
    if selected_filters.get('parameters'):
        filtered_data = [item for item in filtered_data if item['parameter'] in selected_filters['parameters']]
    if selected_filters.get('frequencies'):
        filtered_data = [item for item in filtered_data if item['häufigkeit'] in selected_filters['frequencies']]
    if selected_filters.get('pn_types'):
        filtered_data = [item for item in filtered_data if item['pn_type'] in selected_filters['pn_types']]

    return {
        'customers': create_filter_options(filtered_data, 'kunde'),
        'parameters': create_filter_options(filtered_data, 'parameter'),
        'frequencies': create_filter_options(filtered_data, 'häufigkeit'),
        'pn_types': create_pn_type_filter_options(filtered_data),
        'categories': create_enhanced_category_options(filtered_data)
    }