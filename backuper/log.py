# coding=utf8
import logging

__ch = logging.StreamHandler()
__ch.setLevel(logging.INFO)
__formatter = logging.Formatter('%(asctime)s [%(levelname)s] <%(name)s> %(message)s', r'%d.%m.%y %H:%M:%S')
__ch.setFormatter(__formatter)


def get(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(__ch)
    return logger