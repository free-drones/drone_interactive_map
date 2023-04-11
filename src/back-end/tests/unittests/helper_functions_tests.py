import unittest
import os
import utility.helper_functions as hf

class TestHelper(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_path_from_root_test(self):
        """ 
        Tries to convert a path written relative to project root, to path relative 
        to system root and checks if resulting path is valid. 
        """
        path = hf.get_path_from_root("/utility/helper_functions.py")
        self.assertTrue(os.path.exists(path))

if __name__ == "__main__":
    unittest.main()