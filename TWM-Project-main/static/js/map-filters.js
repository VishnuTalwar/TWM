// Updated map-filters.js - Enhanced filter management with search functionality

// Global filter state (defined in main.js but managed here)
// window.connectedFilters and window.allFilterOptions are available

/**
 * Initialize connected filters system with performance optimizations
 */
function initializeConnectedFilters() {
    const markersData = window.mapConfig.markersData;

    if (!markersData || markersData.length === 0) {
        console.log('No markers data available for filters');
        return;
    }

    console.log('🔧 Initializing enhanced connected filters');

    // Extract all unique values efficiently using Sets
    extractConnectedFilterOptions();

    // Initialize dropdowns
    updateAllFilterDropdowns();

    // Add event listeners for filter labels
    addConnectedFilterEventListeners();

    // Add search functionality
    addSearchFunctionality();

    console.log('✅ Enhanced connected filters initialized');
}

/**
 * Extract filter options efficiently using Sets
 */
function extractConnectedFilterOptions() {
    const customers = new Set();
    const parameters = new Set();
    const categories = new Set();
    const frequencies = new Set();
    const pnTypes = new Set(['I', 'E']); // Force only I and E

    window.mapConfig.markersData.forEach(function(item) {
        // Customer filter - straightforward
        if (item.kunde && item.kunde !== 'Unknown') {
            customers.add(item.kunde);
        }

        // Category filter - straightforward
        if (item.category) {
            categories.add(item.category);
        }

        // FIXED: Parameter filter - extract individual parameters from parameter_details
        if (item.parameter_details && item.parameter_details.length > 0) {
            item.parameter_details.forEach(function(param) {
                const paramName = param.parameter;
                if (paramName && paramName !== 'Unknown' && paramName.trim() !== '') {
                    parameters.add(paramName.trim());
                }
            });
        } else if (item.parameter && item.parameter !== 'Unknown') {
            // Fallback: if no parameter_details, try to split the concatenated parameter string
            const paramList = item.parameter.split(',').map(p => p.trim()).filter(p => p && p !== 'Unknown');
            paramList.forEach(param => parameters.add(param));
        }

        // FIXED: Frequency filter - extract individual frequencies from parameter_details
        if (item.parameter_details && item.parameter_details.length > 0) {
            item.parameter_details.forEach(function(param) {
                const frequency = param.frequency;
                if (frequency && frequency !== 'Unknown' && frequency.trim() !== '') {
                    frequencies.add(frequency.trim());
                }
            });
        } else if (item.häufigkeit && item.häufigkeit !== 'Unknown') {
            // Fallback: if no parameter_details, try to split the concatenated frequency string
            const freqList = item.häufigkeit.split(',').map(f => f.trim()).filter(f => f && f !== 'Unknown');
            freqList.forEach(freq => frequencies.add(freq));
        }
    });

    window.allFilterOptions.customer = [...customers].sort();
    window.allFilterOptions.parameter = [...parameters].sort();
    window.allFilterOptions.category = [...categories].sort();
    window.allFilterOptions.frequency = [...frequencies].sort();
    window.allFilterOptions.pntype = ['I', 'E']; // Always only I and E

    console.log('📊 FIXED filter options extracted:', {
        customers: window.allFilterOptions.customer.length,
        parameters: window.allFilterOptions.parameter.length,
        categories: window.allFilterOptions.category.length,
        frequencies: window.allFilterOptions.frequency.length,
        pnTypes: window.allFilterOptions.pntype.length
    });
}

/**
 * Add event listeners for enhanced filters
 */
function addConnectedFilterEventListeners() {
    // Add click listeners for filter labels
    document.querySelectorAll('.filter-label').forEach(function(label) {
        label.addEventListener('click', function() {
            const filterType = this.getAttribute('data-filter');
            toggleFilterDropdown(filterType);
        });
    });

    // Click outside to close dropdowns
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.filter-group')) {
            closeAllDropdowns();
        }
    });
}

