// UPDATED: Main map initialization with FIXED Messstelle label positioning and professional styling

// Global variables
window.map = null;
window.streetLayer = null;
window.satelliteLayer = null;
window.isSatellite = false;
window.allMarkers = [];
window.forceLabels = false;
window.currentZoom = 9;
window.isUpdating = false;

// Legacy filter state (for category checkboxes compatibility)
window.activeFilters = {
    categories: Object.keys(window.mapConfig?.categoryColors || {}),
    showComplete: true,
    showIncomplete: true,
    showZeroSamples: false  // NEW: Control for 0/0 messstelle
};

// Connected filter state for the enhanced dropdowns
window.connectedFilters = {
    customer: [],
    parameter: [],
    category: [],
    frequency: [],
    pntype: []
};

window.allFilterOptions = {
    customer: [],
    parameter: [],
    category: [],
    frequency: [],
    pntype: []
};

console.log('📊 Map initialized with data:', window.mapConfig?.markersData?.length || 0);

/**
 * Initialize map with moderate performance optimizations
 */
function initializeEnhancedMap() {
    // Initialize map with balanced settings
    window.map = L.map('map', {
        preferCanvas: true,
        zoomAnimation: true,          // Re-enabled but will be smoother
        fadeAnimation: false,         // Keep disabled for performance
        markerZoomAnimation: false,
        zoomSnap: 1,
        zoomDelta: 1,
        wheelDebounceTime: 60,
        wheelPxPerZoomLevel: 60,
        updateWhenIdle: true,
        updateWhenZooming: false
    }).setView([52.318417, 11.567817], 9);

    // Base layers with performance optimizations
    window.streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18,
        updateWhenIdle: true,
        updateWhenZooming: false,
        keepBuffer: 2
    }).addTo(window.map);

    window.satelliteLayer = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
    attribution: '© Google',
    maxZoom: 18,
    updateWhenIdle: true,
    updateWhenZooming: false,
    keepBuffer: 2
    });

    console.log('🗺️ Map initialized successfully');
}

/**
 * File upload handling
 */
function initializeFileUpload() {
    const fileInput = document.getElementById('excel-file');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                uploadFile(file);
            }
        });
    }
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const statusDiv = document.getElementById('upload-status');
    statusDiv.innerHTML = '<span class="loading"></span>Uploading and processing...';

    console.log('📤 Uploading file:', file.name);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log('📥 Upload response:', data);

        if (data.success) {
            statusDiv.innerHTML = '<span class="upload-success">✅ ' + data.message + '</span>';
            if (data.debug_info) {
                console.log('🔍 Debug info:', data.debug_info);
            }
            // Reload page to show new data
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            statusDiv.innerHTML = '<span class="upload-error">❌ ' + data.error + '</span>';
            if (data.debug_info) {
                console.log('🔍 Debug info:', data.debug_info);
            }
        }
    })
    .catch(error => {
        statusDiv.innerHTML = '<span class="upload-error">❌ Upload failed</span>';
        console.error('❌ Upload error:', error);
    });
}

/**
 * Toggle satellite view
 */
function toggleSatellite() {
    if (!window.map) {
        console.error('Map not initialized');
        return;
    }

    try {
        if (window.isSatellite) {
            // Switch to street view
            if (window.satelliteLayer && window.map.hasLayer(window.satelliteLayer)) {
                window.map.removeLayer(window.satelliteLayer);
            }
            if (window.streetLayer) {
                window.map.addLayer(window.streetLayer);
            }
            console.log('Switched to street view');
        } else {
            // Switch to satellite view
            if (window.streetLayer && window.map.hasLayer(window.streetLayer)) {
                window.map.removeLayer(window.streetLayer);
            }
            if (window.satelliteLayer) {
                window.map.addLayer(window.satelliteLayer);
            }
            console.log('Switched to satellite view');
        }

        window.isSatellite = !window.isSatellite;
    } catch (error) {
        console.error('Error toggling satellite view:', error);

        // Recovery: ensure we have at least one layer
        if (!window.map.hasLayer(window.streetLayer) && !window.map.hasLayer(window.satelliteLayer)) {
            window.map.addLayer(window.streetLayer);
            window.isSatellite = false;
        }
    }
}
/**
 * Create category controls
 */
