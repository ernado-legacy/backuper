# coding=utf-8
from datetime import datetime
import os
from ftplib import FTP
from ftplib import all_errors as ftp_all_errors

import errors
from files import format_size


def upload_files(file_list, cfg, logger):
    """
    Upload list of files to pre-configurated server
    @param file_list: upload file list with full paths
    @param cfg: ParseConfig object
    """
    start_time = datetime.now()
    root = cfg.get('ftp', 'root')
    uploads = dict(zip(file_list, map(lambda x: os.path.join(root, os.path.basename(x)), file_list)))
    logger.info('Uploading files: %s' ' '.join(uploads.values()))
    total_size = 0
    # Checking files and counting
    for f in uploads:
        if not os.path.isfile(f):
            logger.critical('Unable to find file %s, unable to complete backup' % f)
            raise errors.BackupException('File not found: %s' % f)
        total_size += os.path.getsize(f)
    logger.info('Total size: %s' % format_size(total_size))
    try:
        logger.info('Connecting to %s' % cfg.get('ftp', 'host'))
        ftp = FTP(cfg.get('ftp', 'host'), cfg.get('ftp', 'user'), cfg.get('ftp', 'password'))
        logger.info('Connected, starting upload')
        map(lambda filename: ftp.storbinary('STOR %s' % uploads[filename], open(filename)), uploads.keys())
        elapsed_seconds = (datetime.now() - start_time).seconds
        if elapsed_seconds != 0:
            logger.info('Uploaded by %s seconds, speed: %s/s' % (elapsed_seconds, format_size(total_size/elapsed_seconds)))
        else:
            logger.info('Uploaded by zero seconds')
        ftp.close()
    except ftp_all_errors as e:
        logger.critical('Unable to complete ftp upload: %s' % e)
        raise errors.BackupException('Critical FTP error: %s' % e)