/**
 * Add search functionality to all filters
 */
function addSearchFunctionality() {
    ['customer', 'parameter', 'category', 'frequency', 'pntype'].forEach(function(filterType) {
        const searchInput = document.getElementById(filterType + '-search');
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                filterDropdownOptions(filterType, this.value);
            });
        }
    });
}

/**
 * Filter dropdown options based on search term
 */
function filterDropdownOptions(filterType, searchTerm) {
    const dropdown = document.getElementById(filterType + '-dropdown');
    if (!dropdown) return;

    const options = dropdown.querySelectorAll('.filter-option:not(.filter-controls)');
    const searchLower = searchTerm.toLowerCase();

    options.forEach(function(option) {
        const text = option.textContent.toLowerCase();
        if (text.includes(searchLower)) {
            option.classList.remove('hidden');
        } else {
            option.classList.add('hidden');
        }
    });
}




function createPnTypeFilterOptions(data) {
    if (!data) {
        return [];
    }

    console.log('🔧 Creating PN type filter options from data:', data.length);

    // Count individual I and E types from parameter details
    let internalCount = 0;
    let externalCount = 0;

    data.forEach(function(item) {
        if (item.parameter_details && item.parameter_details.length > 0) {
            // Count from individual parameter details
            item.parameter_details.forEach(function(param) {
                const paramType = param.type_filter || param.type;
                if (paramType === 'I' || param.type === 'Internal') {
                    internalCount++;
                } else if (paramType === 'E' || param.type === 'External') {
                    externalCount++;
                }
            });
        } else {
            // Fallback: count from main pn_type
            const pnType = item.pn_type || '';
            if (pnType.includes('I')) {
                internalCount++;
            }
            if (pnType.includes('E')) {
                externalCount++;
            }
        }
    });

    const options = [];

    // Always show Internal option if any internal parameters exist
    if (internalCount > 0) {
        options.push({
            label: `Internal (${internalCount})`,
            value: 'I'
        });
    }

    // Always show External option if any external parameters exist
    if (externalCount > 0) {
        options.push({
            label: `External (${externalCount})`,
            value: 'E'
        });
    }

    console.log('✅ Created PN type options:', options, 'Internal:', internalCount, 'External:', externalCount);
    return options;
}







/**
 * Toggle filter dropdown
 */
/**
 * Toggle filter dropdown with proper z-index management
 */
function toggleFilterDropdown(filterType) {
    // Close all other dropdowns first and reset their z-index
    document.querySelectorAll('.filter-dropdown').forEach(function(dropdown) {
        if (dropdown.id !== filterType + '-dropdown') {
            dropdown.classList.remove('show');
        }
    });

    document.querySelectorAll('.filter-label').forEach(function(label) {
        if (label.getAttribute('data-filter') !== filterType) {
            label.classList.remove('active');
        }
    });

    // Reset all filter groups z-index
    document.querySelectorAll('.filter-group').forEach(function(group) {
        group.classList.remove('active');
    });

    // Toggle current dropdown
    const dropdown = document.getElementById(filterType + '-dropdown');
    const label = document.querySelector(`[data-filter="${filterType}"]`);
    const filterGroup = label ? label.closest('.filter-group') : null;

    if (dropdown && label) {
        const isShowing = dropdown.classList.contains('show');

        if (isShowing) {
            dropdown.classList.remove('show');
            label.classList.remove('active');
            if (filterGroup) filterGroup.classList.remove('active');
        } else {
            dropdown.classList.add('show');
            label.classList.add('active');
            if (filterGroup) filterGroup.classList.add('active'); // Add active class for higher z-index
            // Update options when opening
            updateFilterOptions(filterType);
            // Clear search when opening
            const searchInput = document.getElementById(filterType + '-search');
            if (searchInput) {
                searchInput.value = '';
                filterDropdownOptions(filterType, '');
            }
        }
    }
}

