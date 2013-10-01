# coding=utf-8
from datetime import datetime
import os
from ftplib import FTP
from ftplib import all_errors as ftp_all_errors

import errors
import log
import config


def upload(filename, external_filename, cfg=None):
    """
    Uploads to ftp created backup file
    """
    logger = log.get(__name__)
    logger.info('Upload initialized')

    if cfg is None:
        cfg = config.get_config()

    start_time = datetime.now()
    try:
        if os.path.isfile(filename):
            logger.info('Connecting to %s' % cfg.get('ftp', 'host'))
            ftp = FTP(cfg.get('ftp', 'host'), cfg.get('ftp', 'user'), cfg.get('ftp', 'password'))
            logger.info('Connected, starting upload')
            size = os.path.getsize(filename) / (1024 * 1024.0)
            logger.info('Uploading %s MB backup' % size)
            ftp.storbinary('STOR %s' % external_filename, open(filename))
            logger.info('Uploaded by %s seconds' % (datetime.now() - start_time).seconds)
            ftp.close()
        else:
            logger.critical('Unable to find file %s, unable to complete backup' % filename)
            raise errors.BackupException('NOT FOUND: %s' % filename)
    except ftp_all_errors, e:
        logger.critical('Unable to complete ftp upload: %s' %  e)
        raise errors.BackupException('[Error 4] FTP ERROR - %s' % e)
    logger.info('Upload complete')