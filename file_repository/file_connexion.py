# -*- coding: utf-8 -*-
###############################################################################
#
#   file_repository for OpenERP
#   Authors: Sebastien Beau <sebastien.beau@akretion.com>
#            Benoît Guillot <benoit.guillot@akretion.com>
#   Copyright 2013 Akretion
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from tempfile import TemporaryFile
import ftplib
import os
import paramiko
import errno
import functools

def open_and_close_connection(func):
    """
    Open And Close Decorator will automatically launch the connection
    to the external storage system.
    Then the function is excecuted and the connection is closed
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.persistant:
            if not self.connection:
                self.connect()
            return func(self, *args, **kwargs)
        else:
            self.connect()
            try:
                response = func(self, *args, **kwargs)
            except:
                raise
            finally:
                self.close()
            return response
    return wrapper

# Extend paramiko lib with the method mkdirs
def stfp_mkdirs(self, path, mode=511):
    try:
        self.stat(path)
    except IOError, e:
        if e.errno == errno.ENOENT:
            try:
                self.mkdir(path, mode)
            except IOError, e:
                if e.errno == errno.ENOENT:
                    self.mkdirs(os.path.dirname(path), mode)
                    self.mkdir(path, mode)
                else:
                    raise
paramiko.SFTPClient.mkdirs = stfp_mkdirs

# Extend ftplib with the method mkdirs
def ftp_mkdirs(self, path):
    current_dir = self.pwd()
    try:
        self.cwd(path)
    except ftplib.error_perm, e:
        if "550" in str(e):
            try:
                self.mkd(path)
            except ftplib.error_perm, e:
                if "550" in str(e):
                    self.mkdirs(os.path.dirname(path))
                    self.mkd(path)
                else:
                    raise
    self.cwd(current_dir)
ftplib.FTP.mkdirs = ftp_mkdirs

class FileConnection(object):

    def is_(self, protocol):
        return self.protocol.lower() == protocol

    def __init__(self, protocol, location, user, pwd, port=None,
                 allow_dir_creation=None, home_folder='/', persistant=False):
        self.protocol = protocol
        self.allow_dir_creation = allow_dir_creation
        self.location = location
        self.home_folder = home_folder or '/'
        self.port = port
        self.user = user
        self.pwd = pwd
        self.connection = None
        self.persistant = False

    def connect(self):
        if self.is_('ftp'):
            self.connection = ftplib.FTP(self.location, self.port)
            self.connection.login(self.user, self.pwd)
        elif self.is_('sftp'):
            transport = paramiko.Transport((self.location, self.port or 22))
            transport.connect(username = self.user, password = self.pwd)
            self.connection = paramiko.SFTPClient.from_transport(transport)

    def close(self):
        if self.is_('ftp') or self.is_('sftp') and self.connection is not None:
            self.connection.close()

    @open_and_close_connection
    def send(self, filepath, filename, output_file, create_patch=None):
        if self.is_('ftp'):
            filepath = os.path.join(self.home_folder, filepath)
            if self.allow_dir_creation:
                self.connection.mkdirs(filepath)
            self.connection.cwd(filepath)
            self.connection.storbinary('STOR ' + filename, output_file)
            output_file.close()
            return True
        elif self.is_('filestore'):
            if not os.path.isabs(filepath):
                filepath = os.path.join(self.location, filepath)
            if self.allow_dir_creation and not os.path.exists(filepath):
                os.makedirs(filepath)
            output = open(os.path.join(filepath, filename), 'w+b')
            for line in output_file.readlines():
                output.write(line)
            output.close()
            output_file.close()
            return True
        elif self.is_('sftp'):
            if not os.path.isabs(filepath):
                filepath = os.path.join(self.home_folder, filepath)
            if self.allow_dir_creation:
                self.connection.mkdirs(filepath)
            output = self.connection.open(os.path.join(filepath, filename), 'w+b')
            for line in output_file.readlines():
                output.write(line)
            output.close()
            output_file.close()
            return True

    @open_and_close_connection
    def get(self, filepath, filename):
        if self.is_('ftp'):
            outfile = TemporaryFile('w+b')
            self.connection.cwd(filepath)
            self.connection.retrbinary("RETR " + filename, outfile.write)
            outfile.seek(0)
            return outfile
        elif self.is_('sftp'):
            outfile = TemporaryFile('w+b')
            self.connection.chdir(filepath)
            remote_file = self.connection.file(filename)
            outfile.write(remote_file.read())
            outfile.seek(0)
            return outfile
        elif self.is_('filestore'):
            return open(os.path.join(filepath, filename), 'r+b')

    @open_and_close_connection
    def search(self, filepath, filename):
        if self.is_('ftp'):
            self.connection.cwd(filepath)
            #Take care that ftp lib use utf-8 and not unicode
            return [x for x in self.connection.nlst() if filename.encode('utf-8') in x]
        elif self.is_('sftp'):
            self.connection.chdir(filepath)
            return [x for x in self.connection.listdir() if filename in x]
        elif self.is_('filestore'):
            return [x for x in os.listdir(filepath) if filename in x]

    @open_and_close_connection
    def move(self, oldfilepath, newfilepath, filename):
        if self.is_('ftp'):
            self.connection.rename(os.path.join(oldfilepath, filename),
                                   os.path.join(newfilepath, filename))
        elif self.is_('sftp'):
            self.connection.rename(os.path.join(oldfilepath, filename),
                                   os.path.join(newfilepath, filename))
        elif self.is_('filestore'):
            os.rename(os.path.join(oldfilepath, filename),
                      os.path.join(newfilepath, filename))