/**
 * Close all dropdowns
 */
function closeAllDropdowns() {
    document.querySelectorAll('.filter-dropdown').forEach(function(dropdown) {
        dropdown.classList.remove('show');
    });

    document.querySelectorAll('.filter-label').forEach(function(label) {
        label.classList.remove('active');
    });
}

/**
 * Update filter options
 */
function updateFilterOptions(filterType) {
    const availableOptions = window.allFilterOptions[filterType] || [];
    populateFilterDropdown(filterType, availableOptions);
}

/**
 * Populate filter dropdown with separated selected and available options
 */
function populateFilterDropdown(filterType, options) {
    const dropdown = document.getElementById(filterType + '-dropdown');
    if (!dropdown) return;

    // Clear only the filter options (preserve the search container)
    const existingOptions = dropdown.querySelectorAll('.filter-option, .filter-section-header, .filter-selected-section, .filter-available-section');
    existingOptions.forEach(function(option) {
        option.remove();
    });

    const selectedItems = window.connectedFilters[filterType] || [];

    // FIXED: Handle PN type differently
    if (filterType === 'pntype') {
        const pnTypeOptions = createPnTypeFilterOptions(window.mapConfig.markersData);
        const availableOptions = pnTypeOptions.filter(function(option) {
            return !selectedItems.includes(option.value);
        });

        // Add selected items section if any
        if (selectedItems.length > 0) {
            const selectedHeader = document.createElement('div');
            selectedHeader.className = 'filter-section-header';
            selectedHeader.textContent = `Selected (${selectedItems.length})`;
            dropdown.appendChild(selectedHeader);

            selectedItems.forEach(function(item) {
                const pnOption = pnTypeOptions.find(opt => opt.value === item);
                if (pnOption) {
                    const optionElement = createFilterOption(
                        pnOption.label,
                        function() { toggleFilterOption(filterType, item); },
                        true,
                        filterType
                    );
                    dropdown.appendChild(optionElement);
                }
            });
        }

        // Add available items section if any
        if (availableOptions.length > 0) {
            const availableHeader = document.createElement('div');
            availableHeader.className = 'filter-section-header';
            availableHeader.textContent = `Available (${availableOptions.length})`;
            dropdown.appendChild(availableHeader);

            availableOptions.forEach(function(option) {
                const optionElement = createFilterOption(
                    option.label,
                    function() { toggleFilterOption(filterType, option.value); },
                    false,
                    filterType
                );
                dropdown.appendChild(optionElement);
            });
        }
    } else {
        // Handle regular filters (customer, parameter, category, frequency)
        const availableItems = options.filter(function(option) {
            return !selectedItems.includes(option);
        });

        // Add selected items section if any
        if (selectedItems.length > 0) {
            const selectedHeader = document.createElement('div');
            selectedHeader.className = 'filter-section-header';
            selectedHeader.textContent = `Selected (${selectedItems.length})`;
            dropdown.appendChild(selectedHeader);

            selectedItems.forEach(function(item) {
                const optionElement = createFilterOption(
                    item,
                    function() { toggleFilterOption(filterType, item); },
                    true,
                    filterType
                );
                dropdown.appendChild(optionElement);
            });
        }

        // Add available items section if any
        if (availableItems.length > 0) {
            const availableHeader = document.createElement('div');
            availableHeader.className = 'filter-section-header';
            availableHeader.textContent = `Available (${availableItems.length})`;
            dropdown.appendChild(availableHeader);

            availableItems.forEach(function(option) {
                if (option && option !== 'Unknown') {
                    const optionElement = createFilterOption(
                        option,
                        function() { toggleFilterOption(filterType, option); },
                        false,
                        filterType
                    );
                    dropdown.appendChild(optionElement);
                }
            });
        }
    }

    // Update count
    const totalAvailable = filterType === 'pntype'
        ? createPnTypeFilterOptions(window.mapConfig.markersData).length
        : options.length;
    updateFilterCount(filterType, selectedItems.length, totalAvailable);
}

