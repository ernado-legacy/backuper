# coding=utf-8
import os
import ConfigParser
import log

from errors import BackupException

NAME = 'backuper'


def get_config():
    logger = log.get(__name__)
    config = ConfigParser.ConfigParser()
    for loc in os.curdir, os.path.expanduser("~"), "/etc/%s" % NAME, os.environ.get("%s_CONF" % NAME.upper()):
        filename = os.path.join(loc, "%s.conf" % NAME)
        try:
            with open(filename) as source:
                config.readfp(source)
                return config
        except IOError:
            logger.info('File %s not found' % filename)
    raise BackupException('Unable to find configuration file')