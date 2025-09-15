// UPDATED: Complete map-utils.js with FIXED Messstelle label positioning and professional styling

/**
 * Create marker icon with caching for performance
 */
const iconCache = new Map();

function createMarkerIcon(color, isComplete, clusterInfo) {
    const cacheKey = `${color}-${isComplete}-${clusterInfo ? clusterInfo.cluster_size : 0}`;

    if (iconCache.has(cacheKey)) {
        return iconCache.get(cacheKey);
    }

    const symbol = isComplete ? '✓' : '✗';
    const symbolColor = '#000000';

    // Add cluster indicator if needed
    let clusterText = '';
    if (clusterInfo && clusterInfo.is_clustered && clusterInfo.cluster_size > 1) {
        clusterText = `<text x='24' y='8' text-anchor='middle' fill='white' font-size='8' font-weight='bold'>${clusterInfo.cluster_size}</text>`;
    }

    const iconSvg = `
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="45" viewBox="0 0 32 45">
            <ellipse cx="16" cy="42" rx="8" ry="3" fill="rgba(0,0,0,0.2)"/>
            <path d="M16 2 C8 2, 2 8, 2 16 C2 24, 16 42, 16 42 S30 24, 30 16 C30 8, 24 2, 16 2 Z"
                  fill="${color}" stroke="#ffffff" stroke-width="2"/>
            <circle cx="16" cy="16" r="9" fill="#ffffff" stroke="rgba(0,0,0,0.2)" stroke-width="1"/>
            <text x="16" y="21" text-anchor="middle"
                  fill="${symbolColor}" font-size="14" font-weight="bold" font-family="Arial">${symbol}</text>
            ${clusterText}
        </svg>
    `;

    const icon = L.divIcon({
        html: iconSvg,
        iconSize: [32, 45],
        iconAnchor: [16, 45],
        popupAnchor: [0, -45],
        className: 'custom-marker-icon'
    });

    iconCache.set(cacheKey, icon);
    return icon;
}

/**
 * UPDATED: Create popup content with caching for performance and full Messstelle support - FIXED
 */
const popupCache = new Map();