/**
 * Create filter option element
 */
function createFilterOption(text, clickHandler, isSelected = false, filterType = null) {
    const optionDiv = document.createElement('div');
    optionDiv.className = `filter-option${isSelected ? ' selected' : ''}`;

    // Add special styling for category options
    if (filterType === 'category' && window.mapConfig.categoryColors[text]) {
        const color = window.mapConfig.categoryColors[text];
        const colorSpan = document.createElement('span');
        colorSpan.style.cssText = `
            display: inline-block;
            width: 12px;
            height: 12px;
            background-color: ${color};
            border-radius: 2px;
            margin-right: 8px;
        `;
        optionDiv.appendChild(colorSpan);
        optionDiv.appendChild(document.createTextNode(text));
    } else {
        optionDiv.textContent = text;
    }

    optionDiv.addEventListener('click', clickHandler);
    return optionDiv;
}

/**
 * Debounced filter option toggle for better performance
 */
const debouncedUpdateFilters = debounce(() => {
    updateAllFilterDropdowns();
    if (typeof updateMarkersEnhanced === 'function') {
        updateMarkersEnhanced();
    } else if (typeof updateMarkers === 'function') {
        updateMarkers();
    }
}, 100);

function toggleFilterOption(filterType, option) {
    const index = window.connectedFilters[filterType].indexOf(option);

    if (index > -1) {
        // Remove option
        window.connectedFilters[filterType].splice(index, 1);
    } else {
        // Add option
        window.connectedFilters[filterType].push(option);
    }

    // Update UI with debouncing
    updateFilterOptions(filterType);
    debouncedUpdateFilters();
    updateConnectedFilterSummary();

    console.log('🔄 Filter updated:', filterType, window.connectedFilters[filterType].length, 'selected');
}

/**
 * Select all options for a filter - FIXED IMPLEMENTATION
 */
function selectAllFilter(filterType) {
    // Get all available options for this filter type
    const allOptions = window.allFilterOptions[filterType] || [];

    // Set all options as selected
    window.connectedFilters[filterType] = [...allOptions];
    console.log(`✅ Selected all ${filterType} options:`, allOptions.length);

    updateFilterOptions(filterType);
    updateAllFilterDropdowns();
    updateConnectedFilterSummary();

    if (typeof updateMarkersEnhanced === 'function') {
        updateMarkersEnhanced();
    } else if (typeof updateMarkers === 'function') {
        updateMarkers();
    }
}

/**
 * Clear all options for a filter - FIXED IMPLEMENTATION
 */
function clearFilter(filterType) {
    window.connectedFilters[filterType] = [];
    console.log(`🗑️ Cleared all ${filterType} options`);

    updateFilterOptions(filterType);
    updateAllFilterDropdowns();
    updateConnectedFilterSummary();

    if (typeof updateMarkersEnhanced === 'function') {
        updateMarkersEnhanced();
    } else if (typeof updateMarkers === 'function') {
        updateMarkers();
    }
}

/**
 * Update all filter dropdowns
 */
function updateAllFilterDropdowns() {
    // Update counts for all filters
    Object.keys(window.connectedFilters).forEach(function(filterType) {
        const counts = calculateFilterCounts(filterType);
        updateFilterCount(filterType, counts.selected, counts.total);
    });
}

/**
 * Calculate filter counts
 */
function calculateFilterCounts(filterType) {
    const availableOptionsSet = new Set();
    const filteredData = getConnectedFilteredData();

    filteredData.forEach(function(item) {
        const itemValue = getItemValue(item, filterType);
        if (itemValue && itemValue !== 'Unknown') {
            availableOptionsSet.add(itemValue);
        }
    });

    return {
        selected: window.connectedFilters[filterType].length,
        total: availableOptionsSet.size
    };
}

