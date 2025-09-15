# utils/data_processor.py

import pandas as pd
import base64
import io
import re
from config.constants import KW_RANGES, PARAMETER_GROUPS


def format_date_to_ddmmyyyy(date_str):
    """Helper to safely format dates from Timestamp or strings"""
    if pd.isna(date_str):
        return ""

    try:
        parsed_date = pd.to_datetime(date_str, dayfirst=True, errors='coerce')
        if not pd.isna(parsed_date):
            return parsed_date.strftime("%d.%m.%Y")
        else:
            return str(date_str)  # if parsing fails, return as string
    except:
        return str(date_str)


def get_parameter_group(parameter_name):
    """Find which group a parameter belongs to"""
    for group_name, parameters in PARAMETER_GROUPS.items():
        if parameter_name in parameters:
            return group_name
    return "Sonstige"  # Default group for unmatched parameters


def should_split_customer(kunde_dict):
    """Check if a customer should be split into parameter groups"""
    kunde_name = kunde_dict["Kunde"]

    # Only split "TWM GmbH" company specifically
    companies_to_split = ["TWM GmbH"]

    return kunde_name in companies_to_split


def split_customer_by_parameter_groups(kunde_dict):
    """Split a customer into multiple groups based on parameter categories"""
    kunde_name = kunde_dict["Kunde"]

    if not should_split_customer(kunde_dict):
        return [kunde_dict]  # Return as-is if no splitting needed

    # Create separate customer groups
    grouped_customers = {}

    for row in kunde_dict["Rows"]:
        # Group parameters in this row by their categories
        grouped_params = {}

        for param_name, param_data in row.items():
            if param_name in ["Messstelle", "Zapfstelle"]:
                continue

            group_name = get_parameter_group(param_name)

            if group_name not in grouped_params:
                grouped_params[group_name] = {}

            grouped_params[group_name][param_name] = param_data

        # Create separate rows for each parameter group
        for group_name, params in grouped_params.items():
            if not params:  # Skip empty groups
                continue

            customer_group_name = f"{kunde_name} ({group_name})"

            if customer_group_name not in grouped_customers:
                grouped_customers[customer_group_name] = {
                    "Kunde": customer_group_name,
                    "Rows": []
                }

            # Create a new row for this group
            new_row = {
                "Messstelle": row["Messstelle"],
                "Zapfstelle": row["Zapfstelle"]
            }
            new_row.update(params)

            grouped_customers[customer_group_name]["Rows"].append(new_row)

    return list(grouped_customers.values())