function createPopupContent(data) {
    const cacheKey = `${data.label}-${data.parameter_details ? data.parameter_details.length : 0}-${JSON.stringify(window.connectedFilters.pntype || [])}-v3`;

    if (popupCache.has(cacheKey)) {
        return popupCache.get(cacheKey);
    }

    // Get selected PN types from filter
    const selectedPnTypes = window.connectedFilters && window.connectedFilters.pntype ? window.connectedFilters.pntype : [];

    const messstelleValue = getMessstelleValue(data);
    const statusIcon = data.complete ? '✅' : '❌';

    // Handle zero samples display
    const isZeroSample = hasZeroSamples(data);
    let zeroSampleInfo = '';
    if (isZeroSample) {
        zeroSampleInfo = `
            <div style="margin-bottom: 8px; padding: 6px; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; color: #856404; font-size: 12px;">
                ⚠️ <strong>Zero Sample Point</strong> (0 samples expected/taken)
            </div>`;
    }

    // FIXED: Filter parameters based on selected PN types
    let parametersToShow = data.parameter_details || [];

    if (selectedPnTypes.length > 0 && data.parameter_details && data.parameter_details.length > 0) {
        // Filter parameters based on selected PN types
        parametersToShow = data.parameter_details.filter(function(param) {
            const paramType = param.type === 'Internal' ? 'I' : param.type === 'External' ? 'E' : param.type;
            return selectedPnTypes.includes(paramType);
        });

        console.log(`Filtered parameters: ${parametersToShow.length}/${data.parameter_details.length} parameters shown for PN types:`, selectedPnTypes);
    }

    // Create the parameter table HTML with individual progress column
    let parameterTableHtml = '';

    if (parametersToShow && parametersToShow.length > 0) {
        console.log('Creating filtered table with individual parameter progress:', parametersToShow.length);

        parameterTableHtml = `
            <div style="margin-top: 15px; background: white; border: 2px solid #2c3e50; border-radius: 8px; overflow: hidden;">
                <div style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); padding: 10px; border-bottom: 2px solid #2c3e50;">
                    <strong style="color: #ecf0f1; font-size: 14px; letter-spacing: 0.3px;">📊 Individual Parameter Progress</strong>
                    ${selectedPnTypes.length > 0 ?
                        `<span style="font-size: 11px; color: #bdc3c7; margin-left: 8px; font-weight: 400;">(Filtered: ${selectedPnTypes.map(t => t === 'I' ? 'Internal' : 'External').join(', ')})</span>`
                        : ''
                    }
                </div>
                <div style="overflow-x: auto; max-width: 100%;">
                    <table style="width: 100%; border-collapse: collapse; margin: 0; background: white;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 10px 8px; border-right: 1px solid #2c3e50; border-bottom: 1px solid #2c3e50; font-weight: bold; text-align: left; font-size: 12px; min-width: 140px; color: #2c3e50;">Parameter</th>
                                <th style="padding: 10px 8px; border-right: 1px solid #2c3e50; border-bottom: 1px solid #2c3e50; font-weight: bold; text-align: left; font-size: 12px; min-width: 110px; color: #2c3e50;">Frequency</th>
                                <th style="padding: 10px 8px; border-right: 1px solid #2c3e50; border-bottom: 1px solid #2c3e50; font-weight: bold; text-align: center; font-size: 12px; min-width: 90px; color: #2c3e50;">Progress</th>
                                <th style="padding: 10px 8px; border-right: 1px solid #2c3e50; border-bottom: 1px solid #2c3e50; font-weight: bold; text-align: center; font-size: 12px; min-width: 70px; color: #2c3e50;">Type</th>
                                <th style="padding: 10px 8px; border-bottom: 1px solid #2c3e50; font-weight: bold; text-align: center; font-size: 12px; min-width: 90px; color: #2c3e50;">Latest Sample</th>
                            </tr>
                        </thead>
                        <tbody>`;

        // Sort parameters alphabetically - each parameter gets its own row with individual progress
        const sortedParams = parametersToShow.sort(function(a, b) {
            return a.parameter.localeCompare(b.parameter);
        });

        // Create one row for each filtered parameter with individual progress
        sortedParams.forEach(function(param, index) {
            const currentSamples = param.current || 0;
            const totalSamples = param.total || 0;
            const progressPercent = totalSamples > 0 ? Math.round((currentSamples / totalSamples) * 100) : 0;

            // Determine progress status and color
            let progressColor, progressBgColor, progressText;
            if (progressPercent >= 100) {
                progressColor = '#ffffff';
                progressBgColor = '#27ae60'; // Professional green for complete
                progressText = 'Complete';
            } else if (progressPercent > 0) {
                progressColor = '#2c3e50';
                progressBgColor = '#f39c12'; // Professional orange for partial
                progressText = 'In Progress';
            } else {
                progressColor = '#ffffff';
                progressBgColor = '#e74c3c'; // Professional red for not started
                progressText = 'Not Started';
            }

            const typeText = param.type === 'Internal' ? 'Internal' : 'External';
            const typeColor = param.type === 'Internal' ? '#3498db' : '#e74c3c';
            const bgColor = index % 2 === 0 ? 'white' : '#f8f9fa';

            // ADDED: Get latest date for this parameter
            let latestDate = 'No samples';
            if (param.latest_date) {
                latestDate = param.latest_date;
            } else if (currentSamples > 0) {
                latestDate = 'Date not available';
            }

            console.log(`Parameter ${param.parameter}: latest_date = ${param.latest_date}, currentSamples = ${currentSamples}`);

            parameterTableHtml += `
                <tr style="background: ${bgColor};">
                    <td style="padding: 8px; border-right: 1px solid #ddd; font-size: 11px; word-wrap: break-word; max-width: 140px; vertical-align: top;">
                        <strong style="color: #2c3e50;">${param.parameter}</strong>
                    </td>
                    <td style="padding: 8px; border-right: 1px solid #ddd; font-size: 11px; vertical-align: top; color: #34495e;">
                        ${param.frequency || 'Unknown'}
                    </td>
                    <td style="padding: 6px; border-right: 1px solid #ddd; vertical-align: top;">
                        <div style="background: #ecf0f1; border-radius: 6px; overflow: hidden; min-width: 80px; position: relative;">
                            <div style="
                                width: ${Math.min(progressPercent, 100)}%;
                                background: ${progressBgColor};
                                height: 22px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                min-width: 100%;
                                position: relative;
                                transition: all 0.3s ease;
                            ">
                                <span style="
                                    position: absolute;
                                    left: 50%;
                                    top: 50%;
                                    transform: translate(-50%, -50%);
                                    font-size: 10px;
                                    font-weight: bold;
                                    color: ${progressColor};
                                    white-space: nowrap;
                                    z-index: 2;
                                ">${currentSamples}/${totalSamples}</span>
                            </div>
                        </div>
                        <div style="text-align: center; font-size: 9px; color: #7f8c8d; margin-top: 3px; font-weight: 500;">
                            ${progressPercent}% - ${progressText}
                        </div>
                    </td>
                    <td style="padding: 8px; border-right: 1px solid #ddd; font-size: 11px; text-align: center; vertical-align: top;">
                        <span style="padding: 3px 8px; border-radius: 4px; background: ${typeColor}; color: white; font-size: 10px; font-weight: bold; letter-spacing: 0.2px;">${typeText}</span>
                    </td>
                    <td style="padding: 8px; font-size: 10px; text-align: center; vertical-align: top; color: #495057;">
                        <div style="font-weight: 500;">
                            ${latestDate}
                        </div>
                    </td>
                </tr>`;
        });

        parameterTableHtml += `
                        </tbody>
                    </table>
                </div>
            </div>`;

    } else {
        // Show message when no parameters match the filter
        parameterTableHtml = `
            <div style="margin-top: 15px; padding: 20px; text-align: center; color: #7f8c8d; background: #f8f9fa; border-radius: 8px; border: 1px solid #dee2e6;">
                <strong style="color: #2c3e50;">No parameters match the current PN type filter</strong><br>
                <small style="color: #95a5a6;">Selected: ${selectedPnTypes.map(t => t === 'I' ? 'Internal' : 'External').join(', ')}</small>
            </div>`;
    }

    // Calculate summary statistics for filtered parameters
    const filteredTotalSamples = parametersToShow.reduce(function(sum, param) {
        return sum + (param.total || 0);
    }, 0);

    const filteredCompletedSamples = parametersToShow.reduce(function(sum, param) {
        return sum + (param.current || 0);
    }, 0);

    const filteredCompletionRate = filteredTotalSamples > 0 ?
        Math.round((filteredCompletedSamples / filteredTotalSamples) * 100) : 0;

    const content = `
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; width: 480px; max-width: 480px; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 6px 25px rgba(0,0,0,0.15); border: 1px solid rgba(44, 62, 80, 0.1);">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); color: white; padding: 15px;">
                <h4 style="margin: 0; font-size: 16px; line-height: 1.3; font-weight: 600; letter-spacing: 0.3px;">${statusIcon} ${messstelleValue}</h4>
                <div style="font-size: 12px; margin-top: 6px; line-height: 1.4; opacity: 0.9;">
                    <div><strong>Customer:</strong> ${data.kunde || 'Unknown'}</div>
                    ${data.zapfstelle && data.zapfstelle !== 'Not Specified' ?
                        `<div><strong>Zapfstelle:</strong> ${data.zapfstelle}</div>` : ''}
                </div>
            </div>

            <!-- Content -->
            <div style="padding: 15px; background: white;">
                ${zeroSampleInfo}

                <!-- Summary Stats -->
                <div style="margin-bottom: 12px; padding: 10px; background: linear-gradient(135deg, #ecf0f1 0%, #d5dbdb 100%); border-radius: 6px; border: 1px solid #bdc3c7;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 12px; font-weight: 600; color: #2c3e50;">
                            ${selectedPnTypes.length > 0 ? 'Filtered Summary:' : 'Overall Summary:'}
                        </span>
                        <span style="font-size: 12px; font-weight: 700; color: #34495e;">
                            ${filteredCompletedSamples}/${filteredTotalSamples} samples (${filteredCompletionRate}%)
                        </span>
                    </div>
                    <div style="font-size: 11px; color: #7f8c8d; margin-top: 3px; font-weight: 500;">
                        ${parametersToShow.length} parameter${parametersToShow.length !== 1 ? 's' : ''} shown
                        ${selectedPnTypes.length > 0 ? ` • Filter: ${selectedPnTypes.map(t => t === 'I' ? 'Internal' : 'External').join(' + ')}` : ''}
                    </div>
                </div>

                <!-- Status -->
                <div style="margin-bottom: 10px; padding: 8px; background: ${data.complete ? '#d5f4e6' : '#fdeaea'}; border-radius: 6px; border: 1px solid ${data.complete ? '#27ae60' : '#e74c3c'};">
                    <strong style="color: ${data.complete ? '#27ae60' : '#e74c3c'};">Overall Status:</strong> ${data.complete ? 'Complete' : 'Incomplete'}
                </div>

                ${parameterTableHtml}
            </div>
        </div>
    `;

    popupCache.set(cacheKey, content);
    return content;
}

