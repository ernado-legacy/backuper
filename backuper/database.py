# coding=utf-8
"""
Database dump module
"""

import os
import subprocess
from ConfigParser import ConfigParser, NoSectionError

from config import get_config
import log as _log


password_string = 'localhost:5432:db_{name}:pg_{name}:{key}\n'
command_string = 'pg_dump -U pg_{name} db_{name}'


def dump(project_name, dump_file=None, log=None):
    """
    Dump database of project
    @type dump_file: FileIO
    @param project_name: name of project's folder
    @param dump_file: output file
    @type project_name: str
    """
    if log is None:
        log = _log.get(__name__)
    log.info('Dumping %s database' % project_name)
    command = command_string.format(name=project_name)
    if dump_file is None:
        dump_file = open('db_%s.dump' % project_name, 'w')
    p = subprocess.Popen(command, shell=True, stdout=dump_file)
    p.wait()
    dump_file.close()

    log.info('Dump for %s finished' % project_name)


def dump_all(dump_file=None, log=None):
    """
    Full dump
    @param dump_file: output file
    """
    if log is None:
        log = _log.get(__name__)

    command = 'pg_dumpall'
    log.info('Starting full dump')

    if dump_file is None:
        dump_file = open('full.dump', 'w')
    p = subprocess.Popen(command, shell=True, stdout=dump_file)
    p.wait()
    dump_file.close()

    log.info('Full dump finished')


def generate_pgpass(log=None):
    """
    Generates a gpass file
    @return: dictionary of database passwords
    """
    if log is None:
        log = _log.get(__name__)

    log.info('Generating pgpass file')
    config = get_config()
    passwords = {}
    projects_folder = config.get('backuper', 'projects')
    user_root = os.path.expanduser("~")
    project_list = os.listdir(projects_folder)
    pgpass_strings = []

    for project_name in project_list:
        parser = ConfigParser()
        try:
            parser.read(os.path.join(projects_folder, project_name, 'conf', 'backuper.conf'))
            password = parser.get('backuper', 'password')
            log.info('Settings for project %s loaded' % project_name)
            passwords.update({project_name: password})
        except (NoSectionError, IOError), e:
            log.warning('Failed to process %s: %s' % (project_name, e))
            continue
        pgpass_strings.append(password_string.format(key=password, name=project_name))

    with open(os.path.join(user_root, '.pgpass'), 'w') as pgpass_file:
        pgpass_file.writelines(pgpass_strings)

    log.info('Pgpass file generated. Processed projects: %s' % len(pgpass_strings))
    return passwords


if __name__ == '__main__':
    for project in generate_pgpass():
        dump(project)
    dump_all()