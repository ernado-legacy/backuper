#!/usr/bin/python
# coding=utf8
from datetime import datetime
from subprocess import call
import os
import sys
from ftplib import FTP, all_errors
import shutil
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import Encoders

VERSION = '1.0.32'


def send_mail(send_from, send_to, subject, text, files=None, server='localhost'):
    """
    Sends mail
    """
    assert type(send_to) == list
    assert type(files) == list

    if files is None:
        files = []

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(f, "rb").read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)

    smtp = smtplib.SMTP(server)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()


backup_root = '~/backup/'
email_notification = 'ernado@cygame.ru'
email_from = email_notification
path = lambda *args: os.path.join(os.path.abspath(os.path.dirname(__file__)), *args)


class TYPES:
    MONTH = 'month'
    DAY = 'day'
    WEEK = 'week'


class BackupError(Exception):
    pass


def get_week_number(d):
    if d % 7 == 0:
        return d / 7
    else:
        return d / 7 + 1


class Dumper:
    """
    Dumps database to file
    """
    def __init__(self, backuper):
        self.backuper = backuper

    def dump(self, directory=None):
        directory = directory or '~/'
        filename = 'db'
        project = self.backuper.project
        db_name = 'db_%s' % project
        pg_username = 'pg_%s' % project
        dump_promt = 'pg_dump -U {username} {db} -f {f}'.format(username=pg_username, db=db_name,
                                                                f=(filename or '%s.back' % project))
        arguments = dump_promt.split()
        call(arguments)