/**
 * UPDATED: Get Messstelle value from data object - Enhanced for better compatibility
 */
function getMessstelleValue(data) {
    // First priority: Use the actual Messstelle column value from Excel
    if (data.messstelle) {
        return data.messstelle;
    }
    // Alternative spellings that might be in the data
    else if (data.Messstelle) {
        return data.Messstelle;
    }
    else if (data.MESSSTELLE) {
        return data.MESSSTELLE;
    }
    else if (data['Messstelle']) {
        return data['Messstelle'];
    }
    else {
        // Check for any key containing 'messstelle' (case insensitive)
        const keys = Object.keys(data);
        const messstelleKey = keys.find(key =>
            key.toLowerCase().includes('messstelle')
        );

        if (messstelleKey) {
            console.log('Found Messstelle key:', messstelleKey, 'with value:', data[messstelleKey]);
            return data[messstelleKey];
        } else {
            // Log available keys for debugging
            console.log('Available data keys:', Object.keys(data));

            // Fallback to extracting from label
            if (data.label) {
                const parts = data.label.split(' - ');
                if (parts.length >= 3) {
                    return parts[parts.length - 1].trim();
                } else if (parts.length >= 1) {
                    return parts[0].trim();
                }
            }

            // Final fallback
            return data.label || 'Unknown Messstelle';
        }
    }
}

