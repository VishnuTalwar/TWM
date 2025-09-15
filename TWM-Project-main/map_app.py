import json
import os
import traceback
from datetime import datetime

import flask
import numpy as np
import pandas as pd

app = flask.Flask(__name__)

# Create static folders if they don't exist
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

# Global variables
MAP_DATA = None
LAST_ERROR = None
DEBUG_INFO = {}

# Category colors (from your files)
CATEGORY_COLORS = {
    "BB": "#e63946", "DEA": "#e9ef29", "DMS": "#f1faee",
    "GW/B": "#6a0dad", "GW/P": "#ff5722", "HB": "#3f51b5",
    "INF": "#e9c46a", "INS": "#7fb069", "MS": "#2ecc71",
    "PRD": "#6d597a", "TWN": "#b5838d", "UFH": "#4a4e69",
    "WGA": "#457b9d", "WW": "#22223b"
}

# Dashboard application URL
DASHBOARD_APP_URL = "http://127.0.0.1:8050"


def extract_latest_date(row):
    """Extract the most recent date from all Datum columns"""
    import pandas as pd
    from datetime import datetime

    dates = []
    month_names = ['Jan', 'Feb', 'Mrz', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']

    print(f"Extracting date for parameter: {row.get('Parameter', 'Unknown')}")

    # Look through each month's Datum column to find any dates
    for month in month_names:
        datum_col = f"{month}\nDatum"
        datum_value = row.get(datum_col)

        print(f"  {month} Datum: {datum_value} ({type(datum_value)})")

        # Check if this month has a date
        if pd.notna(datum_value) and datum_value != '':
            print(f"    ✅ Found date in {month}, parsing...")

            # Parse the date from this month's Datum column
            parsed_date = parse_date_string(datum_value)
            if parsed_date:
                dates.append(parsed_date)
                print(f"    ✅ Parsed date: {datum_value} -> {parsed_date}")
            else:
                print(f"    ❌ Could not parse date: {datum_value}")
        else:
            print(f"    ➖ No date in {month}")

    # Also check Start Datum and aktuelles Datum columns if they exist
    for col_name in ['Start Datum', 'aktuelles Datum']:
        if col_name in row and pd.notna(row[col_name]) and row[col_name] != '':
            print(f"  {col_name}: {row[col_name]} ({type(row[col_name])})")
            parsed_date = parse_date_string(row[col_name])
            if parsed_date:
                dates.append(parsed_date)
                print(f"    ✅ Parsed {col_name}: {row[col_name]} -> {parsed_date}")

    if dates:
        # Return the most recent date formatted
        latest_date = max(dates)
        result = latest_date.strftime("%d.%m.%Y")
        print(f"  🎯 Latest date found: {result}")
        return result
    else:
        print("  ❌ No dates found in any Datum columns")
        # Check if there are any samples taken but no dates
        aktuell_gesamt = row.get('Aktuell\nGesamt', 0)
        if pd.notna(aktuell_gesamt) and aktuell_gesamt > 0:
            return "Date missing"
        else:
            return None


def parse_date_string(date_value):
    """Parse various date formats commonly found in Excel"""
    import pandas as pd
    from datetime import datetime
    import re

    if pd.isna(date_value) or date_value == '' or date_value is None:
        return None

    # Handle different Excel date formats
    try:
        # If it's already a pandas Timestamp
        if isinstance(date_value, pd.Timestamp):
            return date_value

        # If it's a Python datetime object
        if isinstance(date_value, datetime):
            return date_value

        # If it's an Excel serial date number
        if isinstance(date_value, (int, float)):
            if date_value > 25569:  # Valid Excel date range
                excel_date = pd.to_datetime('1899-12-30') + pd.Timedelta(days=date_value)
                return excel_date
            else:
                return None

        # If it's a string
        if isinstance(date_value, str):
            date_str = date_value.strip()
            if not date_str:
                return None

            # Handle multiple dates separated by semicolon - take the last one
            if ';' in date_str:
                date_parts = [d.strip() for d in date_str.split(';') if d.strip()]
                if date_parts:
                    date_str = date_parts[-1]  # Take the last (most recent) date

            # Common German date formats
            date_formats = [
                '%d.%m.%Y',  # 13.03.2025
                '%d/%m/%Y',  # 13/03/2025
                '%d-%m-%Y',  # 13-03-2025
                '%Y-%m-%d',  # 2025-03-13
                '%d.%m.%y',  # 13.03.25
                '%d/%m/%y',  # 13/03/25
                '%d-%m-%y',  # 13-03-25
            ]

            # Try each format
            for date_format in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, date_format)
                    return parsed_date
                except ValueError:
                    continue

            # Try pandas parsing as fallback
            try:
                parsed_date = pd.to_datetime(date_str, dayfirst=True, errors='coerce')
                if not pd.isna(parsed_date):
                    return parsed_date
            except:
                pass

            # Try regex extraction for messy formats
            try:
                date_pattern = r'(\d{1,2})[./\-](\d{1,2})[./\-](\d{2,4})'
                match = re.search(date_pattern, date_str)
                if match:
                    day, month, year = match.groups()
                    if len(year) == 2:
                        year = '20' + year if int(year) <= 50 else '19' + year

                    try:
                        parsed_date = datetime(int(year), int(month), int(day))
                        return parsed_date
                    except ValueError:
                        pass
            except:
                pass

    except Exception as e:
        print(f"    ❌ Error parsing date {date_value}: {e}")

    return None



