import boto3
import botocore.exceptions
import logging


class FaceDetector(object):

    def __init__(self):
        self.client = boto3.client('rekognition')

    def detect_face_from_bytes(self, img_bytes):
        try:
            response = self.client.detect_labels(Image={'Bytes': img_bytes})
            labels = response.get('Labels')
            return (1 - self.counterfeit_confidence_(labels)) * self.human_face_confidence_(labels)
        except botocore.exceptions.ClientError:
            logging.info(f"client error - check credentials")
            return 0

    def detect_face_from_file(self, img_fp):
        try:
            with open(img_fp, 'rb') as img:
                response = self.client.detect_labels(Image={'Bytes': img.read()})
            labels = response.get('Labels')
            return (1 - self.counterfeit_confidence_(labels)) * self.human_face_confidence_(labels)
        except botocore.exceptions.ClientError:
            logging.info(f"client error - check credentials")
            return 0

    def compare_face_from_bytes(self, src_bytes, tgt_bytes, threshold):
        try:
            response = self.client.compare_faces(SourceImage={'Bytes': src_bytes},
                                             TargetImage={'Bytes': tgt_bytes},
                                             SimilarityThreshold=threshold)
            matches = response.get('FaceMatches')
            return len(matches) > 0
        except botocore.exceptions.ClientError:
            logging.info(f"client error - check credentials")
            return 0

    def compare_face_from_file(self, source, target, threshold):
        try:
            with open(source, 'rb') as source_img:
                with open(target, 'rb') as target_img:
                    response = self.client.compare_faces(SourceImage={'Bytes': source_img.read()},
                                                         TargetImage={'Bytes': target_img.read()},
                                                         SimilarityThreshold=threshold)
            matches = response.get('FaceMatches')
            return len(matches) > 0
        except botocore.exceptions.ClientError:
            logging.info(f"client error - check credentials")
            return 0

    def human_face_confidence_(self, labels):
        human_conf = self.get_confidence_(labels, 'Name', 'Human')
        face_conf = self.get_confidence_(labels, 'Name', 'Face')
        return human_conf * face_conf

    def counterfeit_confidence_(self, labels):
        elec_conf = self.get_confidence_(labels, 'Name', 'Electronics')
        mon_conf = self.get_confidence_(labels, 'Name', 'Monitor')
        phone_conf = self.get_confidence_(labels, 'Name', 'Phone')
        if elec_conf > 0.50 or mon_conf > 0.50 or phone_conf > 0.50:
            return 1
        else:
            return 0

    def get_confidence_(self, entries, key, value):
        idx = self.try_index_(entries, key, value)
        if idx:
            confidence = entries[idx]['Confidence']
        else:
            confidence = 1e-1
        return confidence / 1e2

    @staticmethod
    def try_index_(entries, key, value):
        try:
            idx = [e[key] == value for e in entries].index(True)
        except ValueError:
            idx = None
        return idx
