# coding=utf-8
import os
import ConfigParser

from exceptions import BackupException

NAME = 'backuper'


def get_config():
    config = ConfigParser.ConfigParser()
    for loc in os.curdir, os.path.expanduser("~"), "/etc/%s" % NAME, os.environ.get("%s_CONF" % NAME.upper()):
        try:
            with open(os.path.join(loc, "%s.conf" % NAME)) as source:
                config.readfp(source)
                return config
        except IOError:
            raise BackupException('Unable to find configuration file')