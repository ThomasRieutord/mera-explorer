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
    """Abstract class for transferring tools.
    
    Attributes
    ----------
    localhost: str
        Name or IP adress of the local host
    
    lusername: str
        User name on the local host
    
    
    Parameters
    ----------
    remotehost: str
        Name or IP adress of the remote host
    
    rusername: str
        User name on the remote host
    
    protocol: str
        Transfer protocol used (FTP, SSH, or CP). For documentation only.
    
    verbose: bool
        If True, prompts info during the transfer
    """

    localhost = os.environ["HOSTNAME"]
    lusername = os.environ["USER"]

    def __init__(self, remotehost, rusername, protocol, verbose = False):
        self.remotehost = remotehost
        self.rusername = rusername
        self.protocol = protocol
        self.verbose = verbose

    def __str__(self):
        return f"{self.__module__}.{self.__class__.__name__}: " + ", ".join(
            [
                f"{attr}={getattr(self, attr)}"
                for attr in ["localhost", "remotehost", "lusername", "rusername"]
            ]
        )

    def connect(self):
        """Connect to the remote host and instanciate clients object"""
        pass
        
    def disconnect(self):
        """Close all clients"""
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
        os.makedirs(os.path.dirname(trg), exist_ok=True)

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
        
        self.connect()
        i = 0
        for src, trg in zip(srcs, trgs):
            self.get(src, trg)
            i += 1
            if self.verbose and i % max(len(srcs)//10, 1) == 0:
                print(f"[{i}/{len(srcs)}] last file created: {trg}")
            
        self.disconnect()

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
        
        self.connect()
        i = 0
        for src, trg in zip(srcs, trgs):
            self.put(src, trg)
            i += 1
            if self.verbose and i % max(len(srcs)//10, 1) == 0:
                print(f"[{i}/{len(srcs)}] last file created: {trg}")
            
        self.disconnect()


class SSHTransfer(Transfer):
    """Transfer with SSH protocol"""
    def __init__(self, remotehost, rusername, verbose = False):
        super().__init__(remotehost, rusername, "ssh", verbose)

    def connect(self):
        password = getpass(
            prompt=f"Enter password to connect from {self.localhost} to {self.remotehost} as {self.rusername} with {self.protocol.upper()}:"
        )
        self.sshclient = paramiko.SSHClient()
        self.sshclient.load_host_keys(
            os.path.expanduser(os.path.join("~", ".ssh", "known_hosts"))
        )
        self.sshclient.connect(
            hostname=self.remotehost,
            port=22,
            username=self.rusername,
            password=password,
        )
        self.sftpclient = self.sshclient.open_sftp()

    def disconnect(self):
        self.sshclient.close()
        self.sftpclient.close()
        
    def get(self, src, trg):
        super().get(src, trg)
        self.sftpclient.get(src, trg)

    def put(self, src, trg):
        super().put(src, trg)
        self.sftpclient.put(src, trg)


class FTPTransfer(Transfer):
    """Transfer with FTP protocol"""
    def __init__(self, remotehost, rusername, verbose = False):
        super().__init__(remotehost, rusername, "ftp", verbose)

    def connect(self):
        password = getpass(
            prompt=f"Enter password to connect from {self.localhost} to {self.remotehost} as {self.rusername} with {self.protocol.upper()}:"
        )
        self.client = ftplib.FTP(self.remotehost, self.rusername, password)
        self.client.encoding = "utf-8"
        
    def disconnect(self):
        self.client.close()

    def put(self, src, trg):
        super().put(src, trg)
        with open(src, "rb") as f:
            self.client.storbinary(f"STOR {trg}", f)

    def get(self, src, trg):
        super().get(src, trg)
        with open(trg, "wb") as f:
            self.client.retrbinary(f"RETR {src}", f.write)


class LocalTransfer(Transfer):
    """Transfer on the same host (with cp)"""
    def __init__(self, verbose = False):
        super().__init__(self.localhost, self.lusername, "cp", verbose)

    def get(self, src, trg):
        super().get(src, trg)
        shutil.copy2(src, trg)

    def put(self, src, trg):
        super().put(src, trg)
        shutil.copy2(src, trg)


# EOF
