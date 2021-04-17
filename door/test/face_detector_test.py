import unittest
from detection.face_detector import FaceDetector


class FaceDetectorTestCase(unittest.TestCase):

    def test_detect_positive(self):
        photo = 'images/cap1.jpg'
        c = FaceDetector()
        self.assertEqual(c.detect_face_from_file(photo), True)

    def test_detect_negative1(self):
        photo = 'images/phonepic1.jpg'
        c = FaceDetector()
        self.assertEqual(c.detect_face_from_file(photo), False)

    def test_detect_negative2(self):
        photo = 'images/phonepic2.jpg'
        c = FaceDetector()
        self.assertEqual(c.detect_face_from_file(photo), False)

    def test_detect_negative3(self):
        photo = 'images/framepic1.jpg'
        c = FaceDetector()
        self.assertEqual(c.detect_face_from_file(photo), False)

    def test_compare(self):
        src = 'images/cap1.jpg'
        tgt = 'images/Joe-Benczarski.jpg'
        c = FaceDetector()
        self.assertEqual(c.compare_face_from_file(src, tgt), True)


if __name__ == '__main__':
    unittest.main()
