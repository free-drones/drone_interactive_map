/**
 * Utility functions for map.
 */

/**
 * Formats collection of bounds into a view object.
 */
export function viewify( bounds ) {
    // latlng objects
    const nw = bounds.getNorthWest();
    const ne = bounds.getNorthEast();
    const sw = bounds.getSouthWest();
    const se = bounds.getSouthEast();
    const center = bounds.getCenter();

    // List of coordinate pairs to be stored by state.
    const view = {
        upLeft: {
            lat: nw.lat,
            lng: nw.lng
        },
        upRight: {
            lat: ne.lat,
            lng: ne.lng
        }, 
        downLeft: {
            lat: sw.lat,
            lng: sw.lng
        }, 
        downRight: {
            lat: se.lat,
            lng: se.lng
        }, 
        center: {
            lat: center.lat,
            lng: center.lng
        }
    };

    return(view);
}

export default { viewify };