/**
 * Get item value for filter type
 */
function getItemValue(item, filterType) {
    switch(filterType) {
        case 'customer': return item.kunde;
        case 'parameter': return item.parameter;
        case 'category': return item.category;
        case 'frequency': return item.häufigkeit;
        case 'pntype': return item.pn_type;
        default: return '';
    }
}

/**
 * Update filter count display
 */
function updateFilterCount(filterType, selected, total) {
    const countElement = document.getElementById(filterType + '-count');
    if (countElement) {
        countElement.textContent = selected === 0 ? `(${total})` : `(${selected}/${total})`;
    }
}

/**
 * Get filtered data based on connected filters
 */
function getConnectedFilteredData() {
    return window.mapConfig.markersData.filter(function(item) {
        return passesConnectedFilters(item);
    });
}




function passesPnTypeFilter(data, selectedPnTypes) {
    if (!selectedPnTypes || selectedPnTypes.length === 0) {
        return true; // No filter applied
    }

    console.log('Checking PN type filter for:', data.messstelle || data.label, 'Selected:', selectedPnTypes);

    // Check if any parameter in this marker matches the selected PN types
    if (data.parameter_details && data.parameter_details.length > 0) {
        const hasMatchingParam = data.parameter_details.some(function(param) {
            const paramType = param.type_filter || (param.type === 'Internal' ? 'I' : param.type === 'External' ? 'E' : param.type);
            const matches = selectedPnTypes.includes(paramType);
            if (matches) {
                console.log('  ✅ Parameter matches:', param.parameter, 'Type:', paramType);
            }
            return matches;
        });
        return hasMatchingParam;
    } else {
        // Fallback: check main pn_type
        const mainPnType = data.pn_type || '';
        const matches = selectedPnTypes.some(function(type) {
            return mainPnType.includes(type);
        });
        console.log('  Fallback check:', mainPnType, 'Matches:', matches);
        return matches;
    }
}

function passesParameterFilter(data, selectedParameters) {
    if (!selectedParameters || selectedParameters.length === 0) {
        return true; // No filter applied
    }

    // Check parameter_details first (most accurate)
    if (data.parameter_details && data.parameter_details.length > 0) {
        const hasMatchingParam = data.parameter_details.some(function(param) {
            const paramName = param.parameter;
            return selectedParameters.includes(paramName);
        });
        return hasMatchingParam;
    } else if (data.parameter) {
        // Fallback: check concatenated parameter string
        const paramList = data.parameter.split(',').map(p => p.trim());
        return paramList.some(param => selectedParameters.includes(param));
    }

    return false;
}

/**
 * FIXED: Check if data passes frequency filter by examining individual frequencies
 */
function passesFrequencyFilter(data, selectedFrequencies) {
    if (!selectedFrequencies || selectedFrequencies.length === 0) {
        return true; // No filter applied
    }

    // Check parameter_details first (most accurate)
    if (data.parameter_details && data.parameter_details.length > 0) {
        const hasMatchingFreq = data.parameter_details.some(function(param) {
            const frequency = param.frequency;
            return selectedFrequencies.includes(frequency);
        });
        return hasMatchingFreq;
    } else if (data.häufigkeit) {
        // Fallback: check concatenated frequency string
        const freqList = data.häufigkeit.split(',').map(f => f.trim());
        return freqList.some(freq => selectedFrequencies.includes(freq));
    }

    return false;
}


/**
 * FIXED: Override calculateFilterCounts to handle PN type properly
 */
const originalCalculateFilterCounts = calculateFilterCounts;
calculateFilterCounts = function(filterType) {
    if (filterType === 'pntype') {
        // Special handling for PN type - always return consistent counts
        const options = createPnTypeFilterOptions(window.mapConfig.markersData || []);
        return {
            selected: window.connectedFilters[filterType].length,
            total: options.length  // This will always be 2 (I and E) or less
        };
    } else {
        // Use original logic for other filters
        return originalCalculateFilterCounts ? originalCalculateFilterCounts(filterType) : {
            selected: 0,
            total: 0
        };
    }
};





