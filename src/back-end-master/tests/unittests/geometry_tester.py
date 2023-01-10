"""
Tests the geometry functions to make sure it works.
"""

import unittest
from utility.helper_functions import is_overlapping, polygon_contains_point

class TestGeometry(unittest.TestCase):
    def test_is_overlapping(self):
        square1 = [(5,0),(5,5),(10,5),(10,0)]
        square2 = [(0,0),(0,10),(10,10),(10,0)]
        square3 = [(15,0),(15,5),(20,5),(20,0)]
        square4 = [(9,9),(9,15),(15,15),(15,9)]
        square5 = [(10,-5), (10,2), (16,-5), (16,2)]

        # Test with square1 with respect to every other.
        self.assertTrue(is_overlapping(square1,square2)) # Yes
        self.assertFalse(is_overlapping(square1,square3)) # No
        self.assertFalse(is_overlapping(square1,square4)) # No
        self.assertTrue(is_overlapping(square1,square5)) # Yes

        # Test with square2 with respect to every other.
        self.assertTrue(is_overlapping(square2,square1)) # Yes
        self.assertFalse(is_overlapping(square2,square3)) # No
        self.assertTrue(is_overlapping(square2,square4)) # Yes
        self.assertTrue(is_overlapping(square2,square5)) # Yes

        # Test with square3 with respect to every other.
        self.assertFalse(is_overlapping(square3,square1)) # No
        self.assertFalse(is_overlapping(square3,square2)) # No
        self.assertFalse(is_overlapping(square3,square4)) # No
        self.assertTrue(is_overlapping(square3,square5)) # Yes

        # Test with square4 with respect to every other.
        self.assertFalse(is_overlapping(square4,square1)) # No
        self.assertTrue(is_overlapping(square4,square2)) # Yes
        self.assertFalse(is_overlapping(square4,square3)) # No
        self.assertFalse(is_overlapping(square4,square5)) # No

        # Test with square5 with respect to every other.
        self.assertTrue(is_overlapping(square5,square1)) # Yes
        self.assertTrue(is_overlapping(square5,square2)) # Yes
        self.assertTrue(is_overlapping(square5,square3)) # Yes
        self.assertFalse(is_overlapping(square5,square4)) # No

    def test_polygon_contains_point(self):
        square1 = [(5,0),(5,5),(10,5),(10,0)]
        point1 = (8,3)   # Yes
        point2 = (5.1,1) # Yes
        point3 = (6,1)   # Yes
        point4 = (6,-1)  # No
        point5 = (9,6)   # No
        point6 = (8,-1)  # No
        point7 = (5,1)   # No
        self.assertTrue(polygon_contains_point(point1, square1))
        self.assertTrue(polygon_contains_point(point2, square1))
        self.assertTrue(polygon_contains_point(point3, square1))
        self.assertFalse(polygon_contains_point(point4, square1))
        self.assertFalse(polygon_contains_point(point5, square1))
        self.assertFalse(polygon_contains_point(point6, square1))
        self.assertFalse(polygon_contains_point(point7, square1))
        pass

if __name__ == "__main__":
    unittest.main()
