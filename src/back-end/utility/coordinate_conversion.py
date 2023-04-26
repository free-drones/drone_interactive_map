import utm

"""
This file contains wrappers to convert between utm projected coordinates and latitude and longitude.

UTM (Universal Transverse Mercator) coordinates are a 2D Cartesian coordinate system that uses meters as its unit of measurement. 
    Therefore, you can treat UTM coordinates as a 2D Cartesian coordinate system and perform mathematical calculations accordingly, such as calculating distances and angles between points.
    This can simplify calculations that would be more complex when working with latitudes and longitudes.
    This method divides the earth into zones that are associated with and refered to using zone numbers and zone letters. When converting from latlon to utm coordinates these zone identifiers are derived and when converting to latlon they are required as input.
"""
def utm_from_latlon(lat, lon):
    """Convert (lat, lon) to UTM coordinates
        Returns utm_x (northing), utm_y (easting), zone_number, zone_letter
    """
    return utm.from_latlon(lat, lon)

def utm_to_latlon(utm_x, utm_y, zone_number, zone_letter):
    """Convert UTM coordinates to (lat, lon)
        Returns latitude, longitude
    """
    return utm.to_latlon(utm_x, utm_y, zone_number, zone_letter)