class Backuper:
    """
    Backuper - db dump, upload by ftp
    """
    verbose_text = {
        'week': 'weekly difference backup',
        'day': 'everyday incremental backup',
        'month': 'monthly full backup'
    }

    tar_call_arguments = ['tar', '--create', '--verbose', '--gzip',
                          '--preserve-permissions', '--ignore-failed-read',
                          '--one-file-system', '--recursion', '--totals']

    def send(self, status):
        """
        Sends e-mail with results of current backup process
        """
        self.logger.info('Sending mail')
        subject = {
            'week': 'weekly %s' % self.now.strftime('%m/%d'),
            'month': 'monthly №%s' % self.now.strftime('%m'),
            'day': 'daily %s' % self.now.strftime('%d.%m'),
        }[self.archive_type]

        if not status:
            subject = 'FAILED: %s' % subject
        else:
            subject = 'COMPLETED: %s' % subject

        files = [
            'backup-%s.log' % self.project,
            'backup-%s.err.log' % self.project
        ]

        send_mail(email_from, [email_notification, ], self.project + ': ' + subject, open('backup-%s.backuper.log' % self.project).read(),
                  files=files)
        self.logger.info('Mail sent')

    def tar(self):
        """
        Creates archive for current backup process
        """
        start_time = datetime.now()
        self.logger.info('Archiving to %s' % self.archive_file)
        result = call(self.tar_call_arguments + ['--listed-incremental=%s' % self.increment_file,
                                                 '--file=%s' % self.archive_file,
                                                 self.project_folder],
                      stdout=open('backup-%s.log' % self.project, 'a'),
                      stderr=open('backup-%s.err.log' % self.project, 'a'))
        if result == 0:
            self.logger.info('Archiving completed by %s seconds' % (datetime.now() - start_time).seconds)
        else:
            raise BackupError('[Error 10] Archiving failed')

    def upload(self):
        """
        Uploads to ftp created backup file
        """
        self.logger.info('Upload initialized')
        start_time = datetime.now()
        external_filename = os.path.basename(self.archive_file)
        try:
            if os.path.isfile(self.archive_file):
                self.logger.info('Connecting')
                ftp = FTP(self.FTP_DATA['host'], self.FTP_DATA['user'], self.FTP_DATA['password'])
                self.logger.info('Connected, starting upload')
                size = os.path.getsize(self.archive_file) / (1024 * 1024.0)
                self.logger.info('Uploading %s MB backup' % size)
                ftp.storbinary('STOR %s' % external_filename, open(self.archive_file))
                self.logger.info('Uploaded by %s seconds' % (datetime.now() - start_time).seconds)
                ftp.close()
            else:
                raise BackupError('[Error 3] No file to upload')
        except all_errors, e:
            raise BackupError('[Error 4] FTP ERROR - %s' % e)

    def dump(self):
        """
        Dumps database to file
        """
        # TODO: switch to postgresql dump
        self.logger.info('Dumping database')
        result = call([self.PYTHON, self.manage_path, 'dumpdata', '--exclude=contenttypes',
                       '--exclude=auth', '--natural', '--indent=4', '--format=json'],
                      stdout=open(self.data_dump_path, 'w'),
                      stderr=open('backup-%s.err.log' % self.project, 'a'))
        if result != 0:
            raise BackupError('[Error 1] Failed to dump database')
        self.logger.info('Dumped in %s seconds' % (datetime.now() - self.now).seconds)

    def backup(self):
        """
        Processes automatic full backup of project
        """
        start_time = datetime.now()
        status = False
        if self.archive_type not in [TYPES.MONTH, TYPES.DAY, TYPES.WEEK]:
            raise ValueError('archive type incorrect')
        try:
            shutil.copy(self.increment_file, self.increment_file + '.bak')

            if self.archive_type == TYPES.MONTH:
                self.logger.info('Full backup selected')
                os.remove(self.INCREMENT_FILES['month'])

            if self.archive_type == TYPES.WEEK:
                self.logger.info('Moving week increments')
                shutil.copy(self.INCREMENT_FILES['month'], self.INCREMENT_FILES['week'])
            self.logger.info('Backup started')
            self.dump()
            self.logger.info('Starting %s' % self.verbose)

            self.tar()

            if self.archive_type == TYPES.MONTH:
                self.logger.info('Moving month increments')
                shutil.copy(self.INCREMENT_FILES['month'], self.INCREMENT_FILES['week'])
            if self.archive_type == TYPES.WEEK:
                self.logger.info('Moving week increments')
                shutil.copy(self.INCREMENT_FILES['week'], self.INCREMENT_FILES['day'])

            self.upload()

            self.logger.info('Backup completed successfully by %s seconds' %
                             (datetime.now() - start_time).seconds)
            status = True
        except BackupError, e:
            self.logger.error('Backup failed. %s' % e)
            shutil.copy(self.increment_file + '.bak', self.increment_file)
        finally:
            self.send(status)

    def create_dirs(self):
        """
        Creates missing directories for backup
        """
        self.logger.info('Checking directories')

        dirs = [
            os.path.join(backup_root, self.project),
            os.path.join(backup_root, self.project, 'day'),
            os.path.join(backup_root, self.project, 'month'),
            os.path.join(backup_root, self.project, 'week')
        ]

        for d in dirs:
            if not os.path.exists(d):
                self.logger.info('Created %s' % d)
                os.makedirs(d)
            else:
                self.logger.info('%s already exists' % d)

    def clear_logs(self):
        """
        Re-creating log files for current backup process
        """
        for extension in ['log', 'err.log', 'backuper.log']:
            open('backup-%s.%s' % (self.project, extension), 'w').close()

    def init_loggers(self):
        __ch = logging.StreamHandler()
        __ch.setLevel(logging.INFO)
        __formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', r'%d.%m.%y %H:%M:%S')
        __ch.setFormatter(__formatter)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(__ch)
        handler = logging.FileHandler('backup-%s.backuper.log' % self.project)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', r'%d.%m.%y %H:%M:%S')
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        self.logger.addHandler(handler)

    def __init__(self, project, archive_type=None):
        self.project = project
        self.archive_type = archive_type

        now = datetime.now()

        if archive_type is None:
            #self.logger.info('Started from cron')
            self.archive_type = TYPES.DAY
            if now.day == 1:
                self.archive_type = TYPES.MONTH
            elif now.strftime('%w') == '6':
                self.archive_type = TYPES.WEEK
        archive_type = self.archive_type
        self.clear_logs()
        self.init_loggers()
        self.create_dirs()

        print 'Archive type: %s' % self.archive_type

        self.FTP_DATA = {
            'user': 'ftp1271718',
            'password': '4Fq5kDZL',
            'host': 'wdc-backup2.ispsystem.net',
        }

        self.FOLDERS = {
            'week': os.path.join(backup_root, project, 'week'),
            'day': os.path.join(backup_root, project, 'day'),
            'month': os.path.join(backup_root, project, 'month'),
        }

        self.folder = self.FOLDERS[archive_type]

        self.ARCHIVE_FILES = {
            'week': os.path.join(backup_root, project, self.folder,
                                 '%s-week-%s-%s.tar.gz' % (project, get_week_number(now.day), now.month)),
            'day': os.path.join(backup_root, project, self.folder, '%s-day-%s-%s.tar.gz' % (project, now.day, get_week_number(now.day) )),
            'month': os.path.join(backup_root, project, self.folder, '%s-month-%s.tar.gz' % (project, now.month)),
        }

        self.INCREMENT_FILES = {
            'week': os.path.join(backup_root, project, 'week.inc'),
            'day': os.path.join(backup_root, project, 'day.inc'),
            'month': os.path.join(backup_root, project, 'month.inc'),
        }

        self.increment_file = self.INCREMENT_FILES[archive_type]
        self.archive_file = self.ARCHIVE_FILES[archive_type]

        for f in self.INCREMENT_FILES.values():
            if not os.path.isfile(f):
                self.logger.info('Created file %s' % f)
                open(f, 'w').close()

        self.now = now
        self.PYTHON = '/var/www/ernado/data/envs/%s/bin/python' % project
        self.project_folder = os.path.join(backup_root, project)
        self.manage_path = path(self.project_folder, 'manage.py')
        self.verbose = self.verbose_text[archive_type]
        self.data_dump_path = path(self.project_folder, 'data.json')

        print 'Python path: %s' % self.PYTHON
        print 'manage.py: %s' % self.PYTHON
        print 'dump path: %s' % self.data_dump_path
        exit(0)
        self.logger = logging.getLogger(__name__)