function createCategoryControls() {
    const container = document.getElementById('category-checkboxes');
    if (!container || !window.mapConfig?.categoryColors) return;

    const fragment = document.createDocumentFragment();
    const categoryColors = window.mapConfig.categoryColors;

    Object.keys(categoryColors).forEach(function(category) {
        const div = document.createElement('div');
        div.className = 'checkbox-item';

        const colorBox = document.createElement('div');
        colorBox.className = 'color-box';
        colorBox.style.backgroundColor = categoryColors[category];

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = 'cat-' + category;
        checkbox.checked = true;
        checkbox.onchange = function() {
            updateCategoryFilter();
            updateMarkersEnhanced();
        };

        const label = document.createElement('label');
        label.textContent = category;
        label.style.fontSize = '10px';

        div.appendChild(colorBox);
        div.appendChild(checkbox);
        div.appendChild(label);
        fragment.appendChild(div);
    });

    container.appendChild(fragment);
}

/**
 * Update category filter state
 */
function updateCategoryFilter() {
    window.activeFilters.categories = [];
    const categoryColors = window.mapConfig?.categoryColors || {};

    Object.keys(categoryColors).forEach(function(category) {
        const checkbox = document.getElementById('cat-' + category);
        if (checkbox && checkbox.checked) {
            window.activeFilters.categories.push(category);
        }
    });
}

/**
 * Select all categories
 */
function selectAllCategories() {
    const categoryColors = window.mapConfig?.categoryColors || {};
    Object.keys(categoryColors).forEach(function(category) {
        const checkbox = document.getElementById('cat-' + category);
        if (checkbox) checkbox.checked = true;
    });
    updateCategoryFilter();
    updateMarkersEnhanced();
}

/**
 * Clear all categories
 */
function clearAllCategories() {
    const categoryColors = window.mapConfig?.categoryColors || {};
    Object.keys(categoryColors).forEach(function(category) {
        const checkbox = document.getElementById('cat-' + category);
        if (checkbox) checkbox.checked = false;
    });
    updateCategoryFilter();
    updateMarkersEnhanced();
}

/**
 * Toggle labels function - FIXED TO WORK PROPERLY
 */
function toggleLabels() {
    const forceLabelsCheckbox = document.getElementById('force-labels');
    if (forceLabelsCheckbox) {
        window.forceLabels = forceLabelsCheckbox.checked;
        console.log('🏷️ Force labels toggled:', window.forceLabels);
        updateLabels(); // This should now work properly
    }
}

function updateMarkerPopup(markerItem, data) {
    try {
        // Get current PN type filter selection
        const selectedPnTypes = window.connectedFilters && window.connectedFilters.pntype ? window.connectedFilters.pntype : [];

        // Create filtered popup content
        const popupContent = createPopupContent(data);

        // Update the marker's popup
        markerItem.marker.getPopup().setContent(popupContent);

        console.log(`Updated popup for ${data.messstelle || data.label} with PN filter:`, selectedPnTypes);
    } catch (error) {
        console.warn('Error updating marker popup:', error);
    }
}

/**
 * Enhanced update markers function with zero sample filtering - FIXED
 */
