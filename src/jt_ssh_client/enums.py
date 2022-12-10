from enum import Enum


class Client(Enum):
    SSHClient = "SSHClient"
    SCPClient = "SCPClient"
    SFTPClient = "SFTPClient"