class Restorator:
    """
    Class for backup restoration
    """

    def __init__(self, project, d, m):
        self.day = d
        self.month = m
        self.project = project

    def get_restore_sequence(self):
        """
        returns sequence of .tar files, that need to be extracted
        """
        w = get_week_number(self.day)
        day = int(self.day)
        files = ['month-%s.tar.gz' % self.month, 'week-%s-%s' % (w, self.month)]
        for x in range((w - 1) * 7, day):
            files.append('day-%s-%s' % (x, w))
        return files

    def restore(self):
        """
        Restores to previous condition
        """
        pass
        #s = self.get_restore_sequence()


if __name__ == '__main__':
    import logging
    import argparse

    parser = argparse.ArgumentParser(description='Automatic backup script v%s' % VERSION)
    parser.add_argument('project', help='Project name')
    parser.add_argument('-output', help='Path to project', default=None)
    parser.add_argument('--restore', help='Restore from backup', action='store_true', default=False)

    args = parser.parse_args()
    exit()
    if not os.path.exists(backup_root):
        os.makedirs(backup_root)
    os.chdir(backup_root)
    if len(sys.argv) < 3:
        print 'Usage: python backuper.py backup <project_name> [day|month|week]'
        print 'python backuper.py restore <project_name> <month> <day>'
        exit(0)
    PROJECT = args.project
    if sys.argv[1] == 'backup':
        open('backup-%s.log' % PROJECT, 'w').close()
        open('backup-%s.err.log' % PROJECT, 'w').close()
        open('backup-%s.backuper.log' % PROJECT, 'w').close()

        if len(sys.argv) == 4:
            b = Backuper(PROJECT, sys.argv[3])
        else:
            b = Backuper(PROJECT)
        b.backup()
        # # if len(sys.argv) < 2:
        # #     print 'Usage: python backuper.py (day|month|week)'
        # # elif sys.argv[1] == 'cron':
        #
        #if sys.argv[1] == 'dump':
        #	dump()
        # # else:
        # #     backup(sys.argv[1])
