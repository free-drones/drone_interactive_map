import utm


def utm_from_latlon(lat, lon):
    # Convert (lat, lon) to UTM coordinates
    return utm.from_latlon(lat, lon)

def utm_to_latlon(utm_x, utm_y, zone_number, zone_letter):
    # Convert UTM coordinates to (lat, lon)
    return utm.to_latlon(utm_x, utm_y, zone_number, zone_letter)