def debug_excel_file(file_path):
    """Debug function to analyze Excel file structure"""
    global DEBUG_INFO
    DEBUG_INFO = {}

    try:
        print(f"\n🔍 DEBUGGING EXCEL FILE: {file_path}")

        # Read Excel file
        df = pd.read_excel(file_path, engine='openpyxl')
        print(f"✅ File read successfully. Shape: {df.shape}")

        # Store debug info (convert to basic Python types)
        DEBUG_INFO['file_shape'] = list(df.shape)
        DEBUG_INFO['columns'] = list(df.columns)

        # Convert first few rows to safe format
        first_rows = df.head(3)
        DEBUG_INFO['first_few_rows'] = []
        for _, row in first_rows.iterrows():
            row_dict = {}
            for col in row.index:
                value = row[col]
                if pd.isna(value):
                    row_dict[col] = None
                else:
                    row_dict[col] = str(value)
            DEBUG_INFO['first_few_rows'].append(row_dict)

        print(f"📋 Available columns ({len(df.columns)}):")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i:2d}. '{col}'")

        # Check required columns
        required_columns = ["Gebiet", "Bereich", "Messstelle", "Zapfstelle", "Parameter", "Proben\nGesamt",
                            "Aktuell\nGesamt"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        DEBUG_INFO['required_columns'] = required_columns
        DEBUG_INFO['missing_columns'] = missing_columns

        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            return None, f"Missing required columns: {missing_columns}"
        else:
            print(f"✅ All required columns found!")

        # Check Gebiet column for coordinates
        print(f"\n🗺️ Analyzing 'Gebiet' column for coordinates:")
        gebiet_samples = df['Gebiet'].dropna().head(5)
        DEBUG_INFO['gebiet_samples'] = [str(val) for val in gebiet_samples]

        for i, value in enumerate(gebiet_samples, 1):
            print(f"   {i}. '{value}' (type: {type(value)})")
            if ',' in str(value):
                try:
                    coords_str = str(value).replace(' ', '').replace('\n', '').replace('\r', '')
                    lat, lon = map(float, coords_str.split(','))
                    print(f"      → Parsed as coordinates: {lat}, {lon}")
                except Exception as e:
                    print(f"      → Failed to parse as coordinates: {e}")

        # Check for data after cleaning
        df_clean = df.dropna(subset=["Gebiet", "Messstelle"])
        print(f"\n📊 After removing rows with missing Gebiet/Messstelle: {len(df_clean)} rows")
        DEBUG_INFO['rows_after_cleaning'] = len(df_clean)

        # Try to parse some coordinates
        valid_coords = 0
        for _, row in df_clean.head(10).iterrows():
            try:
                gebiet = str(row['Gebiet']).replace(' ', '').replace('\n', '').replace('\r', '')
                if ',' in gebiet:
                    lat, lon = map(float, gebiet.split(','))
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        valid_coords += 1
            except:
                pass

        print(f"✅ Found {valid_coords} valid coordinates in first 10 rows")
        DEBUG_INFO['valid_coordinates_sample'] = valid_coords

        return df, None

    except Exception as e:
        error_msg = f"Error reading Excel file: {str(e)}"
        print(f"❌ {error_msg}")
        DEBUG_INFO['error'] = error_msg
        DEBUG_INFO['traceback'] = traceback.format_exc()
        return None, error_msg


def parse_excel_data_for_map(file_path):
    """Parse uploaded Excel file for map functionality - ENHANCED with individual parameter sample tracking"""
    global DEBUG_INFO, LAST_ERROR

    try:
        # First, debug the file
        df, error = debug_excel_file(file_path)
        if error:
            LAST_ERROR = error
            return None, error

        print(f"\n🔄 PROCESSING DATA FOR MAP WITH INDIVIDUAL PARAMETER PROGRESS...")

        # Clean data
        df_clean = df.dropna(subset=["Gebiet", "Messstelle"])
        df_clean = df_clean.copy()
        df_clean["Zapfstelle"] = df_clean["Zapfstelle"].fillna("Not Specified")

        print(f"📊 Processing {len(df_clean)} rows after cleaning")

        # Group by coordinates and messstelle
        grouped = df_clean.groupby(["Gebiet", "Messstelle"])
        processed_data = []
        skipped_count = 0
        coordinate_clusters = {}
        zero_sample_count = 0

        print(f"🔍 Processing {len(grouped)} groups...")

        for i, ((gebiet, messstelle), group) in enumerate(grouped):
            try:
                # Parse coordinates
                koordinaten_str = str(gebiet).replace(' ', '').replace('\n', '').replace('\r', '')

                if ',' not in koordinaten_str:
                    print(f"   ⚠️  Group {i + 1}: No comma in coordinates '{koordinaten_str}'")
                    skipped_count += 1
                    continue

                try:
                    lat, lon = map(float, koordinaten_str.split(','))
                except ValueError:
                    print(f"   ⚠️  Group {i + 1}: Cannot parse coordinates '{koordinaten_str}'")
                    skipped_count += 1
                    continue

                # Validate coordinates
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    print(f"   ⚠️  Group {i + 1}: Invalid coordinates {lat}, {lon}")
                    skipped_count += 1
                    continue

                coord_key = f"{lat},{lon}"

                # Get zapfstelle
                zapfstelle = group["Zapfstelle"].iloc[0] if not group["Zapfstelle"].isna().all() else "Not Specified"

                # Calculate totals across ALL parameters
                total_proben = sum(row.get("Proben\nGesamt", 0) for _, row in group.iterrows() if
                                   pd.notna(row.get("Proben\nGesamt", 0)))
                total_aktuell = sum(row.get("Aktuell\nGesamt", 0) for _, row in group.iterrows() if
                                    pd.notna(row.get("Aktuell\nGesamt", 0)))

                # Check if zero sample
                is_zero_sample = (total_proben == 0 and total_aktuell == 0)
                if is_zero_sample:
                    zero_sample_count += 1
                    print(f"   📍 Group {i + 1}: Zero sample point detected - {messstelle}")

                # Check overall completion
                vollständig = all(
                    row.get("Aktuell\nGesamt", 0) >= row.get("Proben\nGesamt", 0)
                    for _, row in group.iterrows()
                )

                # Safe string conversion
                def safe_str_convert(value, default="Unknown"):
                    if pd.isna(value) or value is None:
                        return default
                    return str(value).strip()

                kunde = safe_str_convert(group["Kunde"].iloc[0] if "Kunde" in group.columns else None)

                # ENHANCED: Create individual parameter details with separate sample tracking
                parameter_details = []
                all_parameters = []
                all_frequencies = []
                all_pn_types = []
                all_categories = []

                for _, row in group.iterrows():
                    # Get individual parameter data
                    param = safe_str_convert(row.get('Parameter', ''))
                    category = safe_str_convert(row.get('Bereich', ''))
                    frequency = safe_str_convert(row.get('Häufigkeit', ''))
                    pn_type_raw = safe_str_convert(row.get('PN (I/E)', ''))
                    zapfstelle_row = safe_str_convert(row.get('Zapfstelle', ''))

                    # ENHANCED: Get individual parameter sample counts
                    individual_aktuell = row.get('Aktuell\nGesamt', 0) if pd.notna(row.get('Aktuell\nGesamt', 0)) else 0
                    individual_proben = row.get('Proben\nGesamt', 0) if pd.notna(row.get('Proben\nGesamt', 0)) else 0

                    # Convert to integers safely
                    try:
                        individual_aktuell = int(individual_aktuell)
                    except (ValueError, TypeError):
                        individual_aktuell = 0

                    try:
                        individual_proben = int(individual_proben)
                    except (ValueError, TypeError):
                        individual_proben = 0

                    if param != "Unknown" and param.strip():
                        # FIXED: Map PN type to proper format for filtering
                        if pn_type_raw == 'I':
                            type_display = 'Internal'
                            type_filter = 'I'
                        elif pn_type_raw == 'E':
                            type_display = 'External'
                            type_filter = 'E'
                        else:
                            type_display = pn_type_raw
                            type_filter = pn_type_raw

                        # Calculate individual parameter completion rate
                        individual_completion_rate = (
                                    individual_aktuell / individual_proben * 100) if individual_proben > 0 else 0

                        # Determine parameter status
                        param_status = 'complete' if individual_completion_rate >= 100 else 'incomplete' if individual_completion_rate > 0 else 'not_started'

                        print(f"\n=== DEBUG: Processing parameter {param} ===")
                        print(f"Row columns containing 'Datum': {[col for col in row.index if 'atum' in str(col)]}")
                        for col in row.index:
                            if 'atum' in str(col).lower():
                                print(f"  {col}: {row[col]} (type: {type(row[col])})")

                        # Get the latest date
                        latest_date = extract_latest_date(row)
                        print(f"Extracted latest date: {latest_date}")

                        # Each parameter gets its own separate entry with individual sample tracking
                        parameter_detail = {
                            'parameter': param,
                            'category': category,
                            'frequency': frequency,
                            'type': type_display,  # For display in popup: 'Internal' or 'External'
                            'type_filter': type_filter,  # For filtering: 'I' or 'E'
                            'zapfstelle': zapfstelle_row,
                            'current': individual_aktuell,  # Individual parameter current samples
                            'total': individual_proben,  # Individual parameter total samples
                            'completion_rate': individual_completion_rate,
                            'status': param_status,
                            # Additional metadata
                            'is_complete': individual_completion_rate >= 100,
                            'samples_remaining': max(0, individual_proben - individual_aktuell),
                            'has_samples': individual_proben > 0,
                            'progress_text': f"{individual_aktuell}/{individual_proben}",
                            'latest_date': extract_latest_date(row)
                        }

                        parameter_details.append(parameter_detail)

                        # Collect for summary (backward compatibility)
                        all_parameters.append(param)
                        all_frequencies.append(frequency)
                        all_pn_types.append(pn_type_raw)  # Keep original for summary
                        all_categories.append(category)

                # Handle zero sample case
                if is_zero_sample and not parameter_details:
                    # Create a minimal parameter_details entry for zero sample points
                    bereich = safe_str_convert(group["Bereich"].iloc[0] if "Bereich" in group.columns else "Unknown")
                    parameter_details.append({
                        'parameter': 'No Parameters',
                        'category': bereich,
                        'frequency': 'N/A',
                        'type': 'Unknown',
                        'type_filter': 'Unknown',
                        'zapfstelle': zapfstelle,
                        'current': 0,
                        'total': 0,
                        'completion_rate': 0,
                        'status': 'zero_sample',
                        'is_complete': False,
                        'samples_remaining': 0,
                        'has_samples': False,
                        'progress_text': '0/0'
                    })

                # For backward compatibility - create summary strings
                parameter = ', '.join(list(dict.fromkeys(all_parameters))) if all_parameters else "Unknown"
                häufigkeit = ', '.join(list(dict.fromkeys(all_frequencies))) if all_frequencies else "Unknown"
                pn_type = ', '.join(list(dict.fromkeys(all_pn_types))) if all_pn_types else "Unknown"
                bereich = all_categories[0] if all_categories else "Unknown"  # Use first category for map color

                # Create label
                messstelle_clean = safe_str_convert(messstelle)
                zapfstelle_clean = safe_str_convert(zapfstelle)
                kunde_clean = kunde

                if zapfstelle_clean and zapfstelle_clean != "Not Specified":
                    label = f"{kunde_clean} - {zapfstelle_clean} - {messstelle_clean}"
                else:
                    label = f"{kunde_clean} - {messstelle_clean}"

                # Calculate statistics for different parameter types
                internal_params = [p for p in parameter_details if p['type_filter'] == 'I']
                external_params = [p for p in parameter_details if p['type_filter'] == 'E']

                # Calculate parameter-level statistics
                completed_params = [p for p in parameter_details if p['is_complete']]
                in_progress_params = [p for p in parameter_details if not p['is_complete'] and p['current'] > 0]
                not_started_params = [p for p in parameter_details if p['current'] == 0]

                # Create item data with enhanced parameter details
                item_data = {
                    'lat': lat,
                    'lon': lon,
                    'label': label,
                    'messstelle': messstelle_clean,
                    'zapfstelle': zapfstelle_clean,
                    'bereich': bereich,
                    'kunde': kunde,
                    'parameter': parameter,  # Summary for backward compatibility
                    'häufigkeit': häufigkeit,  # Summary for backward compatibility
                    'pn_type': pn_type,  # Summary for backward compatibility
                    'vollständig': vollständig,
                    'total_samples': total_proben,
                    'completed_samples': total_aktuell,
                    'completion_rate': (total_aktuell / total_proben * 100) if total_proben > 0 else 0,
                    'parameter_details': parameter_details,  # ENHANCED: Each parameter with individual samples
                    'details': parameter_details,
                    'is_zero_sample': is_zero_sample,
                    'parameter_count': len(parameter_details),
                    'all_parameters': all_parameters,
                    'all_frequencies': all_frequencies,
                    'all_categories': all_categories,
                    # ENHANCED: Separate arrays for filtering with individual sample data
                    'internal_parameters': internal_params,
                    'external_parameters': external_params,
                    # ENHANCED: Parameter status statistics
                    'completed_parameter_count': len(completed_params),
                    'in_progress_parameter_count': len(in_progress_params),
                    'not_started_parameter_count': len(not_started_params),
                    'parameter_completion_percentage': len(completed_params) / len(
                        parameter_details) * 100 if parameter_details else 0,
                }

                # Handle coordinate clustering
                if coord_key not in coordinate_clusters:
                    coordinate_clusters[coord_key] = []
                coordinate_clusters[coord_key].append(item_data)

                processed_data.append(item_data)

                if i < 3:  # Show details for first 3 groups
                    zero_indicator = " (ZERO SAMPLE)" if is_zero_sample else ""
                    param_count_info = f" ({len(parameter_details)} parameters)"
                    internal_count = len(internal_params)
                    external_count = len(external_params)
                    completed_count = len(completed_params)
                    pn_info = f" [I:{internal_count}, E:{external_count}, Complete:{completed_count}]"
                    print(
                        f"   ✅ Group {i + 1}: {messstelle} at {lat}, {lon}{param_count_info}{pn_info}{zero_indicator}")

                    # Show individual parameters with their progress
                    for j, param_detail in enumerate(parameter_details[:3]):
                        type_info = f"[{param_detail['type_filter']}]"
                        progress_info = f"{param_detail['current']}/{param_detail['total']} ({param_detail['completion_rate']:.0f}%)"
                        status_icon = "✅" if param_detail['is_complete'] else "🔄" if param_detail[
                                                                                         'current'] > 0 else "❌"
                        print(
                            f"      - {status_icon} {param_detail['parameter']} {type_info} | {progress_info} | {param_detail['frequency']}")

            except Exception as e:
                print(f"   ❌ Group {i + 1}: Error - {str(e)}")
                skipped_count += 1
                continue

        # Mark clustered items
        for coord_key, items in coordinate_clusters.items():
            if len(items) > 1:
                for i, item in enumerate(items):
                    item['is_clustered'] = True
                    item['cluster_size'] = len(items)
                    item['cluster_index'] = i
                    # Slightly offset coordinates to make markers visible
                    offset = 0.0001 * i
                    item['lat'] += offset
                    item['lon'] += offset
            else:
                items[0]['is_clustered'] = False
                items[0]['cluster_size'] = 1
                items[0]['cluster_index'] = 0

        # Calculate enhanced statistics
        total_internal_params = sum(len(item['internal_parameters']) for item in processed_data)
        total_external_params = sum(len(item['external_parameters']) for item in processed_data)
        total_completed_params = sum(item['completed_parameter_count'] for item in processed_data)
        total_in_progress_params = sum(item['in_progress_parameter_count'] for item in processed_data)
        total_not_started_params = sum(item['not_started_parameter_count'] for item in processed_data)
        total_parameters = sum(item['parameter_count'] for item in processed_data)

        print(f"\n📊 ENHANCED PROCESSING COMPLETE:")
        print(f"   ✅ Successfully processed: {len(processed_data)} points")
        print(f"   📍 Zero sample points: {zero_sample_count}")
        print(f"   🏢 Internal parameters: {total_internal_params}")
        print(f"   🌐 External parameters: {total_external_params}")
        print(f"   ✅ Completed parameters: {total_completed_params}")
        print(f"   🔄 In-progress parameters: {total_in_progress_params}")
        print(f"   ❌ Not started parameters: {total_not_started_params}")
        print(f"   📊 Total parameters: {total_parameters}")
        print(f"   ⚠️  Skipped: {skipped_count} groups")

        DEBUG_INFO['processed_points'] = len(processed_data)
        DEBUG_INFO['zero_sample_points'] = zero_sample_count
        DEBUG_INFO['internal_parameters'] = total_internal_params
        DEBUG_INFO['external_parameters'] = total_external_params
        DEBUG_INFO['completed_parameters'] = total_completed_params
        DEBUG_INFO['in_progress_parameters'] = total_in_progress_params
        DEBUG_INFO['not_started_parameters'] = total_not_started_params
        DEBUG_INFO['total_parameters'] = total_parameters
        DEBUG_INFO['skipped_points'] = skipped_count

        if len(processed_data) == 0:
            error_msg = f"No valid map points found. Skipped {skipped_count} groups due to invalid coordinates."
            LAST_ERROR = error_msg
            return None, error_msg

        LAST_ERROR = None
        return processed_data, None

    except Exception as e:
        error_msg = f"Error processing file for map: {str(e)}"
        LAST_ERROR = error_msg
        DEBUG_INFO['processing_error'] = error_msg
        DEBUG_INFO['processing_traceback'] = traceback.format_exc()
        print(f"❌ PROCESSING ERROR: {error_msg}")
        print(f"📋 Full traceback:\n{traceback.format_exc()}")
        return None, error_msg


# Enhanced debug endpoint with individual parameter statistics
@app.route('/debug')
def debug_info():
    """Enhanced debug endpoint with individual parameter statistics"""
    global MAP_DATA, DEBUG_INFO, LAST_ERROR

    try:
        # Enhanced debug data with individual parameter analysis
        debug_data = {
            'map_data_count': len(MAP_DATA) if MAP_DATA else 0,
            'debug_info': clean_for_json(DEBUG_INFO),
            'last_error': LAST_ERROR,
            'sample_data': clean_for_json(MAP_DATA[:3] if MAP_DATA else [])
        }

        # Add individual parameter analysis
        if MAP_DATA:
            all_parameters = []
            parameter_stats = {}
            type_stats = {'Internal': 0, 'External': 0}
            status_stats = {'complete': 0, 'in_progress': 0, 'not_started': 0}

            for item in MAP_DATA:
                if item.get('parameter_details'):
                    for param in item['parameter_details']:
                        all_parameters.append(param)

                        # Count by type
                        param_type = param.get('type', 'Unknown')
                        if param_type in type_stats:
                            type_stats[param_type] += 1

                        # Count by status
                        status = param.get('status', 'unknown')
                        if status in status_stats:
                            status_stats[status] += 1

                        # Individual parameter statistics
                        param_name = param.get('parameter', 'Unknown')
                        if param_name not in parameter_stats:
                            parameter_stats[param_name] = {
                                'count': 0,
                                'total_samples': 0,
                                'completed_samples': 0,
                                'internal_count': 0,
                                'external_count': 0
                            }

                        parameter_stats[param_name]['count'] += 1
                        parameter_stats[param_name]['total_samples'] += param.get('total', 0)
                        parameter_stats[param_name]['completed_samples'] += param.get('current', 0)

                        if param_type == 'Internal':
                            parameter_stats[param_name]['internal_count'] += 1
                        elif param_type == 'External':
                            parameter_stats[param_name]['external_count'] += 1

            debug_data['individual_parameter_analysis'] = {
                'total_individual_parameters': len(all_parameters),
                'unique_parameter_names': len(parameter_stats),
                'type_distribution': type_stats,
                'status_distribution': status_stats,
                'top_parameters': dict(
                    list(sorted(parameter_stats.items(), key=lambda x: x[1]['count'], reverse=True))[:10]),
                'parameter_completion_rates': {
                    name: {
                        'completion_rate': (stats['completed_samples'] / stats['total_samples'] * 100) if stats[
                                                                                                              'total_samples'] > 0 else 0,
                        'progress_text': f"{stats['completed_samples']}/{stats['total_samples']}"
                    }
                    for name, stats in parameter_stats.items()
                }
            }

        return flask.jsonify(debug_data)
    except Exception as e:
        return flask.jsonify({
            'error': f"Enhanced debug endpoint error: {str(e)}",
            'traceback': traceback.format_exc()
        }), 500


@app.route('/')
def map_view():
    """Main map page with file upload and enhanced debug info"""
    global MAP_DATA, DEBUG_INFO, LAST_ERROR

    # FIXED: Prepare data for JavaScript with proper parameter_details structure
    if MAP_DATA:
        markers_data = []
        for item in MAP_DATA:
            # FIXED: Ensure parameter_details are properly structured for JavaScript
            processed_parameter_details = []
            if item.get('parameter_details'):
                for param in item['parameter_details']:
                    processed_parameter_details.append({
                        'parameter': param.get('parameter', 'Unknown'),
                        'category': param.get('category', 'Unknown'),
                        'frequency': param.get('frequency', 'Unknown'),
                        'type': param.get('type', 'Unknown'),  # 'Internal' or 'External'
                        'type_filter': param.get('type_filter', param.get('type', 'Unknown')),  # 'I' or 'E'
                        'zapfstelle': param.get('zapfstelle', 'Unknown'),
                        'current': param.get('current', 0),
                        'total': param.get('total', 0),
                        'completion_rate': param.get('completion_rate', 0),
                        'status': param.get('status', 'unknown'),
                        'is_complete': param.get('is_complete', False),
                        'samples_remaining': param.get('samples_remaining', 0),
                        'has_samples': param.get('has_samples', False),
                        'progress_text': param.get('progress_text', '0/0')
                    })

            marker_data = {
                'coordinates': [item['lat'], item['lon']],
                'category': item['bereich'],
                'label': item['label'],
                'complete': item['vollständig'],
                'kunde': item['kunde'],
                'parameter': item['parameter'],
                'häufigkeit': item['häufigkeit'],
                'pn_type': item['pn_type'],
                'completion_rate': item['completion_rate'],
                'total_samples': item['total_samples'],
                'completed_samples': item['completed_samples'],
                'details': processed_parameter_details,  # Use processed details
                'parameter_details': processed_parameter_details,  # FIXED: Include parameter_details
                'is_clustered': item.get('is_clustered', False),
                'cluster_size': item.get('cluster_size', 1),
                'cluster_index': item.get('cluster_index', 0),
                'is_zero_sample': item.get('is_zero_sample', False),
                'messstelle': item.get('messstelle', item['label']),
                'zapfstelle': item.get('zapfstelle', 'Not Specified')
            }
            markers_data.append(marker_data)
    else:
        markers_data = []

    # Enhanced debug info with zero sample statistics
    enhanced_debug_info = DEBUG_INFO.copy()
    if MAP_DATA:
        zero_samples = sum(1 for item in MAP_DATA if item.get('is_zero_sample', False))
        enhanced_debug_info['zero_sample_statistics'] = {
            'total_zero_samples': zero_samples,
            'percentage': f"{(zero_samples / len(MAP_DATA) * 100):.1f}%" if MAP_DATA else "0%"
        }

    # Use Flask's render_template to load from file
    try:
        return flask.render_template('map.html',
                                     markers_data=json.dumps(markers_data),
                                     category_colors=json.dumps(CATEGORY_COLORS),
                                     dashboard_url=DASHBOARD_APP_URL,
                                     has_data=len(markers_data) > 0,
                                     data_count=len(markers_data),
                                     debug_info=enhanced_debug_info,
                                     last_error=LAST_ERROR,
                                     timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    except Exception as e:
        # Fallback to inline template if file doesn't exist
        print(f"Template file not found, using enhanced inline template: {e}")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Enhanced Map - Template Error</title>
        </head>
        <body>
            <h1>Enhanced Template Error</h1>
            <p>The template file 'templates/map.html' was not found.</p>
            <p>Please create the templates directory and use the enhanced template.</p>
            <p>Error: {e}</p>
            <p>Debug Info: {enhanced_debug_info}</p>
        </body>
        </html>
        """


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload with enhanced debugging and zero sample detection"""
    global MAP_DATA, LAST_ERROR

    try:
        print(f"\n🔄 ENHANCED UPLOAD REQUEST RECEIVED")

        if 'file' not in flask.request.files:
            return flask.jsonify({'success': False, 'error': 'No file provided'}), 400

        file = flask.request.files['file']
        if file.filename == '':
            return flask.jsonify({'success': False, 'error': 'No file selected'}), 400

        print(f"📁 File: {file.filename}")

        if file and file.filename.lower().endswith(('.xlsx', '.xls')):
            # Save file temporarily
            temp_path = f"temp_{file.filename}"
            file.save(temp_path)
            print(f"💾 File saved to: {temp_path}")

            # Process the file with enhanced zero sample detection
            MAP_DATA, error = parse_excel_data_for_map(temp_path)

            # Clean up temp file
            try:
                os.remove(temp_path)
                print(f"🗑️  Temp file removed")
            except:
                pass

            if error:
                return flask.jsonify({
                    'success': False,
                    'error': error,
                    'debug_info': DEBUG_INFO
                }), 400

            # Enhanced success response with zero sample info
            zero_sample_count = DEBUG_INFO.get('zero_sample_points', 0)
            success_message = f'Successfully loaded {len(MAP_DATA)} map points'
            if zero_sample_count > 0:
                success_message += f' (including {zero_sample_count} zero sample points)'

            return flask.jsonify({
                'success': True,
                'message': success_message,
                'debug_info': {
                    'points_loaded': len(MAP_DATA),
                    'zero_sample_points': zero_sample_count,
                    'processing_details': DEBUG_INFO
                },
                'redirect': '/'
            })
        else:
            return flask.jsonify({'success': False, 'error': 'Please upload an Excel file (.xlsx or .xls)'}), 400

    except Exception as e:
        error_msg = f"Enhanced upload error: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        return flask.jsonify({
            'success': False,
            'error': error_msg,
            'traceback': traceback.format_exc()
        }), 500


