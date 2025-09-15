



https://github.com/user-attachments/assets/a80954c1-cbc4-4e4c-a9b7-545aaae747fb





https://github.com/user-attachments/assets/8aa8ad86-bd82-4f17-adda-66381c9eeff8


# Probenplanung - Sample Planning Dashboard & Map

A comprehensive web application for managing and visualizing water quality sample planning data with interactive dashboards and geographic mapping capabilities.

## 🌟 Features

### 📊 Dashboard Application
- **Interactive Sample Tracking**: Visual progress bars for each parameter and location
- **Customer Management**: Organized view by customer with parameter grouping
- **Progress Monitoring**: Real-time tracking of completed vs. required samples
- **Monthly Calendar View**: Detailed month-by-month sample scheduling
- **Legend & Status Indicators**: Clear visual indicators for sample states

### 🗺️ Map Application
- **Geographic Visualization**: Interactive map showing all measurement points (Messstelle)
- **Advanced Filtering**: Multi-level filtering by customer, parameter, category, frequency, and PN type
- **Search Functionality**: Quick search and navigation to specific measurement points
- **Zoom-based Labels**: Automatic display of Messstelle names at high zoom levels
- **Real-time Updates**: Dynamic marker updates based on filter selections
- **Popup Details**: Comprehensive information panels for each location

