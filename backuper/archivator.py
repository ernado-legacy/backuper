# coding=utf-8
import tarfile
import os
from datetime import datetime
from subprocess import call

import log
import errors


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

