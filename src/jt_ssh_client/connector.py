import sys
from os import system
from pathlib import Path
from typing import Callable, Optional, Union

from paramiko import BadHostKeyException, RSAKey, SFTPClient, SSHClient, Transport
from paramiko.client import AutoAddPolicy, MissingHostKeyPolicy
from paramiko.sftp_attr import SFTPAttributes
from paramiko.ssh_exception import AuthenticationException
from scp import SCPClient

from .enums import Client

# region: Helper methods


def _scp_client_progress_text_callback(
    file: bytes,
    size: int,
    sent: int,
    peername: tuple,
):
    """
    SCP text based progress handler

    Args:
        file: File
        size: Size of file in bytes
        sent: Total bytes sent
        peername: Remote host name and port number
    """
    prefix = f"{peername[0]}:{peername[1]} | {file.decode('utf-8')}"
    percentage = 100 * (sent / float(size))

    if sent < size:
        sys.stdout.write(f"{prefix} | {percentage:.2f}%\r")
    else:
        sys.stdout.write(f"{prefix} | {percentage:.2f}%\n")


# endregion: Helper methods


class Connector:
    def __init__(
        self,
        host: str,
        port: int = 22,
        username: Optional[str] = None,
        password: Optional[str] = None,
        ssh_credentials: tuple[Path, Path, Union[str, None]] = tuple(),
        policy=AutoAddPolicy(),
    ):
        """
        Constructor

        Args:
           username: Authentication username for remote host
           password: Authentication password for remote host
           host: Host FQDN or IP address of remote host
           port: Port number of remote host
           ssh_credentials: Path to SSH private key, SSH public key and SSH key passphrase
           policy: Handling policy for unknown server
        """
        self.username = username
        self.password = password
        self.host = host.strip()
        self.port = port
        self.ssh_private_key = None
        self.ssh_private_key_file = None
        self.ssh_public_key_file = None
        self.ssh_key_passphrase = None
        self.policy = policy

        if ssh_credentials:
            credentials = [
                ssh_credentials[0].exists(),
                ssh_credentials[1].exists(),
            ]

            if all(credentials):
                (
                    self.ssh_private_key_file,
                    self.ssh_public_key_file,
                    self.ssh_key_passphrase,
                ) = ssh_credentials

                # self._upload_ssh_public_key()
            else:
                raise FileExistsError(f"Invalid SSH Private/Public Key File")

        def __repr__(self):
            return f"<Connector: {self.host}>"

        self._retrieve_ssh_key()
        self.ssh_client = self._create_ssh_client()
        self.scp_client = self._create_scp_client()
        self.sftp_client = self._create_sftp_client()

    def disconnect(
        self,
    ):
        """
        Disconnect all clients from remote host
        """
        if self.ssh_client:
            self.ssh_client.close()

        if hasattr(self, "scp_client") and self.scp_client:
            self.scp_client.close()

        if hasattr(self, "sftp_client") and self.sftp_client:
            self.sftp_client.close()

    def _create_ssh_client(
        self,
        **kwargs,
    ) -> SSHClient:
        """
        Create an SSH client

        Remarks:
            Order of authentication:
            - pkey | self.ssh_key
            - key_filename | self.ssh_private_key_file
            - allow_agent | Keys provided by an SSH agent
            - look_for_keys | Keys discoverable in ~/.ssh
            - username | self.username
        """
        try:
            client = SSHClient()
            client.set_missing_host_key_policy(self.policy)
            client.load_system_host_keys()

            if self.ssh_private_key:
                client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    pkey=self.ssh_private_key,
                    key_filename=str(self.ssh_private_key_file),
                    passphrase=self.ssh_key_passphrase,
                    timeout=5000,
                    allow_agent=False,
                    look_for_keys=False,
                    **kwargs,
                )
            elif self.username and self.password:
                client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=5000,
                    allow_agent=False,
                    look_for_keys=False,
                    **kwargs,
                )
            else:
                raise Exception(
                    (
                        f"Invalid credentials supplied. Please specify either "
                        f"a username/password or an SSH private key file path "
                        f"and SSH private key passphrase."
                    )
                )

            self.ssh_client = client

            return client

        except BadHostKeyException as error:
            raise error
        except AuthenticationException as error:
            raise error

    def _create_scp_client(
        self,
        callback: Callable = _scp_client_progress_text_callback,
    ) -> SCPClient:
        """
        Creates an SCP client

        Args:
            callback: Task progress callback function
        """
        transport = self.ssh_client.get_transport()

        if not isinstance(transport, type(None)):
            self.scp_client = SCPClient(transport, progress4=callback)

        return self.scp_client

    def _create_sftp_client(
        self,
    ) -> SFTPClient:
        """
        Creates an SFTP client
        """
        self.sftp_client = self.ssh_client.open_sftp()

        return self.sftp_client

    def _get_client(
        self,
        client: Client,
    ) -> Union[SSHClient, SCPClient, SFTPClient]:
        """
        Get client type
        """
        if client == Client.SSHClient:
            return self.ssh_client

        elif client == Client.SCPClient:
            return self.scp_client

        else:
            return self.sftp_client

    def _retrieve_ssh_key(
        self,
    ):
        """
        Retrieve SSH key from localhost
        """
        if self.ssh_private_key_file:
            self.ssh_private_key = RSAKey.from_private_key_file(
                str(self.ssh_private_key_file),
                self.ssh_key_passphrase,
            )

            return self.ssh_private_key

    def _upload_ssh_public_key(
        self,
    ):
        """
        Upload SSH key to remote server
        """
        command = (
            f"ssh-copy-id -i {self.ssh_public_key_file} -p {self.port} " f"{self.username}@{self.host}>/dev/null 2>&1"
        )

        try:
            system(command)
        except Exception as error:
            raise error

    def _download_file(
        self,
        client: Client,
        source: str,
        destination: Union[Path, str] = "",
        recursive: bool = False,
        **kwargs,
    ):
        """
        Download file from remote host

        Args:
            client: Transport client to facilitate upload task
            source: Remote file/directory to be downloaded
            destination: Directory path to download file to
            recursive: Recursively download contents of source directory
        """
        _client = self._get_client(client)

        # Download using SCP client (Faster option)
        if isinstance(_client, SCPClient):
            # Check for validate directory if recursive is false
            _client.get(source, local_path=str(destination), recursive=recursive, **kwargs)

        # Download using SFTP client (Slower option)
        elif isinstance(_client, SFTPClient):
            _client.get(source, str(destination), **kwargs)

        else:
            raise Exception(f"{client.value} not currently supported")

    def _download_files(
        self,
        client: Client,
        sources: list[str],
        destination: Union[Path, str] = "",
        recursive: bool = False,
    ):
        """
        Download files from remote host

        Args:
            client: Transport client to facilitate download task
            sources: Collection of remote files to be downloaded
            destination: Directory path to download files to
            recursive: Recursively download contents of source directory
        """
        [self._download_file(client, source, destination, recursive) for source in sources]

    def _upload_file(
        self,
        client: Client,
        source: Path,
        destination: str,
        **kwargs,
    ):
        """
        Upload file to host

        Args:
            client: Transport client to facilitate upload task
            source: Local file to be uploaded
            destination: Directory path to be uploaded to
        """
        _client = self._get_client(client)

        # Upload using SCP client (Faster option)
        if isinstance(_client, SCPClient):
            _client.put(source, remote_path=destination)

        # Upload using SFTP client
        elif isinstance(_client, SFTPClient):
            _client.put(str(source), destination, **kwargs)

        else:
            raise Exception(f"{client.value} not currently supported")

    def _upload_files(
        self,
        client: Client,
        sources: list[Path],
        destination: str,
        recursive: bool = False,
        **kwargs,
    ):
        """
        Upload collection of files to host

        Args:
            client: Transport client to facilitate upload task
            sources: Collection of local files to be uploaded
            destination: Directory path to be uploaded to
            recursive: Recursively upload contents of source directory
        """
        for source in sources:
            if source.is_file():
                self._upload_file(client, source, destination, **kwargs)

            if source.is_dir() and recursive:
                for item in source.iterdir():
                    self._upload_files(client, [item], destination, **kwargs)

    def _execute_commands(
        self,
        commands: list[str],
    ):
        """
        Execute BASH commands on host

        Args:
            commands: Collection of commands to be executed
        """
        for command in commands:
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            stdout.channel.recv_exit_status()
            response = stdout.readlines()

            for line in response:
                print(f"Input: {command} \n" f"Result: {line}")

    # region: SFTP only commands

    def _list_directory(
        self,
        path: str,
    ) -> list[str]:
        """
        List contents of directory using SFTP

        Args:
            path: Directory path on host
        """
        return self.sftp_client.listdir(path)

    def _list_attributes(
        self,
        path: str,
    ) -> list[SFTPAttributes]:
        """
        List attributes of directory contents using SFTP

        Args:
            path: Directory path on host
        """
        return self.sftp_client.listdir_attr(path)

    def _retrieve_stats(
        self,
        path: str,
    ) -> SFTPAttributes:
        """
        Retrieve file/directory information

        Args:
            path: File/Directory path on host
        """
        return self.sftp_client.stat(path)

    def _remove_directory(
        self,
        path: str,
    ):
        """
        Remove directory using SFTP

        Args:
            path: Directory path to be removed
        """
        return self.sftp_client.rmdir(path)

    def _remove_directories(
        self,
        paths: list[str],
    ):
        """
        Remove collection of directories using SFTP

        Args:
            paths: Collection of directories to be removed
        """
        [self._remove_directory(path) for path in paths]

    def _remove_file(
        self,
        path: str,
    ):
        """
        Remove file using SFTP

        Args:
            path: File path to be removed
        """
        return self.sftp_client.remove(path)

    def _remove_files(
        self,
        paths: list[str],
    ):
        """
        Remove collection of files using SFTP

        Args:
            paths: Collection of files to be removed
        """
        [self._remove_file(path) for path in paths]

    # endregion: SFTP only commands

    # region: Wrapper methods
    # endregion: Wrapper methods

    # region: Helper methods for Android hosts

    def backup_android_media_directories(
        self,
        client: Client,
        sources: list[str] = [
            "/sdcard/DCIM",
            "/sdcard/Pictures",
            "/sdcard/Movies",
            "/sdcard/Music",
            "/sdcard/Ringtones",
        ],
        destination: Union[Path, str] = "",
        **kwargs,
    ):
        """
        Helper method to recursively backup contents of media directories
        on Android devices.

        Args:
            client: Transport client to facilitate upload task
            sources: Collection of media directories to be backed up
            destination: Directory path to download file to
        """
        for source in sources:
            self._download_file(client, source, destination, recursive=True, **kwargs)

    def backup_android_document_directories(
        self,
        client: Client,
        sources: list[str] = ["/sdcard/Download"],
        destination: Union[Path, str] = "",
        **kwargs,
    ):
        """
        Helper method to recursively backup contents of document directories
        on Android devices

        Args:
            client: Transport client to facilitate upload task
            sources: Collection of document directories to be backed up
            destination: Directory path to download file to
        """
        for source in sources:
            self._download_file(client, source, destination, recursive=True, **kwargs)

    def create_android_directories(
        self,
        paths: list[str] = ["/sdcard/Download/HelloWorld"],
    ):
        """
        Helper method to create directory on Android devices

        Args:
            path: Collection of directory paths to create
        """
        commands = [f"mkdir -p {i}" for i in paths]

        self._execute_commands(commands)

    # endregion: Helper methods for Android hosts