function updateMarkersEnhanced() {
    if (window.isUpdating) return;
    window.isUpdating = true;

    console.log('🔄 Updating markers with PN type filtering...');

    // Clear popup cache when filters change
    if (typeof clearPopupCache === 'function') {
        clearPopupCache();
    }

    // Get filter states - FIXED to handle missing elements
    const showCompleteEl = document.getElementById('show-complete');
    const showIncompleteEl = document.getElementById('show-incomplete');
    const showZeroSamplesEl = document.getElementById('show-zero-samples');

    window.activeFilters.showComplete = showCompleteEl ? showCompleteEl.checked : true;
    window.activeFilters.showIncomplete = showIncompleteEl ? showIncompleteEl.checked : true;
    window.activeFilters.showZeroSamples = showZeroSamplesEl ? showZeroSamplesEl.checked : false;

    let visibleCount = 0;
    const filteredData = [];

    window.allMarkers.forEach(function(item) {
        const data = item.data;

        if (passesAllFilters(data)) {
            if (!window.map.hasLayer(item.marker)) {
                window.map.addLayer(item.marker);
            }

            // FIXED: Update marker popup with filtered content
            updateMarkerPopup(item, data);

            visibleCount++;
            filteredData.push(data);
        } else {
            if (window.map.hasLayer(item.marker)) {
                window.map.removeLayer(item.marker);
                // Remove Messstelle label if marker becomes invisible
                if (item.hasZoomLabel) {
                    removeMessstelleLabel(item);
                }
            }
        }
    });

    console.log(`👁️ Showing ${visibleCount} of ${window.allMarkers.length} markers (PN filter: ${JSON.stringify(window.connectedFilters.pntype)})`);

    // Update visible count display
    const visibleCountEl = document.getElementById('visible-count');
    if (visibleCountEl) {
        visibleCountEl.textContent = visibleCount;
    }

    // Update statistics if function exists
    if (typeof updateStatistics === 'function') {
        updateStatistics(filteredData);
    }

    updateLabels(); // Update labels after filtering

    // Update filter summary if function exists
    if (typeof updateConnectedFilterSummary === 'function') {
        updateConnectedFilterSummary();
    }

    window.isUpdating = false;
}

/**
 * Enhanced filter checking function with zero sample support - FIXED
 */
function passesAllFilters(data) {
    // Check zero sample filter first - FIXED IMPLEMENTATION
    if (hasZeroSamples(data) && !window.activeFilters.showZeroSamples) {
        return false;
    }

    // Check connected filters if function exists
    if (typeof passesConnectedFilters === 'function') {
        if (!passesConnectedFilters(data)) return false;
    }

    // Check category filters
    if (!window.activeFilters.categories.includes(data.category)) return false;

    // Check status filters
    if (!window.activeFilters.showComplete && data.complete) return false;
    if (!window.activeFilters.showIncomplete && !data.complete) return false;

    return true;
}

/**
 * Utility function to check if a data point has zero samples - FIXED
 */
function hasZeroSamples(data) {
    return (data.total_samples === 0 && data.completed_samples === 0) || data.is_zero_sample === true;
}

/**
 * UPDATED: Update zoom-based labels for Messstelle with FIXED positioning and professional styling
 */
function updateLabels() {
    if (!window.map) return;

    window.currentZoom = window.map.getZoom();
    const forceLabelsEl = document.getElementById('force-labels');
    const forceLabels = forceLabelsEl ? forceLabelsEl.checked : false;
    const showLabels = window.currentZoom >= 12 || forceLabels;

    // Update UI
    const zoomLevelEl = document.getElementById('zoom-level');
    const labelInfoEl = document.getElementById('label-info');

    if (zoomLevelEl) zoomLevelEl.textContent = window.currentZoom;
    if (labelInfoEl) {
        labelInfoEl.textContent = showLabels ? 'Visible' : 'Hidden (zoom to 12+)';
    }

    console.log(`🔍 Zoom: ${window.currentZoom}, Force Labels: ${forceLabels}, Show Labels: ${showLabels}`);

    window.allMarkers.forEach(function(item) {
        // Only process visible markers on the map
        if (!window.map.hasLayer(item.marker)) return;

        if (showLabels && !item.hasZoomLabel) {
            // Add Messstelle label
            addMessstelleLabel(item);
        } else if (!showLabels && item.hasZoomLabel) {
            // Remove Messstelle label
            removeMessstelleLabel(item);
        } else if (showLabels && item.hasZoomLabel) {
            // FIXED: Re-bind label if it got lost during map interactions
            if (!item.marker.getTooltip() && item.zoomLabel) {
                item.marker.bindTooltip(item.zoomLabel);
            }
        }
    });
}

