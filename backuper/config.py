# coding=utf-8
import os
import ConfigParser
import log

from errors import BackupException

NAME = 'backuper'


def get_config():
    logger = log.get(__name__)
    logger.info('Getting config')
    config = ConfigParser.ConfigParser()
    for loc in os.path.expanduser("~"), "/etc/%s" % NAME, os.environ.get("%s_CONF" % NAME.upper()):
        filename = os.path.join(loc, "%s.conf" % NAME)
        try:
            with open(filename) as source:
                config.readfp(source)
                logger.info('Loading config %s' % filename)
                return config
        except IOError:
            logger.debug('File %s not found' % filename)
    raise BackupException('Unable to find configuration file')