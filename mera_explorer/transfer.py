#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer.

Transferring tools.
"""

import os
import ftplib
import paramiko
import shutil
from getpass import getpass


class Transfer:
    """Abstract class for transferring tools"""

    localhost = os.environ["HOSTNAME"]
    lusername = os.environ["USERNAME"]

    def __init__(self, remotehost, rusername, protocol):
        self.remotehost = remotehost
        self.rusername = rusername
        self.protocol = protocol

    def __str__(self):
        return f"{self.__module__}.{self.__class__.__name__}: " + ", ".join(
            [
                f"{attr}={getattr(self, attr)}"
                for attr in ["localhost", "remotehost", "lusername", "rusername"]
            ]
        )

    def connect(self):
        """Connect to the remote host and return a client object"""
        pass

    def get(self, src, trg):
        """Copy the file from `src` (remote) to `trg` (local)


        Parameters
        ----------
        src: str
            Path to the source file on the remote host

        trg: str
            Path to the target file on the local host
        """
        os.makedirs(trg, exist_ok=True)

    def put(self, src, trg):
        """Copy the file from `src` (local) to `trg` (remote)


        Parameters
        ----------
        src: str
            Path to the source file on the local host

        trg: str
            Path to the target file on the remote host
        """
        assert os.path.isfile(src), f"{self.localhost}:{src} is not a file"

    def mget(self, srcs, trgs):
        """Mutilple get


        Parameters
        ----------
        srcs: list of str
            List of source files on the remote host

        trgs: list of str
            List of target files on the local host
        """
        assert len(srcs) == len(
            trgs
        ), f"Lists of source files and target files do not have the same length"

    def mput(self, srcs, trgs):
        """Mutilple put


        Parameters
        ----------
        srcs: list of str
            List of source files on the remote host

        trgs: list of str
            List of target files on the local host
        """
        assert len(srcs) == len(
            trgs
        ), f"Lists of source files and target files do not have the same length"


class SSHTransfer(Transfer):
    """Transfer with SSH protocol"""

    def __init__(self, remotehost, rusername):
        super().__init__(remotehost, rusername, "ssh")

    def connect(self):
        password = getpass(
            prompt=f"Enter password to connect from {self.localhost} to {self.remotehost} as {self.rusername} with {self.protocol.upper()}:"
        )
        client = paramiko.SSHClient()
        client.load_host_keys(
            os.path.expanduser(os.path.join("~", ".ssh", "known_hosts"))
        )
        client.connect(
            hostname=self.remotehost,
            port=22,
            username=self.rusername,
            password=password,
        )
        return client

    def get(self, src, trg):
        super().get(src, trg)
        client = self.connect()
        sftp = client.open_sftp()
        sftp.get(src, trg)
        sftp.close()
        client.close()

    def put(self, src, trg):
        super().put(src, trg)
        client = self.connect()
        sftp = client.open_sftp()
        sftp.put(src, trg)
        sftp.close()
        client.close()

    def mget(self, srcs, trgs):
        super().mget(srcs, trgs)
        client = self.connect()
        sftp = client.open_sftp()
        for src, trg in zip(srcs, trgs):
            sftp.get(src, trg)

        sftp.close()
        client.close()

    def mput(self, srcs, trgs):
        super().mput(srcs, trgs)
        client = self.connect()
        sftp = client.open_sftp()
        for src, trg in zip(srcs, trgs):
            sftp.put(src, trg)

        sftp.close()
        client.close()


class FTPTransfer(Transfer):
    """Transfer with FTP protocol"""

    def __init__(self, remotehost, rusername):
        super().__init__(remotehost, rusername, "ftp")

    def connect(self):
        password = getpass(
            prompt=f"Enter password to connect from {self.localhost} to {self.remotehost} as {self.rusername} with {self.protocol.upper()}:"
        )
        client = ftplib.FTP(self.remotehost, self.rusername, password)
        client.encoding = "utf-8"
        return client

    def put(self, src, trg):
        super().put(src, trg)
        client = self.connect()
        with open(src, "rb") as f:
            client.storbinary(f"STOR {trg}", f)

        client.close()

    def get(self, src, trg):
        super().get(src, trg)
        client = self.connect()
        with open(trg, "wb") as f:
            client.retrbinary(f"RETR {src}", f.write)

        client.close()

    def mget(self, srcs, trgs):
        super().mget(srcs, trgs)
        client = self.connect()
        for src, trg in zip(srcs, trgs):
            with open(trg, "wb") as f:
                client.retrbinary(f"RETR {src}", f.write)

        client.close()

    def mput(self, srcs, trgs):
        super().mput(srcs, trgs)
        client = self.connect()
        for src, trg in zip(srcs, trgs):
            with open(src, "rb") as f:
                client.storbinary(f"STOR {trg}", f)

        client.close()


class LocalTransfer(Transfer):
    def __init__(self):
        super().__init__(self.localhost, self.lusername, "cp")

    def get(self, src, trg):
        super().get(src, trg)
        shutil.copy2(src, trg)

    def put(self, src, trg):
        super().get(src, trg)
        shutil.copy2(src, trg)

    def mget(self, srcs, trgs):
        super().mget(srcs, trgs)
        for src, trg in zip(srcs, trgs):
            shutil.copy2(src, trg)

    def mput(self, srcs, trgs):
        super().mput(srcs, trgs)
        for src, trg in zip(srcs, trgs):
            shutil.copy2(src, trg)


# EOF