### 🔧 Technical Features
- **Dual Application Architecture**: Separate dashboard and map applications
- **Excel File Upload**: Direct upload and processing of .xlsx/.xls files
- **Real-time Data Processing**: Automatic transformation of Excel data
- **Performance Optimized**: Efficient rendering for large datasets
- **Responsive Design**: Mobile-friendly interface
- **Caching System**: Improved performance with intelligent caching

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Required Python packages (see Installation)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd TWM-Project-main
   ```

2. **Install dependencies**
   ```bash
   pip install dash pandas openpyxl flask leaflet plotly
   ```

3. **Start both applications**
   ```bash
   python start_apps.py
   ```

   Or start individually:
   ```bash
   # Dashboard only
   python dashboard_app.py

   # Map only
   python map_app.py
   ```

4. **Access the applications**
   - Dashboard: http://127.0.0.1:8050
   - Map: http://127.0.0.1:5002

## 📁 Project Structure

```
TWM-Project-main/
├── assets/
│   └── styles.css              # Main application styles
├── config/
│   ├── __init__.py
│   └── constants.py            # Configuration constants
├── static/
│   ├── css/
│   │   └── map-styles.css      # Map-specific styles
│   └── js/
│       ├── map-main.js         # Main map functionality
│       ├── map-filters.js      # Advanced filter system
│       ├── map-markers.js      # Marker management
│       └── map-utils.js        # Utility functions
├── templates/
│   └── map.html                # Map application template
├── utils/
│   ├── __init__.py
│   ├── data_processor.py       # Excel data processing
│   ├── display_handlers.py     # UI display logic
│   └── ui_components.py        # Reusable UI components
├── dashboard_app.py            # Dashboard application
├── dashboard_module.py         # Dashboard logic
├── map_app.py                  # Map application
├── map_module.py               # Map logic
└── start_apps.py               # Dual application launcher
```

## 📋 Data Format

The application expects Excel files with the following columns:

### Required Columns
- **Gebiet**: Geographic coordinates (latitude,longitude)
- **Kunde**: Customer name
- **Messstelle**: Measurement point identifier
- **Zapfstelle**: Sampling point (optional)
- **Bereich**: Category/area classification
- **Parameter**: Parameter name being measured
- **Häufigkeit**: Sampling frequency
- **PN (I/E)**: Internal (I) or External (E) classification
- **Proben\nGesamt**: Total required samples
- **Aktuell\nGesamt**: Currently completed samples

### Monthly Data Columns
For each month (Jan, Feb, Mrz, Apr, Mai, Jun, Jul, Aug, Sep, Okt, Nov, Dez):
- **[Month]\nKW**: Calendar week or day specification
- **[Month]\nIst**: Actual samples taken
- **[Month]\nDatum**: Sample dates

### Example Data Format
```
Gebiet          | Kunde     | Messstelle | Parameter    | Proben\nGesamt | Aktuell\nGesamt
52.3184,11.5678 | TWM GmbH  | MW-001     | Grundwasser  | 12             | 8
```

## 🎯 Usage Guide

### Dashboard Application

1. **Upload Data**: Use the drag & drop area to upload your Excel file
2. **View Progress**: Monitor sample completion progress by customer and parameter
3. **Navigate**: Use the scrollable tables to review all measurement points
4. **Analyze**: Check the legend to understand status indicators

### Map Application

1. **Upload Data**: Upload Excel file using the file input
2. **Filter Data**: Use the advanced filter panel to narrow down display
   - **Customer Filter**: Select specific customers
   - **Parameter Filter**: Filter by measurement parameters
   - **Category Filter**: Choose measurement categories
   - **Frequency Filter**: Filter by sampling frequency
   - **PN Type Filter**: Select Internal/External classifications

3. **Search Locations**: Use the search bar to find specific Messstelle
4. **View Details**: Click on map markers for detailed information
5. **Control Display**:
   - Toggle satellite/street view
   - Show/hide complete/incomplete points
   - Force display of Messstelle labels
   - Filter zero sample points

## ⚙️ Configuration

### Constants Configuration
Edit `config/constants.py` to customize:
- **KW_RANGES**: Calendar week ranges per month
- **COLORS**: Color schemes for different states
- **QUARTERS**: Quarterly groupings
- **HALFYEARS**: Semi-annual groupings
- **PARAMETER_GROUPS**: Parameter categorization

### Map Colors
Customize category colors in `map_app.py`:
```python
CATEGORY_COLORS = {
    "BB": "#e63946",
    "DEA": "#e9ef29",
    # Add more categories...
}
```

## 🔍 Advanced Features

### Filter System
- **Cascading Filters**: Filters update based on previous selections
- **Search Integration**: Real-time search within filter options
- **Connected Filtering**: Synchronized filtering across all data
- **Performance Optimized**: Efficient filtering for large datasets

### Map Features
- **Cluster Management**: Automatic clustering of nearby points
- **Zoom-based Labels**: Labels appear/disappear based on zoom level
- **Performance Monitoring**: Optimized for large datasets
- **Search & Navigation**: Quick location finding and navigation

### Data Processing
- **Automatic Grouping**: Smart parameter grouping for complex customers
- **Date Handling**: Flexible date format processing
- **Validation**: Data validation and error handling
- **Frequency Handling**: Special processing for different sampling frequencies

## 🐛 Troubleshooting

### Common Issues

1. **File Upload Fails**
   - Check file format (.xlsx or .xls)
   - Verify required columns are present
   - Check for data formatting issues

2. **Map Not Loading**
   - Verify geographic coordinates in "Gebiet" column
   - Check coordinate format (latitude,longitude)
   - Ensure coordinates are valid ranges

3. **Performance Issues**
   - Reduce number of visible markers using filters
   - Check browser console for JavaScript errors
   - Consider file size limitations

### Debug Information
Access debug endpoints:
- Dashboard debug: Check console logs
- Map debug: http://127.0.0.1:5002/debug

## 🔧 Development

### Adding New Features

1. **Dashboard Components**: Add to `utils/ui_components.py`
2. **Map Functionality**: Extend JavaScript files in `static/js/`
3. **Data Processing**: Modify `utils/data_processor.py`
4. **Styling**: Update CSS files in `assets/` or `static/css/`

### Code Structure
- **Modular Design**: Separate concerns between dashboard and map
- **Utility Functions**: Reusable components in `utils/`
- **Configuration**: Centralized settings in `config/`
- **Frontend**: Modern JavaScript with performance optimizations

## 📝 License

This project is proprietary software for TWM GmbH water quality sample planning.

## 🤝 Support

For technical support or feature requests, please contact the development team.

---

**Built with ❤️ for efficient water quality sample planning and monitoring.**
