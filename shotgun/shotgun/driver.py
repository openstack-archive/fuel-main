import os
import re
import tempfile
import stat

import fabric.api

from shotgun.logger import logger
from shotgun.utils import is_local
from shotgun.utils import execute


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
            "command": Command,
        }.get(driver_type, cls)(data, conf)

    def __init__(self, data, conf):
        logger.debug("Initializing driver %s: host=%s",
            self.__class__.__name__, data.get("host"))
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
                output = fabric.api.run(command, pty=True)
                out.stdout = output
                out.return_code = output.return_code
                out.stderr = output.stderr
        else:
            logger.debug("Running local command: %s", command)
            out.return_code, out.stdout, out.stderr = execute(command)
        return out

    def get(self, path, target_path):
        if not self.local:
            with fabric.api.settings(host_string=self.host):
                logger.debug("Getting remote file: %s %s", path, target_path)
                return fabric.api.get(path, target_path)
        else:
            logger.debug("Getting local file: cp -r %s %s", path, target_path)
            execute("mkdir -p %s" % os.path.dirname(target_path))
            return execute("cp -r %s %s" % (path, target_path))


class File(Driver):
    def __init__(self, data, conf):
        super(File, self).__init__(data, conf)
        self.path = self.data["path"]
        logger.debug("File to get: %s", self.path)
        self.target_path = os.path.join(
            self.conf.target, self.host, self.path.lstrip("/"))
        logger.debug("File to save: %s", self.target_path)

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
        execute(command, to_filename=temp)
        self.command("mv %s %s" % (temp, self.target_path))
        tf.close()

    def subs_directory(self):
        f = tempfile.TemporaryFile(mode='r+b')
        tf = tarfile.open(fileobj=f, mode='w:gz')
        for arcname, path in settings.LOGS_TO_PACK_FOR_SUPPORT.items():
            walk = os.walk(path)
            if not os.path.isdir(path):
                walk = (("/", [], [path]),)
            for root, _, files in walk:
                for filename in files:
                    absfilename = os.path.join(root, filename)
                    relfilename = os.path.relpath(absfilename, path)
                    if not re.search(r".+\.bz2", filename):
                        lf = tempfile.NamedTemporaryFile()
                        self.sed(absfilename, lf.name,
                                 (True
                                  if re.search(r".+\.gz", filename)
                                  else False))
                        target = os.path.normpath(
                            os.path.join(arcname, relfilename)
                        )
                        tf.add(lf.name, target)
                        lf.close()
        tf.close()


class Postgres(Driver):
    def __init__(self, data, conf):
        super(Postgres, self).__init__(data, conf)
        self.dbhost = self.data.get("dbhost", "localhost")
        self.dbname = self.data["dbname"]
        self.username = self.data.get("username", "postgres")
        self.password = self.data.get("password")

    def snapshot(self):
        if self.password:
            authline = "{host}:{port}:{dbname}:{username}:{password}".format(
                host=self.host, port="5432", dbname=self.dbname,
                username=self.username, password=self.password)
            with open(os.path.expanduser("~/.pgpass"), "a+") as fo:
                fo.seek(0)
                auth = False
                for line in fo:
                    if re.search(ur"^%s$" % authline, line):
                        auth = True
                        break
                if not auth:
                    fo.seek(0, 2)
                    fo.write("{0}\n".format(authline))
            os.chmod(os.path.expanduser("~/.pgpass"), stat.S_IRUSR + stat.S_IWUSR)
        temp = self.command("mktemp").stdout.strip()
        self.command("pg_dump -h {dbhost} -U {username} -w "
                     "-f {file} {dbname}".format(
                        dbhost=self.dbhost, username=self.username,
                        file=temp, dbname=self.dbname))
        self.get(temp, os.path.join(
            self.conf.target, self.host, "postgres_dump_%s.sql" % self.dbname))
        self.command("rm -f %s" % temp)


class Command(Driver):
    def __init__(self, data, conf):
        super(Command, self).__init__(data, conf)
        self.cmdname = self.data["command"]
        self.to_file = self.data["to_file"]
        self.target_path = os.path.join(
            self.conf.target, self.host, "commands", self.to_file)

    def snapshot(self):
        out = self.command(self.cmdname)
        execute("mkdir -p {0}".format(os.path.dirname(self.target_path)))
        with open(self.target_path, "w") as f:
            f.write("===== COMMAND =====: {0}\n".format(self.cmdname))
            f.write("===== RETURN CODE =====: {0}\n".format(out.return_code))
            f.write("===== STDOUT =====:\n")
            f.write(out.stdout)
            f.write("\n===== STDERR =====:\n")
            f.write(out.stderr)