/**
 * FIXED: Override extractConnectedFilterOptions to prevent wrong PN counts
 */
const originalExtractConnectedFilterOptions = extractConnectedFilterOptions;
extractConnectedFilterOptions = function() {
    // Run original extraction for other filters
    if (originalExtractConnectedFilterOptions) {
        originalExtractConnectedFilterOptions();
    } else {
        // Fallback extraction
        const customers = new Set();
        const parameters = new Set();
        const categories = new Set();
        const frequencies = new Set();

        window.mapConfig.markersData.forEach(function(item) {
            if (item.kunde && item.kunde !== 'Unknown') customers.add(item.kunde);
            if (item.parameter && item.parameter !== 'Unknown') parameters.add(item.parameter);
            if (item.category) categories.add(item.category);
            if (item.häufigkeit && item.häufigkeit !== 'Unknown') frequencies.add(item.häufigkeit);
        });

        window.allFilterOptions.customer = [...customers].sort();
        window.allFilterOptions.parameter = [...parameters].sort();
        window.allFilterOptions.category = [...categories].sort();
        window.allFilterOptions.frequency = [...frequencies].sort();
    }

    // FIXED: Force PN type to always be only I and E
    window.allFilterOptions.pntype = ['I', 'E'];

    console.log('Filter options after extraction:', {
        customers: window.allFilterOptions.customer.length,
        parameters: window.allFilterOptions.parameter.length,
        categories: window.allFilterOptions.category.length,
        frequencies: window.allFilterOptions.frequency.length,
        pnTypes: window.allFilterOptions.pntype.length  // This should always be 2
    });
};



/**
 * FIXED: Override updateAllFilterDropdowns to use consistent counts
 */
const originalUpdateAllFilterDropdowns = updateAllFilterDropdowns;
updateAllFilterDropdowns = function() {
    // Update counts for all filters with special PN type handling
    Object.keys(window.connectedFilters).forEach(function(filterType) {
        const counts = calculateFilterCounts(filterType);  // This now uses our fixed version
        updateFilterCount(filterType, counts.selected, counts.total);
    });
};





/**
 * FIXED: Override clearAllFilters to maintain consistent counts
 */
const originalClearAllFilters = clearAllFilters;
clearAllFilters = function() {
    console.log('Clearing all connected filters with fixed counts');

    // Reset filter state
    Object.keys(window.connectedFilters).forEach(function(key) {
        window.connectedFilters[key] = [];
    });

    // Close dropdowns and update UI with fixed counts
    closeAllDropdowns();
    updateAllFilterDropdowns();  // This uses our fixed version
    updateConnectedFilterSummary();

    if (typeof updateMarkersEnhanced === 'function') {
        updateMarkersEnhanced();
    } else if (typeof updateMarkers === 'function') {
        updateMarkers();
    }

    console.log('All connected filters cleared with consistent counts');
};





/**
 * FIXED: Initialize filter system with consistent counts
 */
function initializeConsistentFilters() {
    console.log('Initializing consistent filter counting system');

    if (window.mapConfig && window.mapConfig.markersData && window.mapConfig.markersData.length > 0) {
        // Extract options with our fixed logic
        extractConnectedFilterOptions();

        // Update all dropdowns with consistent counts
        updateAllFilterDropdowns();

        // Test PN type filter specifically
        const pnOptions = createPnTypeFilterOptions(window.mapConfig.markersData);
        console.log('PN type options count should be:', pnOptions.length);

        // Force update PN type display
        updateFilterCount('pntype', 0, pnOptions.length);

        console.log('Filter system initialized with consistent counts');
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(initializeConsistentFilters, 1500);
});



/**
 * FIXED: Debug function to check filter counts
 */