def transform_data(contents):
    """Transform uploaded Excel data into structured format"""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    data = pd.read_excel(io.BytesIO(decoded))

    transformed_data = []
    for kunde, kunde_group in data.groupby('Kunde'):
        kunde_dict = {"Kunde": kunde, "Rows": []}
        for messstelle, messstelle_group in kunde_group.groupby('Messstelle'):
            for zapfstelle, zapfstelle_group in messstelle_group.groupby('Zapfstelle', dropna=False):

                row_dict = {"Messstelle": messstelle, "Zapfstelle": zapfstelle}
                parameters_dict = {}
                for _, row in zapfstelle_group.iterrows():

                    # Skip rows where both Proben Gesamt and Häufigkeit are empty
                    proben_val = row.get("Proben\nGesamt")
                    freq_val = row.get("Häufigkeit")

                    if (pd.isna(proben_val) or str(proben_val).strip() == "") and \
                            (pd.isna(freq_val) or str(freq_val).strip() == ""):
                        continue

                    # Skip if Parameter is NaN, empty or invalid
                    parameter = str(row.get("Parameter", "")).strip()
                    if not parameter or parameter.lower() in ["nan", "none", ""]:
                        continue

                    try:
                        proben_gesamt = int(row.get("Proben\nGesamt", 0)) if not pd.isna(
                            row.get("Proben\nGesamt")) else 0
                    except:
                        proben_gesamt = 0

                    aktuell_col_name = next(
                        (col for col in row.index if isinstance(col, str) and "Aktuell" in col and "Gesamt" in col),
                        None)
                    aktuell_gesamt_val = row.get(aktuell_col_name, 0) if aktuell_col_name else 0

                    try:
                        completed_samples = int(aktuell_gesamt_val) if not pd.isna(aktuell_gesamt_val) else 0
                    except (ValueError, TypeError):
                        match = re.search(r'\d+', str(aktuell_gesamt_val))
                        completed_samples = int(match.group()) if match else 0

                    pn_type = str(row.get("PN (I/E)", "")).strip()
                    haeufigkeit = str(row.get("Häufigkeit", "")).strip()

                    if parameter not in parameters_dict:
                        parameters_dict[parameter] = {
                            "proben_gesamt": proben_gesamt,
                            "completed": completed_samples,
                            "pn_type": pn_type,
                            "haeufigkeit": haeufigkeit,
                            "month_data": {}
                        }

                    exclude_months = set()
                    for col in row.index:
                        if isinstance(col, str) and "KW" in col:
                            month_match = re.search(r'(Jan|Feb|Mrz|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez)', col)
                            if month_match:
                                month = month_match.group(1)
                                val = row[col]

                                # Only exclude month if KW is 0 *and* Ist and Datum are also empty
                                ist_col = next((c for c in row.index if f"{month}" in c and "Ist" in c), None)
                                datum_col = next((c for c in row.index if f"{month}" in c and "Datum" in c), None)

                                ist_val = row.get(ist_col, "") if ist_col else ""
                                datum_val = row.get(datum_col, "") if datum_col else ""

                                no_sample_info = (
                                        (pd.isna(ist_val) or str(ist_val).strip() == "")
                                        and (pd.isna(datum_val) or str(datum_val).strip() == "")
                                )

                                if (pd.isna(val) or (isinstance(val, (int, float)) and val == 0)) and no_sample_info:
                                    exclude_months.add(month)

                    for col in row.index:
                        if not isinstance(col, str):
                            continue
                        month_match = re.search(r'(Jan|Feb|Mrz|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez)', col)
                        if month_match:
                            month = month_match.group(1)
                            if month in exclude_months:
                                continue
                            value = row[col]
                            if pd.isna(value):
                                continue

                            col_type = ""
                            if "KW" in col:
                                col_type = "KW"
                            elif "Ist" in col:
                                col_type = "Ist"
                            elif "Datum" in col:
                                col_type = "Datum"

                            if month not in parameters_dict[parameter]["month_data"]:
                                parameters_dict[parameter]["month_data"][month] = {
                                    "value": None,
                                    "col_type": {}
                                }

                            parameters_dict[parameter]["month_data"][month]["col_type"][col_type] = value
                            if col_type == "Ist":
                                parameters_dict[parameter]["month_data"][month]["value"] = value

                # Only include the row if there are valid parameters
                valid_parameters = {}

                for parameter, param_data in parameters_dict.items():
                    # Skip parameters with total=0 and completed=0
                    if param_data["proben_gesamt"] == 0 and param_data["completed"] == 0:
                        continue

                    valid_parameters[parameter] = {
                        "proben_gesamt": param_data["proben_gesamt"],
                        "completed": param_data["completed"],
                        "pn_type": param_data["pn_type"],
                        "haeufigkeit": param_data["haeufigkeit"],
                        "remaining": max(0, param_data["proben_gesamt"] - param_data["completed"]),
                        "month_data": param_data["month_data"]
                    }

                # Only append row if there are valid parameters
                if valid_parameters:
                    row_dict.update(valid_parameters)
                    kunde_dict["Rows"].append(row_dict)

        # After processing all rows for this customer, check if it should be split
        split_customers = split_customer_by_parameter_groups(kunde_dict)
        transformed_data.extend(split_customers)

    return transformed_data