/**
 * UPDATED: Add Messstelle label to marker with FIXED positioning and professional styling
 */
function addMessstelleLabel(markerItem) {
    try {
        const messstelleValue = getMessstelleValue(markerItem.data);
        console.log('Adding permanent Messstelle label:', messstelleValue);

        // FIXED: Create label as separate DOM element with new styling
        if (!markerItem.labelElement) {
            // Create label element
            markerItem.labelElement = document.createElement('div');
            markerItem.labelElement.className = 'permanent-messstelle-label-custom';
            markerItem.labelElement.textContent = messstelleValue;
            markerItem.labelElement.style.cssText = `
                position: absolute;
                z-index: 900;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(0, 0, 0, 0.2);
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
                color: #000000;
                box-shadow: 0 2px 6px rgba(0,0,0,0.15);
                pointer-events: none;
                white-space: normal;
                opacity: 1;
                backdrop-filter: blur(3px);
                max-width: 120px;
                min-width: 60px;
                text-align: center;
                word-wrap: break-word;
                word-break: break-word;
                hyphens: auto;
                overflow-wrap: break-word;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                letter-spacing: 0.1px;
                line-height: 1.2;
                transform: translate(-50%, -100%);
                margin-top: -10px;
            `;

            // Add to map container
            window.map.getContainer().appendChild(markerItem.labelElement);
        }

        // Position the label above the marker
        updateLabelPosition(markerItem);

        // Update position when map moves
        if (!markerItem.positionUpdateBound) {
            const updatePosition = () => updateLabelPosition(markerItem);
            window.map.on('viewreset', updatePosition);
            window.map.on('zoom', updatePosition);
            window.map.on('move', updatePosition)
            markerItem.positionUpdateBound = true;
            markerItem.updatePosition = updatePosition;
        }

        markerItem.hasZoomLabel = true;
        console.log('✅ Permanent Messstelle label added:', messstelleValue);

    } catch (error) {
        console.error('Error adding permanent Messstelle label:', error);
    }
}




function updateLabelPosition(markerItem) {
    if (!markerItem.labelElement || !markerItem.marker || !window.map) return;

    if (markerItem.labelElement.style.visibility === 'hidden') return;

    try {
        // Get marker position in pixels
        const markerLatLng = markerItem.marker.getLatLng();
        const markerPoint = window.map.latLngToContainerPoint(markerLatLng);

        // Position label above marker
        markerItem.labelElement.style.left = markerPoint.x + 'px';
        markerItem.labelElement.style.top = (markerPoint.y - 45) + 'px'; // 45px above marker

    } catch (error) {
        console.warn('Error updating label position:', error);
    }
}




/**
 * UPDATED: Remove Messstelle label from marker and restore hover tooltip - FIXED
 */
