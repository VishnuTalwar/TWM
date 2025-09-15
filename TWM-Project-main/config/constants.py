# config/constants.py

# Defining KW ranges per month
KW_RANGES = {
    "Jan": "KW: 1-5",
    "Feb": "KW: 5-9",
    "Mrz": "KW: 9-13",
    "Apr": "KW: 14-17",
    "Mai": "KW: 18-22",
    "Jun": "KW: 23-26",
    "Jul": "KW: 27-31",
    "Aug": "KW: 32-35",
    "Sep": "KW: 36-39",
    "Okt": "KW: 40-44",
    "Nov": "KW: 45-48",
    "Dez": "KW: 49-52",
}

# Color schemes for different states
COLORS = {
    'completed': {
        'bg': '#d4edda',
        'text': '#155724',
        'border': '#c3e6cb'
    },
    'excess': {
        'bg': '#1F7D53',
        'text': '#ffffff',
        'border': '#186446'
    },
    'missing_internal': {
        'bg': '#f8d7da',
        'text': '#721c24',
        'border': '#f5c6cb'
    },
    'missing_external': {
        'bg': '#e6e6fa',
        'text': '#6a0dad',
        'border': '#d8bfd8'
    },
    'progress_complete': '#28a745',
    'progress_incomplete': '#ffc107',
    'header_bg': '#2980b9'
}

# Quarters and half-years definitions
QUARTERS = [
    {"name": "Jan - Mrz", "months": ["Jan", "Feb", "Mrz"]},
    {"name": "Apr - Jun", "months": ["Apr", "Mai", "Jun"]},
    {"name": "Jul - Sep", "months": ["Jul", "Aug", "Sep"]},
    {"name": "Okt - Dez", "months": ["Okt", "Nov", "Dez"]}
]

HALFYEARS = [
    {"name": "Jan - Jun", "months": ["Jan", "Feb", "Mrz", "Apr", "Mai", "Jun"]},
    {"name": "Jul - Dez", "months": ["Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]}
]

# Parameter groups for splitting customers into categories
PARAMETER_GROUPS = {
    "Grundwasser Pegel": [
        "Grundwasser Pegel (SMP 1)",
        "Grundwasser Pegel (SMP 2)",
        "Grundwasser Pegel (SMP 5) PBSM",
        "Grundwasser Pegel (SMP 6)",
        "Grundwassermeßprogramm Pegel (GMP/EMP 1)",
        "Grundwassermeßprogramm Pegel (GMP/EMP 1 + SMP 1)",
        "Grundwassermeßprogramm Pegel (GMP/EMP 1 + SMP 1 + SMP 5)",
        "Grundwassermeßprogramm Pegel (GMP/EMP 1 + SMP 1 + SMP 6)",
        "Grundwassermeßprogramm Pegel (GMP/EMP 1+ SMP 5)",
        "Grundwassermeßprogramm Pegel (GMP/EMP 1+ SMP 5 + SMP 6)",
        "Grundwassermeßprogramm Pegel (GMP+EMP 1+EMP 3)",
        "Grundwassermeßprogramm Pegel (GMP+EMP 1+EMP 3+SMP6)"
    ],
    "Grundwasser Brunnen": [
        "Grundwasser (SMP 1)",
        "Grundwasser (SMP 1) + DIN 50930+Fe/Mn",
        "Grundwasser (SMP 1 + SMP 5) ohne vor Ort-Messung",
        "Grundwasser (SMP 1) ohne vor Ort-Messung",
        "Grundwasser (SMP 2)",
        "Grundwasser (SMP 2) ohne vor Ort Messung",
        "Grundwasser (SMP 5) PBSM",
        "Grundwasser (SMP 5) PBSM ohne vor Ort Messung",
        "Grundwasser (SMP 6)",
        "Grundwasser (SMP 7)",
        "Grundwassermeßprogramm (GMP)",
        "GrundwassermeBprogramm (GMP)+Bak",
        "Grundwassermeßprogramm (GMP/EMP 1)",
        "Grundwassermeßprogramm (GMP/EMP 1 + SMP 1)",
        "Grundwassermeßprogramm (GMP/EMP 1 + SMP 1 + SMP 5)",
        "Grundwassermeßprogramm (GMP/EMP 1 + SMP 1 + SMP 5 + SMP 6)",
        "Grundwassermeßprogramm (GMP/EMP 1 + SMP 1 + SMP 6)",
        "Grundwassermeßprogramm (GMP/EMP 1+ SMP 5)",
        "Grundwassermeßprogramm (GMP+EMP 1+EMP 3)",
        "Grundwassermeßprogramm (GMP+EMP 1+EMP 3+SMP 4)",
        "Grundwassermeßprogramm (GMP+EMP 1+EMP 3+SMP 6)"
    ],
    "Filterrückspülwässer": [
        "abfiltrierbare Stoffe, pH Filterrückspülw.SAS+AOX+As",
        "Filterrückspülw. Temp/pH",
        "Klarwasser emin.",
        "Sonderunters. Klarw.v. Filterrückspülw. (SAS)",
        "Sonderunters. Klarw.v. Filterrückspülw. (SAS)+Alu",
        "Sonderunters. Klarw. v. Filterrückspülw. (SAS+AOX)",
        "Trubung"
    ],
    "Parametergruppe A": [
        "Parametergruppe A TWN",
        "Parametergruppe A TWN (mit Al, Clos)",
        "Parametergruppe A WW-Ausg-",
        "Parametergruppe A WW-Ausg- (mit Al,Clos)",
        "Parametergruppe A WW-Ausg- (mit Al,Clos+GH)",
        "Parametergruppe A WW-Ausg.+GH",
        "Bakteriologie/Temp. (TrinkwV)",
        "Clostridium perfringens"
    ],
    "Parametergruppe B": [
        "Parametergruppe B (mit THM)",
        "Parametergruppe B (ohne THM)",
        "Sonst de Unters. nach DiM90430",
        "LHKW + BTEX"
    ]
}