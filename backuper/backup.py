# coding=utf-8
import os
import datetime
import shutil
import logging
import codecs
import sys

from errors import BackupException, ProjectException
from config import get_config
from database import dump, dump_all, generate_pgpass
from uploader import upload_files
from archivator import incremental_compress, compress, compress_file
from reports import send


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


def get_backup_index(project_name, day, month, year=None, b_type=None):
    """
    @param project_name: Name of the project
    @return: backup unique index
    """
    assert type(project_name) is str
    assert type(day) is int
    assert type(month) is int
    assert type(year) is int

    if year is None:
        year = datetime.datetime.now().year

    if b_type is not None and b_type in (TYPES.daily, TYPES.monthly):
        t = b_type[0]
    else:
        t = get_backup_type(day)[0]

    return '{project}-{t}-{d:0>2}-{m:0>2}-{y}'.format(project=project_name,
                                                      t=t,
                                                      d=day,
                                                      m=month,
                                                      y=str(year)[-2:])


def get_current_index(project_name, b_type=None):
    now = datetime.datetime.now()
    day = now.day
    if b_type == TYPES.monthly:
        day = 1
    return get_backup_index(project_name, day, now.month, now.year, b_type)


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

    def __str__(self):
        return self.title


class Backuper(object):
    def __init__(self, project_title, b_type=None):
        self.log = logging.getLogger(__name__)
        self.cfg = get_config(self.log)
        self.file_handler = None

        if b_type is None:
            b_type = get_backup_type()

        if b_type in (TYPES.daily, TYPES.monthly):
            self.b_type = b_type
        else:
            raise ValueError("Unknown backup type %s" % b_type)
        try:
            projects_folder = self.cfg.get('backuper', 'projects')
            self.project = Project(project_title, projects_folder)
        except ProjectException as e:
            raise BackupException('Unable to open project %s: %s' % (project_title, e))
        self.b_index = get_current_index(self.project.title, b_type)
        b_folder = self.cfg.get('backuper', 'backups')
        self.log_filename = os.path.join(b_folder, '%s-backup.log.txt' % self.b_index)
        open(self.log_filename, 'w').close()
        self.initiate_loggers()

    def backup(self):
        b_time = datetime.datetime.now()
        self.log.info('Starting %s backup of %s' % (self.b_type, self.project))

        b_folder = self.cfg.get('backuper', 'backups')
        b_compress_log = os.path.join(b_folder, '%s-compress.txt' % self.b_index)
        b_compress_log_f = codecs.open(b_compress_log, 'w', 'utf-8')

        if not os.path.exists(b_folder):
            self.log.info('Creating folder %s for all backups' % b_folder)
            os.mkdir(b_folder)

        current_folder = os.path.join(b_folder, self.b_index)
        output_tarfile = os.path.join(b_folder, '%s.tar' % self.b_index)
        output_media_tarfile = os.path.join(current_folder, 'media.tar')

        if not os.path.exists(current_folder):
            self.log.info('Creating folder %s for current backup' % current_folder)
            os.mkdir(current_folder)

        dump_file_path = os.path.join(current_folder, '%s.dump' % self.project)
        dump(self.project.title, open(dump_file_path, 'w'), self.log)

        self.log.info('Compressing database')
        compress_file(dump_file_path, '%s.tar.gz' % dump_file_path, self.log)
        os.remove(dump_file_path)

        incremental_file = '%s.new.inc' % get_backup_index(self.project.title, 1, b_time.month, b_time.year)
        incremental_file = os.path.join(b_folder, incremental_file)
        incremental_compress(self.project.media_folder, output_media_tarfile, incremental_file,
                             b_compress_log_f, self.log)

        self.log.info('Compressing all to file')
        compress(current_folder, output_tarfile, b_compress_log_f, self.log)
        b_compress_log_f.close()

        self.log.info('Removing temporary files')
        shutil.rmtree(current_folder)
        shutil.move(incremental_file, incremental_file.replace('.new.inc', '.inc'))
        self.log.info('Uploading to ftp server')
        upload_files([output_tarfile], self.cfg, self.log)
        self.log.info('Completed')
        self.log.handlers = []
        self.file_handler.close()
        log_info = open(self.log_filename).read()
        send('backup %s' % self.b_index, log_info, cfg=self.cfg, files=[b_compress_log], logger=self.log)

    def initiate_loggers(self):
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', r'%d.%m.%y %H:%M:%S')
        handler = logging.StreamHandler()
        self.log.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        self.log.addHandler(handler)
        self.file_handler = logging.FileHandler(self.log_filename)
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        self.log.addHandler(self.file_handler)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: backuper.py <project_name> backup <?m/d>'
        print 'or: backuper.py <project_name> restore <dd.mm(?.yy)>'
    generate_pgpass()
    project = sys.argv[1]
    b_mode = sys.argv[2]
    if b_mode == 'backup':
        b_type = None
        if len(sys.argv) > 3:
            b_type = sys.argv[3]
            for t in (TYPES.monthly, TYPES.daily):
                if t[0] == b_type[0] or t == b_type:
                    b_type = t
        if b_type is not None and b_type not in (TYPES.monthly, TYPES.daily):
            b = Backuper(project, b_type)
            b.backup()
        else:
            print 'Incorrect backup type'
    else:
        print 'Not implemented'