function removeMessstelleLabel(markerItem) {
    try {
        console.log('Removing permanent Messstelle label for:', markerItem.data.label);

        // Remove custom label element
        if (markerItem.labelElement) {
            markerItem.labelElement.remove();
            markerItem.labelElement = null;
        }

        // Remove event listeners
        if (markerItem.updatePosition) {
            window.map.off('viewreset', markerItem.updatePosition);
            window.map.off('zoom', markerItem.updatePosition);
            window.map.off('move', markerItem.updatePosition);
            markerItem.positionUpdateBound = false;
            markerItem.updatePosition = null;
        }

        markerItem.hasZoomLabel = false;

        // Ensure hover tooltip is still working
        if (!markerItem.marker.getTooltip()) {
            markerItem.marker.bindTooltip(markerItem.data.label, {
                permanent: false,
                direction: 'top',
                offset: [0, -25],
                className: 'hover-tooltip-improved',
                interactive: false
            });
        }

        console.log('✅ Permanent Messstelle label removed, hover tooltip restored');

    } catch (error) {
        console.error('Error removing permanent Messstelle label:', error);
    }
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
 * Enhanced initialization function - FIXED
 */
function initializeEnhanced() {
    console.log('🚀 Starting enhanced map initialization...');

    // Check if we have the required data
    if (!window.mapConfig) {
        console.error('❌ window.mapConfig is not defined');
        return;
    }

    const markersData = window.mapConfig.markersData;
    console.log('🔍 Markers data:', markersData?.length || 0, 'items');

    // Always initialize the map
    initializeEnhancedMap();
    initializeFileUpload();

    // Initialize connected filters if the function exists
    if (typeof initializeConnectedFilters === 'function') {
        try {
            initializeConnectedFilters();
        } catch (error) {
            console.warn('⚠️ Connected filters initialization failed:', error);
        }
    }

    

    // Add markers if we have data
    if (markersData && markersData.length > 0) {
        console.log('📍 Adding markers...');

        try {
            addMarkersEnhanced();
            updateMarkersEnhanced();

            // Initialize marker events
            initializeEnhancedMarkerEvents();

            // Auto-zoom to show all markers (for reasonable number of markers)
            if (window.allMarkers.length > 0 && window.allMarkers.length < 1000) {
                setTimeout(() => {
                    fitMapToVisibleMarkers();
                }, 500);
            }
        } catch (error) {
            console.error('❌ Error adding markers:', error);
        }
    } else {
        console.log('⚠️ No markers data to display');
    }

    // Update zoom labels
    updateLabels();

    console.log('🎉 Enhanced Map initialization complete');
}

/**
 * UPDATED: Basic marker addition with professional styling - FIXED
 */
function addMarkersEnhanced() {
    const markersData = window.mapConfig.markersData;
    if (!markersData || markersData.length === 0) {
        console.log('No markers to add');
        return;
    }

    console.log('🔧 Adding markers with professional zoom labels to map:', markersData.length);
    window.allMarkers = [];

    markersData.forEach(function(data, index) {
        try {
            const categoryColors = window.mapConfig.categoryColors || {};
            const color = categoryColors[data.category] || '#0000FF';
            const clusterInfo = {
                is_clustered: data.is_clustered || false,
                cluster_size: data.cluster_size || 1
            };

            // Create icon using the utility function if available, or basic marker
            let icon;
            if (typeof createMarkerIcon === 'function') {
                icon = createMarkerIcon(color, data.complete, clusterInfo);
            } else {
                // Fallback icon with professional styling
                icon = L.divIcon({
                    html: `<div style="background-color: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 3px 8px rgba(0,0,0,0.3);"></div>`,
                    iconSize: [20, 20],
                    iconAnchor: [10, 10],
                    className: 'custom-div-icon'
                });
            }

            // Create marker
            const marker = L.marker(data.coordinates, { icon: icon });

            // Add popup with professional styling
            const popupContent = typeof createPopupContent === 'function'
                ? createPopupContent(data)
                : `<strong style="color: #2c3e50;">${data.label}</strong><br>Status: ${data.complete ? '<span style="color: #27ae60;">Complete</span>' : '<span style="color: #e74c3c;">Incomplete</span>'}`;

            marker.bindPopup(() => popupContent, {
                maxWidth: 420,
                className: 'custom-popup'
            });

            // Add professional hover tooltip (always present) - shows full label on hover
            marker.bindTooltip(data.label, {
                permanent: false,
                direction: 'top',
                offset: [0, -25],
                className: 'hover-tooltip-improved',
                interactive: false
            });

            // FIXED: Add event listeners to manage label visibility with popups
           marker.on('popupopen', function() {
                // When ANY popup opens, hide ALL labels
                window.allMarkers.forEach(function(markerData) {
                    if (markerData.labelElement) {
                        markerData.labelElement.style.visibility = 'hidden';
                    }
                });
           });

            marker.on('popupclose', function() {
                // When popup closes, show ALL labels again (if they should be visible)
                const currentZoom = window.map.getZoom();
                const forceLabelsEl = document.getElementById('force-labels');
                const forceLabels = forceLabelsEl ? forceLabelsEl.checked : false;
                const showLabels = currentZoom >= 12 || forceLabels;

                if (showLabels) {
                    window.allMarkers.forEach(function(markerData) {
                        if (markerData.hasZoomLabel && markerData.labelElement) {
                            markerData.labelElement.style.visibility = 'visible';
                        }
                    });
                }
            });

            // Store marker data with zoom label placeholder
            const markerData = {
                marker: marker,
                data: data,
                hasZoomLabel: false,
                zoomLabel: null, // Will be created when needed
                labelElement: null, // For custom DOM label
                positionUpdateBound: false,
                updatePosition: null
            };

            window.allMarkers.push(markerData);
            window.map.addLayer(marker);
        } catch (error) {
            console.error('Error adding marker', index, ':', error);
        }
    });

    console.log('✅ Professional markers added:', window.allMarkers.length);

    // Initialize zoom labels after all markers are added
    updateLabels();
}

/**
 * UPDATED: Initialize enhanced marker event listeners with professional handling - FIXED
 */
function initializeEnhancedMarkerEvents() {
    if (!window.map) return;

    // Zoom event with proper throttling - FIXED
    window.map.on('zoomend', throttle(function() {
        console.log('🔍 Zoom ended, updating professional labels...');
        updateLabels();
    }, 100));

    // FIXED: Add move events to preserve permanent labels
    window.map.on('movestart', function() {
        // Store current permanent labels before move
        window.allMarkers.forEach(function(markerData) {
            if (markerData.hasZoomLabel && markerData.zoomLabel) {
                markerData.labelWasVisible = true;
            }
        });
    });

    window.map.on('moveend', throttle(function() {
        console.log('🗺️ Map move ended, restoring permanent labels...');
        // Restore permanent labels after move
        window.allMarkers.forEach(function(markerData) {
            if (markerData.labelWasVisible && markerData.hasZoomLabel && markerData.zoomLabel) {
                // Check if tooltip is still bound, if not, rebind it
                if (!markerData.marker.getTooltip()) {
                    markerData.marker.bindTooltip(markerData.zoomLabel);
                }
                markerData.labelWasVisible = false; // Reset flag
            }
        });
    }, 100));

    // FIXED: Add drag events to preserve labels
    window.map.on('drag', throttle(function() {
        // Preserve labels during drag
        window.allMarkers.forEach(function(markerData) {
            if (markerData.hasZoomLabel && markerData.zoomLabel && !markerData.marker.getTooltip()) {
                markerData.marker.bindTooltip(markerData.zoomLabel);
            }
        });
    }, 50));

    console.log('🎯 Enhanced marker events initialized with professional handling');
}

/**
 * Auto-fit map to show all visible markers
 */
function fitMapToVisibleMarkers() {
    const visibleMarkers = window.allMarkers
        .filter(markerData => window.map.hasLayer(markerData.marker))
        .map(markerData => markerData.marker);

    if (visibleMarkers.length > 0) {
        const group = new L.featureGroup(visibleMarkers);
        window.map.fitBounds(group.getBounds().pad(0.1));
        console.log(`🎯 Map fitted to ${visibleMarkers.length} visible markers`);

        // Update labels after fitting
        setTimeout(() => {
            updateLabels();
        }, 300);
    }
}

/**
 * Update statistics display - FIXED
 */
function updateStatistics(filteredData) {
    // This function can be called to update statistics display
    // Implementation depends on your needs
    console.log('📊 Statistics updated for', filteredData.length, 'items');
}

/**
 * Compatibility functions
 */
function updateMarkers() {
    updateMarkersEnhanced();
}

// Basic throttle function
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

// Start initialization when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeEnhanced);
} else {
    initializeEnhanced();
}