# coding=utf-8
import tarfile
import os
from datetime import datetime
from subprocess import call

import log
import errors


def compress_file(input_file, output_file):
    """
    Compressing folder to file
    @param input_folder: Folder to compress
    @param output_file: output tar file
    @param zip: compress flag
    """
    mode = 'w'
    logger = log.get(__name__)
    logger.info('Starting compression of the %s' % input_file)
    if not os.path.isfile(input_file):
        raise IOError('%s is not file or not found' % input_file)
    mode = 'w:gz'
    tar = tarfile.open(output_file, mode)
    tar.add(input_file)
    tar.close()
    logger.info('File %s compressed to file %s' % (input_file, output_file))


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
        full_name = os.path.join(name, output_file)
        logger.info('Archiving file %s' % name)
        if os.path.isfile(full_name):
            tar.add(full_name)
    tar.close()
    logger.info('Folder %s compressed to file %s' % (input_folder, output_file))


def incremental_compress(input_folder, output_file, incremental_list_file):
    logger = log.get(__name__)
    tar_call_arguments = ['tar', '--create', '--verbose',
                          '--preserve-permissions', '--ignore-failed-read',
                          '--one-file-system', '--recursion', '--totals']

    start_time = datetime.now()
    logger.info('Archiving to %s' % output_file)
    result = call(tar_call_arguments + ['--listed-incremental=%s' % incremental_list_file,
                                        '--file=%s' % output_file,
                                        input_folder])
    if result == 0:
        logger.info('Archiving completed by %s seconds' % (datetime.now() - start_time).seconds)
    else:
        logger.critical('Failed to archive %s' % input_folder)
        raise errors.BackupException('Archiving failed')

