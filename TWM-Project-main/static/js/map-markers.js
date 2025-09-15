// Fixed marker management with working zoom-based labels showing Messtelle names

/**
 * Add all markers to the map with proper zoom-based labels
 */
function addMarkersEnhanced() {
    const markersData = window.mapConfig.markersData;
    if (!markersData || markersData.length === 0) {
        console.log('No markers to add');
        return;
    }

    console.log('ðŸ”§ Adding markers with zoom labels to map:', markersData.length);
    window.allMarkers = [];

    markersData.forEach(function(data, index) {
        try {
            const categoryColors = window.mapConfig.categoryColors || {};
            const color = categoryColors[data.category] || '#0000FF';
            const clusterInfo = {
                is_clustered: data.is_clustered || false,
                cluster_size: data.cluster_size || 1
            };

            // Create icon
            let icon;
            if (typeof createMarkerIcon === 'function') {
                icon = createMarkerIcon(color, data.complete, clusterInfo);
            } else {
                // Fallback icon
                icon = L.divIcon({
                    html: `<div style="background-color: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
                    iconSize: [20, 20],
                    iconAnchor: [10, 10],
                    className: 'custom-div-icon'
                });
            }

            // Create marker
            const marker = L.marker(data.coordinates, { icon: icon });

            // Add popup
            const popupContent = typeof createPopupContent === 'function'
                ? createPopupContent(data)
                : `<strong>${data.label}</strong><br>Status: ${data.complete ? 'Complete' : 'Incomplete'}`;

            marker.bindPopup(popupContent, {
                maxWidth: 350,
                className: 'custom-popup'
            });

            // Add hover tooltip (always present) - shows full label on hover
            marker.bindTooltip(data.label, {
                permanent: false,
                direction: 'top',
                offset: [0, -25],
                className: 'hover-tooltip',
                interactive: false
            });

            // Store marker data with zoom label placeholder
            const markerData = {
                marker: marker,
                data: data,
                isVisible: true,
                hasZoomLabel: false,
                zoomLabel: null // Will be created when needed
            };

            window.allMarkers.push(markerData);
            window.map.addLayer(marker);
        } catch (error) {
            console.error('Error adding marker', index, ':', error);
        }
    });

    console.log('âœ… Markers added:', window.allMarkers.length);

    // Initialize zoom labels after all markers are added
    updateZoomLabels();
}

/**
 * Update markers visibility based on filters
 */
function updateMarkersEnhanced() {
    if (window.isUpdating) return;
    window.isUpdating = true;

    console.log('ðŸ”„ Updating markers...');

    // Get status filter values
    const showCompleteEl = document.getElementById('show-complete');
    const showIncompleteEl = document.getElementById('show-incomplete');

    const showComplete = showCompleteEl ? showCompleteEl.checked : true;
    const showIncomplete = showIncompleteEl ? showIncompleteEl.checked : true;

    let visibleCount = 0;
    const filteredData = [];

    window.allMarkers.forEach(function(markerData) {
        const data = markerData.data;
        let shouldShow = true;

        // Apply connected filters if the function exists
        if (typeof passesConnectedFilters === 'function') {
            if (!passesConnectedFilters(data)) {
                shouldShow = false;
            }
        }

        // Apply status filters
        if (!showComplete && data.complete) {
            shouldShow = false;
        }
        if (!showIncomplete && !data.complete) {
            shouldShow = false;
        }

        // Apply category filters
        if (!window.activeFilters.categories.includes(data.category)) {
            shouldShow = false;
        }

        // Update marker visibility
        if (shouldShow) {
            if (!markerData.isVisible) {
                window.map.addLayer(markerData.marker);
                markerData.isVisible = true;
            }
            visibleCount++;
            filteredData.push(data);
        } else {
            if (markerData.isVisible) {
                window.map.removeLayer(markerData.marker);
                // Remove zoom label if marker becomes invisible
                if (markerData.hasZoomLabel) {
                    removeZoomLabel(markerData);
                }
                markerData.isVisible = false;
            }
        }
    });

    console.log(`ðŸ‘ï¸ Showing ${visibleCount} of ${window.allMarkers.length} markers`);

    // Update UI
    const visibleCountEl = document.getElementById('visible-count');
    if (visibleCountEl) {
        visibleCountEl.textContent = visibleCount;
    }

    // Update statistics if the function exists
    if (typeof updateStatistics === 'function') {
        try {
            updateStatistics(filteredData);
        } catch (error) {
            console.warn('Statistics update failed:', error);
        }
    }

    // Update zoom labels after visibility changes
    updateZoomLabels();

    window.isUpdating = false;
}

/**
 * Update zoom-based labels based on current zoom level - Fixed to show Messtelle names
 */
function updateZoomLabels() {
    if (!window.map) return;

    const currentZoom = window.map.getZoom();
    const forceLabelsEl = document.getElementById('force-labels');
    const forceLabels = forceLabelsEl ? forceLabelsEl.checked : false;

    // Show labels at zoom 12+ or when forced
    const showLabels = currentZoom >= 12 || forceLabels;

    // Update UI elements
    const zoomLevelEl = document.getElementById('zoom-level');
    const labelInfoEl = document.getElementById('label-info');

    if (zoomLevelEl) zoomLevelEl.textContent = currentZoom;
    if (labelInfoEl) {
        labelInfoEl.textContent = showLabels ? 'Visible' : 'Hidden (zoom to 12+)';
    }

    console.log(`ðŸ” Zoom: ${currentZoom}, Force Labels: ${forceLabels}, Show Labels: ${showLabels}`);

    // Update labels for all visible markers
    window.allMarkers.forEach(function(markerData) {
        // Only process visible markers
        if (!markerData.isVisible) return;

        if (showLabels && !markerData.hasZoomLabel) {
            // Add zoom label
            addZoomLabel(markerData);
        } else if (!showLabels && markerData.hasZoomLabel) {
            // Remove zoom label
            removeZoomLabel(markerData);
        }
    });
}

/**
 * Add zoom label to a marker - Shows Messstelle column value
 */
function addZoomLabel(markerData) {
    try {
        const data = markerData.data;
        let labelText = '';

        // First priority: Use the actual Messstelle column value from Excel
        if (data.messstelle) {
            labelText = data.messstelle;
        }
        // Alternative spellings that might be in the data
        else if (data.Messstelle) {
            labelText = data.Messstelle;
        }
        else if (data.MESSSTELLE) {
            labelText = data.MESSSTELLE;
        }
        // Fallback: extract from label if Messstelle column not found
        else {
            const parts = data.label.split(' - ');
            if (parts.length >= 3) {
                labelText = parts[parts.length - 1].trim();
            } else {
                labelText = data.label;
            }
        }

        console.log('Adding zoom label for Messstelle:', labelText);

        // Create zoom label tooltip if it doesn't exist
        if (!markerData.zoomLabel) {
            markerData.zoomLabel = L.tooltip({
                permanent: true,
                direction: 'top',
                offset: [0, -35],
                className: 'zoom-label',
                opacity: 0.95,
                interactive: false
            }).setContent(labelText);
        } else {
            // Update content if label already exists
            markerData.zoomLabel.setContent(labelText);
        }

        // Remove any existing tooltips first
        markerData.marker.unbindTooltip();

        // Bind the zoom label (permanent)
        markerData.marker.bindTooltip(markerData.zoomLabel);
        markerData.hasZoomLabel = true;

        console.log('âœ… Zoom label added for Messstelle:', labelText);

    } catch (error) {
        console.error('Error adding zoom label:', error);
    }
}

/**
 * Remove zoom label from a marker and restore hover tooltip
 */
function removeZoomLabel(markerData) {
    try {
        console.log('Removing zoom label for:', markerData.data.label);

        // Unbind the zoom label
        if (markerData.hasZoomLabel) {
            markerData.marker.unbindTooltip();
            markerData.hasZoomLabel = false;
        }

        // Re-bind hover tooltip
        markerData.marker.bindTooltip(markerData.data.label, {
            permanent: false,
            direction: 'top',
            offset: [0, -25],
            className: 'hover-tooltip',
            interactive: false
        });

        console.log('âœ… Zoom label removed, hover tooltip restored');

    } catch (error) {
        console.error('Error removing zoom label:', error);
    }
}

/**
 * Initialize enhanced marker event listeners
 */
function initializeEnhancedMarkerEvents() {
    if (!window.map) return;

    // Zoom event with proper throttling
    window.map.on('zoomend', throttle(function() {
        console.log('ðŸ” Zoom ended, updating labels...');
        updateZoomLabels();
    }, 150));

    // Optional: Move event (commented out for better performance)
    // window.map.on('moveend', throttle(updateZoomLabels, 200));

    console.log('ðŸŽ¯ Enhanced marker events initialized');
}

/**
 * Toggle labels manually (force show/hide) - Fixed to work properly
 */
function toggleLabelsEnhanced() {
    console.log('ðŸ·ï¸ Toggling labels manually');

    // Get the current state of the checkbox
    const forceLabelsEl = document.getElementById('force-labels');
    if (forceLabelsEl) {
        console.log('Force labels checkbox state:', forceLabelsEl.checked);
    }

    // Update zoom labels immediately
    updateZoomLabels();
}

/**
 * Auto-fit map to show all visible markers
 */
function fitMapToVisibleMarkers() {
    const visibleMarkers = window.allMarkers
        .filter(markerData => markerData.isVisible)
        .map(markerData => markerData.marker);

    if (visibleMarkers.length > 0) {
        const group = new L.featureGroup(visibleMarkers);
        window.map.fitBounds(group.getBounds().pad(0.1));
        console.log(`ðŸŽ¯ Map fitted to ${visibleMarkers.length} visible markers`);

        // Update labels after fitting
        setTimeout(() => {
            updateZoomLabels();
        }, 300);
    }
}

/**
 * Get statistics for visible markers
 */
function getVisibleMarkersStats() {
    const visibleData = window.allMarkers
        .filter(markerData => markerData.isVisible)
        .map(markerData => markerData.data);

    return {
        total: visibleData.length,
        complete: visibleData.filter(item => item.complete).length,
        incomplete: visibleData.filter(item => !item.complete).length,
        customers: new Set(visibleData.map(item => item.kunde)).size,
        parameters: new Set(visibleData.map(item => item.parameter)).size,
        internal: visibleData.filter(item => item.pn_type === 'I').length,
        external: visibleData.filter(item => item.pn_type === 'E').length
    };
}

/**
 * Enhanced throttle function
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

// Override the original functions to use enhanced versions
window.addMarkers = addMarkersEnhanced;
window.updateMarkers = updateMarkersEnhanced;
window.toggleLabels = toggleLabelsEnhanced;
window.updateZoomLabels = updateZoomLabels;