/**
 * Process marker data for enhanced functionality
 */
function processMarkerData(originalData) {
    return originalData.map(function(item) {
        return {
            ...item,
            parameter_count: item.parameter_details ? item.parameter_details.length : 1
        };
    });
}

/**
 * Throttle function to limit execution frequency
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

/**
 * Debounce function to delay execution
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
 * Check if a data item passes current filters (if connected filters exist) - FIXED
 */
function passesConnectedFilters(data) {
    // This function will be used if connected filters are available
    // Check each filter type
    if (!window.connectedFilters) {
        return true; // No filters applied
    }

    for (const filterType in window.connectedFilters) {
        const selectedValues = window.connectedFilters[filterType];
        if (selectedValues.length > 0) {
            if (filterType === 'pntype') {
                // Special handling for PN type filter
                if (!passesPnTypeFilter(data, selectedValues)) {
                    return false;
                }
            } else {
                const itemValue = getItemValue(data, filterType);
                if (!selectedValues.includes(itemValue)) {
                    return false;
                }
            }
        }
    }
    return true;
}

/**
 * UPDATED: Enhanced PN type filter checking
 */
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
 * Utility function to check if a data point has zero samples - FIXED
 */
function hasZeroSamples(data) {
    return (data.total_samples === 0 && data.completed_samples === 0) || data.is_zero_sample === true;
}

/**
 * Format numbers without decimals
 */
function formatNumber(num) {
    if (typeof num === 'number') {
        if (num % 1 === 0) {
            return num.toString();
        } else {
            return num.toFixed(0);
        }
    }
    return num.toString();
}

/**
 * Safely truncate text for display
 */
function safeTruncate(text, maxLength = 100) {
    if (!text || text === "Unknown") {
        return "Not specified";
    }
    const textStr = text.toString();
    return textStr.length > maxLength ? textStr.substring(0, maxLength) + '...' : textStr;
}

/**
 * Get statistics for visible markers - utility function
 */
function getVisibleMarkersStats() {
    if (!window.allMarkers) return null;

    const visibleData = window.allMarkers
        .filter(markerData => window.map && window.map.hasLayer(markerData.marker))
        .map(markerData => markerData.data);

    return {
        total: visibleData.length,
        complete: visibleData.filter(item => item.complete).length,
        incomplete: visibleData.filter(item => !item.complete).length,
        customers: new Set(visibleData.map(item => item.kunde)).size,
        parameters: new Set(visibleData.map(item => item.parameter)).size,
        internal: visibleData.filter(item => item.pn_type === 'I').length,
        external: visibleData.filter(item => item.pn_type === 'E').length,
        zeroSamples: visibleData.filter(item => hasZeroSamples(item)).length
    };
}

/**
 * Create enhanced tooltip content
 */
function createTooltipContent(data, type = 'hover') {
    if (type === 'hover') {
        return data.label;
    } else if (type === 'permanent') {
        return getMessstelleValue(data);
    }
    return data.label;
}

/**
 * Performance optimization: Batch DOM operations
 */
function batchDOMUpdates(updates) {
    // Use requestAnimationFrame for optimal timing
    requestAnimationFrame(() => {
        updates.forEach(update => {
            try {
                update();
            } catch (error) {
                console.warn('DOM update failed:', error);
            }
        });
    });
}

/**
 * Clean up cached data for memory management
 */
function cleanupCaches() {
    if (iconCache.size > 100) {
        iconCache.clear();
        console.log('🧹 Icon cache cleared');
    }
    if (popupCache.size > 50) {
        popupCache.clear();
        console.log('🧹 Popup cache cleared');
    }
}

/**
 * Initialize performance monitoring
 */
function initializePerformanceMonitoring() {
    // Clean up caches periodically
    setInterval(cleanupCaches, 300000); // Every 5 minutes

    // Log performance stats
    if (window.mapConfig && window.mapConfig.markersData && window.mapConfig.markersData.length > 500) {
        console.log('📊 Large dataset detected - performance monitoring enabled');

        setInterval(() => {
            const stats = getVisibleMarkersStats();
            if (stats) {
                console.log(`🔍 Performance stats: ${stats.total} visible markers, ${iconCache.size} cached icons, ${popupCache.size} cached popups`);
            }
        }, 30000); // Every 30 seconds
    }
}

// Initialize performance monitoring when this script loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePerformanceMonitoring);
} else {
    initializePerformanceMonitoring();
}