function debugFilterCounts() {
    console.log('=== FILTER COUNTS DEBUG ===');
    Object.keys(window.connectedFilters || {}).forEach(function(filterType) {
        const counts = calculateFilterCounts(filterType);
        const displayElement = document.getElementById(filterType + '-count');
        const displayText = displayElement ? displayElement.textContent : 'N/A';

        console.log(`${filterType}:`, {
            selected: counts.selected,
            total: counts.total,
            displayed: displayText
        });

        if (filterType === 'pntype') {
            const options = createPnTypeFilterOptions(window.mapConfig.markersData || []);
            console.log('PN type options:', options);
        }
    });
    console.log('============================');
}

// Call debug after initialization
setTimeout(debugFilterCounts, 3000);






/**
 * Check if data passes connected filters
 */
function passesConnectedFilters(data) {
    if (!window.connectedFilters) {
        return true; // No filters applied
    }

    // Check each filter type
    for (const filterType in window.connectedFilters) {
        const selectedValues = window.connectedFilters[filterType];
        if (selectedValues.length > 0) {
            if (filterType === 'pntype') {
                // Special handling for PN type filter
                if (!passesPnTypeFilter(data, selectedValues)) {
                    return false;
                }
            } else if (filterType === 'parameter') {
                // FIXED: Special handling for parameter filter - check individual parameters
                if (!passesParameterFilter(data, selectedValues)) {
                    return false;
                }
            } else if (filterType === 'frequency') {
                // FIXED: Special handling for frequency filter - check individual frequencies
                if (!passesFrequencyFilter(data, selectedValues)) {
                    return false;
                }
            } else {
                // Standard handling for customer and category
                const itemValue = getItemValue(data, filterType);
                if (!selectedValues.includes(itemValue)) {
                    return false;
                }
            }
        }
    }
    return true;
}




function create_pn_type_filter_options(data) {
    if (!data) {
        return [];
    }

    // Count individual I and E types from parameter details
    let internalCount = 0;
    let externalCount = 0;

    data.forEach(function(item) {
        if (item.parameter_details && item.parameter_details.length > 0) {
            // Count from individual parameter details
            item.parameter_details.forEach(function(param) {
                if (param.type === 'Internal' || param.type === 'I') {
                    internalCount++;
                } else if (param.type === 'External' || param.type === 'E') {
                    externalCount++;
                }
            });
        } else {
            // Fallback: count from main pn_type
            const pnType = item.pn_type || '';
            if (pnType.includes('I')) {
                internalCount++;
            }
            if (pnType.includes('E')) {
                externalCount++;
            }
        }
    });

    const options = [];

    // Always show Internal option if any internal parameters exist
    if (internalCount > 0) {
        options.push({
            'label': html.Div([
                html.Div(style={
                    'width': '16px', 'height': '16px',
                    'backgroundColor': '#007bff',
                    'border': '2px solid white', 'borderRadius': '3px',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.3)', 'marginRight': '8px',
                    'display': 'inline-block', 'verticalAlign': 'middle'
                }),
                html.Span(`Internal (${internalCount})`, style={
                    'fontSize': '14px', 'fontWeight': '500', 'verticalAlign': 'middle'
                })
            ], style={'display': 'flex', 'alignItems': 'center'}),
            'value': 'I'
        });
    }

    // Always show External option if any external parameters exist
    if (externalCount > 0) {
        options.push({
            'label': html.Div([
                html.Div(style={
                    'width': '16px', 'height': '16px',
                    'backgroundColor': '#dc3545',
                    'border': '2px solid white', 'borderRadius': '3px',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.3)', 'marginRight': '8px',
                    'display': 'inline-block', 'verticalAlign': 'middle'
                }),
                html.Span(`External (${externalCount})`, style={
                    'fontSize': '14px', 'fontWeight': '500', 'verticalAlign': 'middle'
                })
            ], style={'display': 'flex', 'alignItems': 'center'}),
            'value': 'E'
        });
    }

    return options;
}







