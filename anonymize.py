"""Import libraries"""
import turicreate as tc
import os
# import numpy as np
from mtcnn.mtcnn import MTCNN
import _visualization
import warnings
# import ray

warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
"""Load all models - load only once, then process sframes in batches"""

# # ray.init()
# @ray.remote
class anonymize():

    def __init__(self, config):
        """
        Saves masked versions of images extracted from one pdf file to /anonymized_images/ dir.
    -----------------------------------------------------------
        :param
            config: parameters from stdin
                --path_to_main_dir  - path to dir where images are stored
                --path_to_save_dir - path to dir where masked images are saved
                --path_to_save_logs - path to dir where logs are saved
                --BATCH_SIZE - Batch size to process images
                --PATH_TO_PLATE_DETECTION_MODEL - Path to plates detection model
                --VERBOSE Show progress in console
                --SAVE ANONYMIZED - Whether to save anonymized images or not
    -----------------------------------------------------------
        INPUT - pdf or tiff file.
        ACTIONS - Methods in main.py.
            1. Read PDF or tiff
            2. Extract images
            3. Split images in batches
            4. Run face and plates detection on images (batch-wise).
            5. Saves images fro,m input file to anonimyzied_images/dir with dir == name of pdf/tiff file
            6. Save logs Sframe at logs/logs.sframe of all completed pdf/tiff paths with a UID.
        OUTPUT - Run face and plates detection model and saves the masked images to a destination directory
    -----------------------------------------------------------
        : returns
        Saves masked versions of images extracted from one pdf file to /anonymized_images/ dir.
    -----------------------------------------------------------
        """
        self.image_dir_path = config.path_to_main_dir
        self.save_dir = config.path_to_save_dir
        self.BATCH_SIZE = config.BATCH_SIZE
        self.plate_detection_model = self._load_turicreate_model(config.PATH_TO_PLATE_DETECTION_MODEL)
        self.face_detection_model = self._load_face_detection_model()
        self.VERBOSE = config.VERBOSE

    def _load_turicreate_model(self, path):
        """
        Loads any turicreate model from path
        :param
            Path to plate detection model
        :return
            Model object (instance)
        """
        return tc.load_model(path)

    def _load_face_detection_model(self):
        """
        Load face detection model from MTCNN.
        :param default
        :return Model object (instance)
        """
        return MTCNN()

    def predict_plates_faces(self, sframe, cv2images):
        """
        Run predictions on a batch. Returns plates and face coordinates
    -----------------------------------------------------------
        :param
            sframe : sframe with 'images' - accepted format for turicreate model
            pil_images : PIL images - accepted format for MTCNN model
    -----------------------------------------------------------
        :return
            SArray - annotations)
    -----------------------------------------------------------
        """
        faces_coords = [self.face_detection_model.detect_faces(cv2images[i]) for i in range(len(cv2images))]
        plates_coords = self.plate_detection_model.predict(sframe['images'], verbose=self.VERBOSE)

        # extracting only the coordinates from returned dicts
        faces = [[{'label': 'faces',
                   'coordinates': {'x': j['box'][0],
                                   'y': j['box'][1],
                                   'width': j['box'][2],
                                   'height': j['box'][3]
                                   }} for j in i] for i in faces_coords]  # needed to convert to turicreate format of dict.
        plates = [[j for j in i] for i in plates_coords]
        return tc.SArray([i + j for i, j in zip(plates, faces)])


    def save_masked_images(self, sframe, file_name):
        """
        Saves masked images at '/anonimyzed_images/' dir
        :param sframe: SFrame with following columns | 'images' | 'annotations'  .
                       len(sframe) must be equal to total number of images extracted from PDF/TIFF.
        :param file_name: PDF/TIFF filename to create a DIR.
                          Hence, all images from a PDF/TIFF file are stored in a DIR with name == file_name
        :return:
        Saves the masked images at  '/anonymized/file_name/pic_count.jpg'
        """
        blurred_image = _visualization.draw_bounding_boxes(sframe['images'], sframe['annotations'])
        try:
            os.mkdir(self.save_dir + '/anonymized_images/' + file_name + '/')
        except FileExistsError:
            pass
        for i, j in enumerate(blurred_image):
            j.save(''.join([self.save_dir, '/anonymized_images/', file_name, '/', str(i), '.jpg']))
