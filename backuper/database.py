# coding=utf-8
import os
import subprocess
from ConfigParser import ConfigParser, NoSectionError

from config import get_config
import log

logger = log.get(__name__)
password_format = 'localhost:5432:db_{name}:pg_{name}:{key}\n'
command_format = 'pg_dump -U pg_{name} db_{name}'


def dump(project_name, dump_file=None):
    logger.info('Dumping %s database' % project_name)
    command = command_format.format(name=project_name)
    if dump_file is None:
        dump_file = open('db_%s.dump' % project_name, 'w')
    p = subprocess.Popen(command, shell=True, stdout=dump_file)
    p.wait()
    dump_file.close()
    logger.info('Dump finished')


def generate_pgpass():
    logger.info('Generating pgpass file')
    config = get_config()
    projects_folder = config.get('backuper', 'projects')
    user_root = os.path.expanduser("~")
    project_list = os.listdir(projects_folder)
    pgpass_strings = []

    for project_name in project_list:
        parser = ConfigParser()
        try:
            parser.read(os.path.join(projects_folder, project_name, 'conf', 'backuper.conf'))
            password = parser.get('backuper', 'password')
        except (NoSectionError, IOError), e:
            logger.error('Failed to process %s: %s' % (project_name, e))
            continue
        pgpass_strings.append(password_format.format(key=password, name=project_name))

    with open(os.path.join(user_root, '.pgpass'), 'w') as pgpass_file:
        pgpass_file.writelines(pgpass_strings)

    logger.info('Processed database password lines: %s' % len(pgpass_strings))
    return pgpass_strings

if __name__ == '__main__':
    settings = generate_pgpass()
    if settings:
        dump('machines')