/**
 * Clear all connected filters - GLOBAL FUNCTION FOR TEMPLATE
 */
function clearAllFilters() {
    console.log('🗑️ Clearing all connected filters');

    // Reset filter state
    Object.keys(window.connectedFilters).forEach(function(key) {
        window.connectedFilters[key] = [];
    });

    // Close dropdowns and update UI
    closeAllDropdowns();
    updateAllFilterDropdowns();
    updateConnectedFilterSummary();

    if (typeof updateMarkersEnhanced === 'function') {
        updateMarkersEnhanced();
    } else if (typeof updateMarkers === 'function') {
        updateMarkers();
    }

    console.log('✅ All connected filters cleared');
}

/**
 * Update filter summary
 */
/**
 * Enhanced filter summary with individual deselect options
 */
function updateConnectedFilterSummary() {
    const summaryElement = document.getElementById('filter-summary');
    if (!summaryElement) return;

    const activeSummary = [];
    let hasActiveFilters = false;

    Object.keys(window.connectedFilters).forEach(function(filterType) {
        const selectedItems = window.connectedFilters[filterType];
        if (selectedItems.length > 0) {
            hasActiveFilters = true;
            const emoji = {
                customer: '👥',
                parameter: '🧪',
                category: '📁',
                frequency: '📅',
                pntype: '🏢'
            }[filterType] || '🔍';

            const filterName = filterType.charAt(0).toUpperCase() + filterType.slice(1);

            // Create detailed summary for this filter
            let filterSummary = `<div style="margin-bottom: 12px; padding: 8px; background: #f8f9fa; border-radius: 6px; border-left: 3px solid #007bff;">`;
            filterSummary += `<div style="font-weight: bold; margin-bottom: 6px; color: #2c3e50;">${emoji} ${filterName} (${selectedItems.length})</div>`;

            // Add individual selected items with remove buttons
            selectedItems.forEach(function(item, index) {
                const displayText = filterType === 'pntype' ?
                    (item === 'I' ? 'Internal' : item === 'E' ? 'External' : item) :
                    item;

                filterSummary += `
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; padding: 4px 8px; background: white; border-radius: 4px; border: 1px solid #dee2e6;">
                        <span style="font-size: 12px; color: #495057; flex: 1;">${displayText}</span>
                        <button onclick="removeFilterItem('${filterType}', '${item}')" 
                                style="background: #dc3545; color: white; border: none; border-radius: 3px; width: 18px; height: 18px; font-size: 10px; cursor: pointer; margin-left: 8px; display: flex; align-items: center; justify-content: center;"
                                title="Remove this filter">×</button>
                    </div>`;
            });

            filterSummary += `</div>`;
            activeSummary.push(filterSummary);
        }
    });

    if (!hasActiveFilters) {
        summaryElement.innerHTML = '<em style="color: #6c757d;">No filters applied</em>';
    } else {
        summaryElement.innerHTML = `
            <div style="margin-bottom: 10px;">
                <strong style="color: #2c3e50;">Active Filters:</strong>
            </div>
            ${activeSummary.join('')}
        `;
    }
}


/**
 * Remove individual filter item
 */
function removeFilterItem(filterType, item) {
    const index = window.connectedFilters[filterType].indexOf(item);
    if (index > -1) {
        window.connectedFilters[filterType].splice(index, 1);
        console.log(`🗑️ Removed ${item} from ${filterType} filter`);

        // Update UI
        updateFilterOptions(filterType);
        updateAllFilterDropdowns();
        updateConnectedFilterSummary();

        // Update markers
        if (typeof updateMarkersEnhanced === 'function') {
            updateMarkersEnhanced();
        } else if (typeof updateMarkers === 'function') {
            updateMarkers();
        }
    }
}





/**
 * Enhanced debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Enhanced throttle function for better performance
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}