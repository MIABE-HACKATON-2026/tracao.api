import json
from shapely.geometry import Polygon, shape
from pyproj import Geod

class GISService:
    @staticmethod
    def calculate_area(gps_coordinates):
        """
        gps_coordinates: list of [lat, lon] or [lon, lat]
        Returns area in hectares.
        """
        try:
            # Assuming coordinates are [lon, lat] for GeoJSON standard
            # If they are [lat, lon], we need to flip them.
            poly = Polygon(gps_coordinates)
            geod = Geod(ellps="WGS84")
            area_m2, perimeter = geod.geometry_area_perimeter(poly)
            return abs(area_m2) / 10000.0  # m2 to hectares
        except Exception as e:
            print(f"Error calculating area: {e}")
            return 0.0

    @staticmethod
    def check_overlap(new_coords, existing_parcels_coords):
        """
        new_coords: list of coords for the new parcel
        existing_parcels_coords: list of lists of coords
        Returns True if there is an overlap.
        """
        try:
            new_poly = Polygon(new_coords)
            for coords in existing_parcels_coords:
                existing_poly = Polygon(coords)
                if new_poly.intersects(existing_poly):
                    # Check if the intersection is more than just a point/line
                    if new_poly.intersection(existing_poly).area > 1e-9:
                        return True
            return False
        except Exception as e:
            print(f"Error checking overlap: {e}")
            return False
