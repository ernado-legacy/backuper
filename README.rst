=====
Backuper
=====

Backup system for cyberprojects

Quick start
-----------

1. Create postgresql superuser::

    CREATE USER backuper WITH PASSWORD 'password here';
    ALTER USER backuper WITH SUPERUSER;

2. in /etc/postgresql/8.4/main/pg_hba.conf::

    # Database administrative login by UNIX sockets
    local   all         postgres                          ident
    # Add this:
    local   all         backuper                          ident
    # TYPE  DATABASE    USER        CIDR-ADDRESS          METHOD


3. Grant read/write rights on project and backup folder::

   adduser backuper sudo
   chgrp -R sudo <folder>

4. Copy  config to backuper user folder and set up permissions::

    cp backuper/backuper/backuper.conf ~
    chmod o-rwx,g-rwx ~/backuper.conf

5. Create .pgpass file and set up permissions::

   touch ~/.pgpass
   chmod o-rwx,g-rwx ~/.pgpass

