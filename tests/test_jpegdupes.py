import unittest
import os, shutil
# from jpegdupes import jpegdupes
import jpegdupes.jpegdupes

class TestFilterFolder(unittest.TestCase):

    LIBRARY_DIR = "tests/library"
    TOFILTER_DIR = "tests/tofilter"
    IMAGES_DIR = "tests/images"

    @classmethod
    def setUpClass(cls):
        os.makedirs(cls.LIBRARY_DIR)
        os.makedirs(cls.TOFILTER_DIR)
        for img in ("/donatello.jpg", "/Raphael.jpeg", "/mikey.jpg"):
            shutil.copy2(cls.IMAGES_DIR + img, cls.LIBRARY_DIR)
        for img in ("/donatello2.jpg", "/Raphael2.jpeg", "/leo.jpg", "/mikey.jpg"):
            shutil.copy2(cls.IMAGES_DIR + img, cls.TOFILTER_DIR)


    @classmethod
    def tearDownClass(cls):
        # return
        shutil.rmtree(cls.LIBRARY_DIR)
        shutil.rmtree(cls.TOFILTER_DIR)


    def test_ok(self):
        tofilter = self.TOFILTER_DIR
        library = self.LIBRARY_DIR
        print(dir(jpegdupes))

        jpegdupes.jpegdupes.filterfolder(tofilter, library)
        # for img in ("/donatello2.jpg", "/Raphael2.jpeg", "/mikey.jpg"):
            # os.remove(self.TOFILTER_DIR + img)

        self.assertTrue(os.path.isfile(self.TOFILTER_DIR + "/leo.jpg"))
        for img in ("/donatello2.jpg", "/Raphael2.jpeg", "/mikey.jpg"):
            self.assertFalse(os.path.isfile(self.TOFILTER_DIR + img), img)