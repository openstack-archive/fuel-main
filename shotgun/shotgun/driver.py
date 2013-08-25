import os
import subprocess
import shlex
import re
import logging
import tempfile

import fabric.api

from shotgun.utils import is_local

logger = logging.getLogger()

class CommandOut(object):
    pass

class Driver(object):
    @classmethod
    def getDriver(cls, data, conf):
        driver_type = data["type"]
        return {
            "file": File,
            "dir": Dir,
            "subs": Subs,
            "postgres": Postgres,
        }.get(driver_type, cls)(data, conf)

    def __init__(self, data, conf):
        logger.debug("Initializing driver %s", self.__class__.__name__)
        self.data = data
        self.host = self.data.get("host", "localhost")
        self.local = is_local(self.host)
        self.conf = conf

    def snapshot(self):
        raise NotImplementedError

    def command(self, command):
        out = CommandOut()
        if not self.local:
            with fabric.api.settings(host_string=self.host):
                logger.debug("Running remote command: "
                             "host: %s command: %s", self.host, command)
                out.stdout = fabric.api.run(command, pty=True)
                out.return_code = result.return_code
                out.stderr = result.stderr
        else:
            logger.debug("Running local command: %s", command)
            out.return_code, out.stdout, out.stderr = self._execute(command)
        return out

    def get(self, path, target_path):
        if not self.local:
            with fabric.api.settings(host_string=self.host):
                logger.debug("Getting remote file: %s %s", path, target_path)
                return fabric.api.get(path, target_path)
        else:
            logger.debug("Getting local file: cp -r %s %s", path, target_path)
            self._execute("mkdir -p %s" % os.path.dirname(target_path))
            return self._execute("cp -r %s %s" % (path, target_path))

    def _execute(self, command, to_filename=None):
        commands = [c.strip() for c in re.split(ur'\|', command)]
        env = os.environ
        env["PATH"] = "/bin:/usr/bin:/sbin:/usr/sbin"

        to_file = None
        if to_filename:
            to_file = open(to_filename, 'wb')

        process = []
        for c in commands:
            process.append(subprocess.Popen(
                shlex.split(c),
                env=env,
                stdin=(process[-1].stdout if process else None),
                stdout=(to_file
                        if (len(process) == len(commands) - 1) and to_file
                        else subprocess.PIPE),
                stderr=(subprocess.PIPE)
            ))
            if len(process) >= 2:
                process[-2].stdout.close()
        stdout, stderr = process[-1].communicate()
        return (process[-1].returncode, stdout, stderr)

class File(Driver):
    def __init__(self, data, conf):
        super(File, self).__init__(data, conf)
        self.path = self.data["path"]
        self.target_path = os.path.join(
            self.conf.target, self.host, os.path.relpath(self.path, "/"))

    def snapshot(self):
        self.get(self.path, self.target_path)


Dir = File


class Subs(File):
    def __init__(self, data, conf):
        super(Subs, self).__init__(data, conf)
        self.subs = self.data["subs"]

    @property
    def gz(self):
        """
        Here we need something more sophisticated than just
        looking at file name.
        """
        if re.search(ur".+\.gz$", self.target_path):
            return True
        return False

    def snapshot(self):
        super(Subs, self).snapshot()
        tf = tempfile.NamedTemporaryFile()
        logger.debug("Sed script: %s", tf.name)
        for orig, new in self.subs.iteritems():
            logger.debug("Sed script: s/%s/%s/g", orig, new)
            tf.write("s/%s/%s/g\n" % (orig, new))
            tf.flush()
        temp = self.command("mktemp").stdout.strip()
        command = " | ".join(filter(lambda x: x != "", [
            "cat %s" % self.target_path,
            "gunzip -c" if self.gz else "",
            "sed -f %s" % tf.name,
            "gzip -c" if self.gz else ""
        ]))
        self._execute(command, to_filename=temp)
        self.command("mv %s %s" % (temp, self.target_path))
        tf.close()


class Postgres(Driver):
    def __init__(self, data, conf):
        super(Postgres, self).__init__(data, conf)
        self.dbname = self.data["dbname"]
        self.username = self.data.get("username", "postgres")
        self.password = self.data.get("password")

    def snapshot(self):
        password_opt = "-w"
        if self.password:
            password_opt = "-W %s" % self.password
        temp = self.command("mktemp").stdout.strip()
        self.command("pg_dump -U {user} {password_opt} "
                     "-f {file} {dbname}".format(user=self.username,
                                                 password_opt=password_opt,
                                                 file=temp, dbname=self.dbname))
        self.get(temp, os.path.join(
            self.conf.target, self.host, "postgres_dump_%s.sql" % self.dbname))
        self.command("rm -f %s" % temp)
