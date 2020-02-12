import glob
import os
import fitz
import PIL as P
import io
import numpy as np
import turicreate as tc
import pandas as pd
def load_paths(path):
    """
    Loads pdf and tiff files from the root folder as a 1-D list.
    -----------------------------------------------------------
    :param
        path: str, path of the root dir where to for PDF and TIFFs
    -----------------------------------------------------------
    :return: list with all pdf and tiffs found
    note -  Debug here - if extra pdfs are there in the folder, getting an idea about a UID will be helpful!
    """
    paths = glob.glob(path + '/**', recursive=True)
    pdfs = [i for i in paths if ('.pdf') in i]
    pdfs_ = [i for i in paths if ('.PDF') in i]
    tiff = [i for i in paths if ('.tiff') in i]
    final_list = np.hstack((pdfs, pdfs_, tiff))
    print("Total of %d files were found"% len(final_list))
    return final_list


def chunk_generator(l, batch_size):
    """
    Given any list and a batch size, returns a list of lists where each element is a list containing
    N (BATCH_SIZE) elements.
    -----------------------------------------------------------
    :param
        l: a 1-D list
        batch_size: Batch size of a chunk
    -----------------------------------------------------------
    :return: list of lists of batches
    """
    chunks = [l[i:i + batch_size] for i in range(0, len(l), batch_size)]
    return chunks


def get_size(all_paths):
    """
    Returns the size of a file given a path. If list is given returns the size of all files.
    -----------------------------------------------------------
    :param
        all_paths: list of paths of files to calculate size
    -----------------------------------------------------------
    :return:
        Size of file(s) in MegaBytes
    """
    total_size = 0
    for i in all_paths:
        total_size += os.path.getsize(i)
    return total_size / 1024000


def read_tiff(path):
    """
    Returns a list of image objects given a .tiff file.
    -----------------------------------------------------------
    :param
        path: path to a tiff file
    -----------------------------------------------------------
    :return:
        List of image objects from tiff  ( number of images = number of pages in tiff)
    """
    # img = P.Image.open(path)
    # for i in range(img.n_frames):    # splitting tiff pages
    #     img.seek(i)
    #     img.save('tiff_temp/image_%s.jpg'%(i,))
    img = P.Image.open(path)
    images = []
    for i in range(img.n_frames):
        img.seek(i)
        images.append(P.Image.fromarray(np.array(img)))
    return images



def pdf2images(path):
    """
    Returns a list of image objects from pdf.
    -----------------------------------------------------------
    :param
        path: path to pdf file
    -----------------------------------------------------------
    :return:
        list of image objects from the pdf
    """
    doc = fitz.open(path)
    # lenXREF = doc._getXrefLength()
    images = []
    for i in range(len(doc)):
        imglist = doc.getPageImageList(i)
        for img in imglist:
            xref = img[0]  # xref number
            pix = fitz.Pixmap(doc, xref)  # make pixmap from image
            if pix.n < 5:  # can be saved as PNG
                images.append(bytes_to_image(pix.getPNGData()))
            else:  # must convert CMYK first
                pix0 = fitz.Pixmap(fitz.csRGB, pix)
                images.append(bytes_to_image(pix0.getPNGData()))
                pix0 = None  # free Pixmap resources
            pix = None  # free Pixmap resources
    return images


def bytes_to_image(image_bytes):
    """
    Converts byte image to a PIL image object.
    -----------------------------------------------------------
    :param
        image_bytes: image in Bytes format
    -----------------------------------------------------------
    :return:
        PIL image
    """
    imgstream = io.BytesIO(image_bytes)
    imageFile = P.Image.open(imgstream)
    return imageFile


def create_destination_dirs(config):
    """
    Creates logs and save dirs
    -----------------------------------------------------------
    :param
        config: config for initializing anonymize()
    -----------------------------------------------------------
    :return:
        tuple (str,str) - (path to save dir, path to logs dir)
    """
    try:
        save_folder = os.mkdir(config.path_to_save_dir + '/anonymized_images/')
    except FileExistsError:
        save_folder = config.path_to_save_dir + '/anonymized_images/'
    try:
        logs_folder = os.mkdir(config.path_to_save_logs + '/logs/')
        logs_df = pd.DataFrame(columns=['path', 'annotations'])
        logs_df.to_csv( config.path_to_save_logs + '/logs/' + 'logs.csv',index=False)
    except FileExistsError:
        logs_folder = config.path_to_save_logs + '/logs/'

    return config.path_to_save_dir + '/anonymized_images/', config.path_to_save_logs + '/logs/'


def from_pil_image(pil_img):
    """
    Returns a graphlab.Image constructed from the passed PIL Image
    -----------------------------------------------------------
    Parameters
    -----------------------------------------------------------
        pil_img : PIL.Image
            A PIL Image that is to be converted to a graphlab.Image
    -----------------------------------------------------------
    Returns
        out: graphlab.Image
            The input converted to a graphlab.Image
    -----------------------------------------------------------
    """
    # Read in PIL image data and meta data
    height = pil_img.size[1]
    width = pil_img.size[0]
    _format = {'JPG': 0, 'PNG': 1, 'RAW': 2, 'UNDEFINED': 3}

    if pil_img.mode == 'L':
        image_data = bytearray([z for z in pil_img.getdata()])
        channels = 1
    elif pil_img.mode == 'RGB':
        image_data = bytearray([z for l in pil_img.getdata() for z in l ])
        channels = 3
    else:
        image_data = bytearray([z for l in pil_img.getdata() for z in l])
        channels = 4
    format_enum = _format['RAW']
    image_data_size = len(image_data)

    # Construct a tc.Image
    img = tc.Image(_image_data=image_data,
                   _width=width,
                   _height=height,
                   _channels=channels,
                   _format_enum=format_enum,
                   _image_data_size=image_data_size)
    return img

def pil2cv2(pil_image):
    """
    Returns a cv2 image given a PIL image object. (If input image has 2 channels, then converts into three channels)
    -----------------------------------------------------------
    :param
        pil_image:  PIL image format
    -----------------------------------------------------------
    :return:
        cv2 image
    """
    open_cv_image = np.array(pil_image)
    # Convert RGB to BGR
    try:
        open_cv_image = open_cv_image[:, :, ::-1].copy()
    except IndexError:
        pass
    if len(open_cv_image.shape) == 2:
        reshaped_img = np.stack((open_cv_image,)*3, axis=-1)
        return reshaped_img
    else:
        return open_cv_image