def clean_for_json(obj):
    """Clean data for JSON serialization - FIXED for pandas compatibility"""
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(item) for item in obj]
    elif pd.isna(obj):
        return None
    elif isinstance(obj, pd.Timestamp):
        return str(obj)
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        return float(obj)
    elif hasattr(obj, 'item'):  # numpy scalar
        try:
            return obj.item()
        except:
            return str(obj)
    else:
        return obj


# @app.route('/debug')
# def debug_info():
#     """Enhanced debug endpoint with zero sample statistics"""
#     global MAP_DATA, DEBUG_INFO, LAST_ERROR
#
#     try:
#         # Enhanced debug data with zero sample analysis
#         debug_data = {
#             'map_data_count': len(MAP_DATA) if MAP_DATA else 0,
#             'debug_info': clean_for_json(DEBUG_INFO),
#             'last_error': LAST_ERROR,
#             'sample_data': clean_for_json(MAP_DATA[:3] if MAP_DATA else [])
#         }
#
#         # Add zero sample analysis
#         if MAP_DATA:
#             zero_samples = [item for item in MAP_DATA if item.get('is_zero_sample', False)]
#             debug_data['zero_sample_analysis'] = {
#                 'count': len(zero_samples),
#                 'percentage': f"{(len(zero_samples) / len(MAP_DATA) * 100):.1f}%",
#                 'examples': clean_for_json(zero_samples[:3])
#             }
#
#         return flask.jsonify(debug_data)
#     except Exception as e:
#         return flask.jsonify({
#             'error': f"Enhanced debug endpoint error: {str(e)}",
#             'traceback': traceback.format_exc()
#         }), 500


if __name__ == '__main__':
    print("=" * 70)
    print("🗺️ STARTING ENHANCED MAP APPLICATION WITH ZERO SAMPLE FILTERING")
    print("=" * 70)
    print(f"Map URL: http://127.0.0.1:5002")
    print(f"Debug endpoint: http://127.0.0.1:5002/debug")
    print(f"Dashboard URL: {DASHBOARD_APP_URL}")
    print("Enhanced Features:")
    print("  - Zero sample point detection and filtering")
    print("  - Enhanced search functionality in filters")
    print("  - Improved filter controls with select/clear all")
    print("  - Compact clear all button")
    print("=" * 70)
    app.run(debug=True, host='127.0.0.1', port=5002)