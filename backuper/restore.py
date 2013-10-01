# coding=utf-8
import datetime

from backup import get_backup_index


def find_backup_sequence(project, day, month, year=None):
    if year is None:
        year = datetime.datetime.now().year
    s = [get_backup_index(project, 1, month, year)]

    for day_number in range(1, day + 1):
        s.append(get_backup_index(project, day, month, year))

    return map(lambda x: '%s.tar' % x, s)
