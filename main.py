import jsonargparse
from anonymize import anonymize
import turicreate as tc
import os
import warnings
import numpy as np
import pandas as pd
import time
import ray
import utils

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings('ignore')
# ray.init()
def run_anonymization(config):
    """
    Given a list of paths of all PDF and TIFF files, performs following operations :
        1. Parse arguments. From list of paths, generate batches.
        2. Start processing each batch.
            Save at --PATH_TO_SAVE_DIR batchwise and update logs.sframe with | 'paths' | 'plates' | 'faces' |
            (logs.sframe also saved at --PATH_TO_SAVE_DIR

    -----------------------------------------------------------
    :param
    -----------------------------------------------------------
        -- config: parsed arguments from CMD
           --path_to_main_dir  -- str, Path to main directory where PDF's and TIFF's are stored
           --BATCH_SIZE -- int, optional (default = 16)
                    Batch size (Number of files) for each epoch of anonymization
           --PATH_TO_PLATE_DETECTION_MODEL   - str, optional
                    Path to license plate detection model
           --VERBOSE - bool, optional (default = True)
                    Print debugging messages
           --SAVE_ANONYMIZED - bool, optional (default = True)
    -----------------------------------------------------------
    :return: Saves the masked images at save folder.
    -----------------------------------------------------------
    """
    start_time = time.time()
    tc.config.set_num_gpus(-1)    # set gpu
    _anonymize = anonymize(config)  # initialize anonymize.py
    car_model = tc.load_model(config.path_to_car_model)
    paths = set(utils.load_paths(config.path_to_main_dir))  # load all paths
    print("Creating log dir at - " + config.path_to_save_logs + '/logs/')
    # 1. check if logs exists. creating logs.csv and dir for saving masked pdf images.
    save_folder, logs_folder = utils.create_destination_dirs(config)

    # 2. Read existing files
    logs_df = pd.read_csv(logs_folder + 'logs.csv')
    done_paths = set(logs_df.path)
    todo_paths = list(paths.difference(done_paths))  # final list of remaining paths
    print("Processing total", len(todo_paths), "files")
    # evaluating memory requirements:
    mem_req = utils.get_size(todo_paths)
    print("Total size of all files found > ", mem_req, "MegaBytes.")
    print("Min. available storage required is", mem_req, "MegaBytes.")

    # 3. Loop for main steps (iterating over list of batches)
    # a = len(todo_paths)  # Keeps a count of batches - using as UID
    logs_placeholder = {}
    for i in todo_paths:    # path of one file
        print('processing file', i)
        # a += 1
        # 3.1 Stripping (str) file format and file_name from file.
        file_format = i.split('/')[-1].split('.')[-1]
        file_name = i.split('/')[-1].split('.')[0]     # use maybe for UID
        # extracting images from PDF/TIFF
        if file_format == 'PDF' or file_format == 'pdf':
            pil_images = utils.pdf2images(i)
            pil_images = [i for i in pil_images if i.size != (600, 207)]  # removes dekra, but better retrain car model
            pil_images = [i for i in pil_images if i.size[1] >= 60] # removes bar codes etc

        if file_format == 'tiff':
            pil_images = utils.read_tiff(i)
        # car no car filter
        sframe_temp = tc.SFrame({'image': [utils.from_pil_image(im) for im in pil_images], 'index': np.arange(len(pil_images))})

        # this is to except some error from certain blank PDFS
        try:
            sframe_temp['predictions'] = car_model.predict(sframe_temp)
        except RuntimeError:
            continue
        cars = sframe_temp.filter_by(['car'], 'predictions')
        car_indices = cars['index']
        # final inputs to anonymize
        car_images = cars['image']   # graphlab images for turicreate model
        cv2_images = [utils.pil2cv2(pil_images[im]) for im in car_indices]  # cv2 images for mtcnn
        # batch generator
        batches_graphlab = utils.chunk_generator(car_images, batch_size=config.BATCH_SIZE)   # graphlab images.
        batches_cv2 = utils.chunk_generator(cv2_images, batch_size=config.BATCH_SIZE)        # cv2 images - This
        #   is highly inefficient(== mtcnn()). Please suggest/edit improvements.
        del car_images, cv2_images, sframe_temp
        for k, l in zip(batches_graphlab, batches_cv2):
            sfr = tc.SFrame({'images': k})
            # 3.2 Predict faces and licence plates for the batch.

            sarray = _anonymize.predict_plates_faces(sfr, l)
            # saving logs for a file and append the clean the dict
            logs_placeholder['path'] = i
            logs_placeholder['annotations'] = sarray
            # 3.3 Saving batch results  into sframe (logs) - | 'paths' | 'annotations' |
            sfr['annotations'] = sarray
            # Load image to memory temporarily, clear after saving (batch-wise)
            # 3.4 Saving image_objects at PATH_TO_SAVE_DIR.
            if config.SAVE_ANONYMIZED:
                _anonymize.save_masked_images(sfr,file_name)
            del sfr
        # save everything from here if until here is successful
        logs_df = logs_df.append(logs_placeholder, ignore_index=True)
        logs_df.to_csv(logs_folder + 'logs.csv', index=False)
        logs_placeholder = {}

        print("Total script runtime so far --- %s seconds ---" % (time.time() - start_time))

    if config.SAVE_ANONYMIZED:  # printing path to saved folder
        print('All anonymized images saved at ->', config.path_to_main_dir + '/anonymized_images/')

if __name__ == '__main__':
    parser = jsonargparse.ArgumentParser()
    parser.add_argument('--path_to_main_dir', type=str, help='path to dir where images are stored')
    parser.add_argument('--path_to_save_dir', type=str, help='path to dir where masked images are saved')
    parser.add_argument('--path_to_save_logs', type=str, help='path to dir where logs are saved')

    parser.add_argument('--BATCH_SIZE', default=16, type=int, help='Batch size to process images')
    parser.add_argument('--PATH_TO_PLATE_DETECTION_MODEL',
                        default='models/license_plate_detection/plate_detection_model_1804.model', type=str,
                        help='Path to plates detection model')
    parser.add_argument('--path_to_car_model', default='models/20191117_500iters_v2.model')
    parser.add_argument('--VERBOSE', default=True, type=bool, help='Show progress in console')
    parser.add_argument('--SAVE_ANONYMIZED', default=True, type=bool, help='Whether to save anonymized images or not')
    # parse arguments and initialize precessing by calling run_anonymization(config)
    config = parser.parse_args()
    run_anonymization(config)
