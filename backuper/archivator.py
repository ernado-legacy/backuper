# coding=utf-8
import tarfile
import os

import log


def compress(input_folder, output_file, zip=False):
    """
    Compressing folder to file
    @param input_folder: Folder to compress
    @param output_file: output tar file
    @param zip: compress flag
    """
    mode = 'w'
    logger = log.get(__name__)
    logger.info('Starting compression of the folder %s' % input_folder)
    if not os.path.isdir(input_folder):
        raise IOError('%s is not folder or folder not found' % input_folder)
    if zip:
        mode = 'w:gz'
    tar = tarfile.open(output_file, mode)
    for name in os.listdir(input_folder):
        if os.path.isfile(name):
            tar.add(name)
    tar.close()
    logger.info('Folder %s compressed to file %s' % (input_folder, output_file))