# coding=utf-8
import os
import datetime

from errors import BackupException, ProjectException
from config import get_config
import log


class TYPES(object):
    """
    Types of backup
    """
    daily = 'daily'
    monthly = 'monthly'
    _types = (daily, monthly)

    def __contains__(self, item):
        if item in self._types:
            return True
        return False


def get_backup_index(project, day, month, year=None):
    """
    @param project: Name of the project
    @return: backup unique index
    """
    assert type(project) is str
    assert type(day) is int
    assert type(month) is int
    assert type(year) is int

    if year is None:
        year = datetime.datetime.now().year

    t = get_backup_type(day)[0]

    return '{project}-{t}-{d:0>1}-{m:0>1}-{y}'.format(project=project,
                                                      t=t,
                                                      d=day,
                                                      m=month,
                                                      y=str(year)[-2:])


def get_current_index(project):
    now = datetime.datetime.now()
    return get_backup_index(project, now.day, now.month, now.year)


def get_backup_type(day=None):
    if day is None:
        day = datetime.datetime.now().day
    if day == 1:
        return TYPES.monthly
    return TYPES.daily


class Project(object):
    def __init__(self, project_title, projects_folder):
        self.title = project_title
        self.folder = os.path.join(projects_folder, self.title)
        if not os.path.isdir(self.folder):
            raise ProjectException('Folder %s does not exist for project %s' % (project_title, self.folder))
        self.media_folder = os.path.join(self.folder, 'media')
        if not os.path.isdir(self.media_folder):
            raise ProjectException('Media folder %s does not exist for project %s' % (self.media_folder, project_title))
        self.db_name = 'db_%s' % project_title
        self.filename = '%s.tar' % get_backup_index(project_title, None, None)

    def __str__(self):
        return self.title


class Backuper(object):
    def __init__(self, project_title, b_type=None):
        self._logger = log.get(__name__)
        self._config = get_config()

        if b_type is None:
            b_type = get_backup_type()

        if b_type in TYPES:
            self._backup_type = b_type
        else:
            raise ValueError("Unknown backup type %s" % b_type)
        try:
            projects_folder = self._config.get('backuper', 'projects')
            self.project = Project(project_title, projects_folder)
        except ProjectException as e:
            raise BackupException('Unable to open project %s: %s' % (project_title, e))

    def backup(self):
        self._logger.info('Starting %s backup of %s' % (self._backup_type, self.project))
        index = get_current_index(self.project.title)
        backups_folder = self._config.get('backuper', 'backups')
        if not os.path.exists(backups_folder):
            self._logger.info('Creating folder %s for all backups' % backups_folder)
            os.mkdir(backups_folder)

        current_backup_folder = os.path.join(backups_folder, index)

        if not os.path.exists(current_backup_folder):
            self._logger.info('Creating folder %s for current backup' % current_backup_folder)
            os.mkdir(current_backup_folder)

if __name__ == '__main__':
    b = Backuper('machines')
    b.backup()