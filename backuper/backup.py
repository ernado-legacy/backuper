# coding=utf-8
import os
from errors import BackupException, ProjectException

from config import get_config


class backup_types(object):
    """
    Types of backup
    """
    daily = 'daily'
    weekly = 'weekly'
    monthly = 'monthly'
    _types = (daily, weekly, monthly)

    def __contains__(self, item):
        if item in self._types:
            return True
        return False


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


class Backuper(object):

    def __init__(self, b_type, project_title):
        self.config = get_config()
        if b_type in backup_types:
            self.backup_type = b_type
        else:
            raise ValueError("Unknown backup type %s" % b_type)
        try:
            projects_folder = self.config.get('backuper', 'projects')
            self.project = Project(project_title, projects_folder)
        except ProjectException as e:
            raise BackupException('Unable to open project %s: %s' % (project_title, e))


