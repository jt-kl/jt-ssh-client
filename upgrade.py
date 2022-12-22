#!/usr/bin/env python3.10.6
from argparse import ArgumentParser, BooleanOptionalAction
from pathlib import Path
from sys import exit

from semver import VersionInfo


def main(
    major: bool = False,
    minor: bool = False,
    patch: bool = False,
    prerelease: bool = False,
    build: bool = False,
):
    """
    Semantic Versioning Handler

    Args:
        major: Bump major version number
        minor: Bump minor version number
        patch: Bump patch version number
        prerelease: Bump prerelease version number
        build: Bump build version number

    Example:
        python3 upgrade.py -minor -prerelease
        python3 upgrade.py -build
    """
    # region: Pre-flight operations

    BASE_DIRECTORY = Path(__name__).parent
    REFERENCE_FILE = BASE_DIRECTORY.joinpath("VERSION")
    MODULE_FILE = BASE_DIRECTORY.joinpath("src/jt_ssh_client/_version.py")

    # endregion: Pre-flight operations

    text = REFERENCE_FILE.read_text()

    if not text:
        text = "0.0.0"

    _version = VersionInfo.parse(text)

    conditions = [
        major == False,
        minor == False,
        patch == False,
        prerelease == False,
        build == False,
    ]

    if all(conditions):
        print(f"Current version: {_version}")
        exit()

    if major:
        _version = _version.bump_major()

    if minor:
        _version = _version.bump_minor()

    if patch:
        _version = _version.bump_patch()

    if prerelease:
        _version = _version.bump_prerelease()

    if build:
        _version = _version.bump_build()

    confirmed = False

    while not confirmed:
        response = input(f"Upgrade current version: v{text} to v{_version} - Confirm (Y/N): ")

        if not response.upper() in ["Y", "N"]:
            print(f"Invalid response, try again.\n")

            continue
        else:
            if response.upper() == "Y":
                confirmed = True

                REFERENCE_FILE.write_text(str(_version))
                MODULE_FILE.write_text(f'VERSION="{str(_version)}"')

                break
            else:
                break


if __name__ == "__main__":

    parser = ArgumentParser(description="Semantic Versioning Utility")
    parser.add_argument(
        "--major",
        action="store_true",
        dest="major",
        help="Invoke to bump major version number",
    )
    parser.add_argument(
        "--minor",
        action="store_true",
        dest="minor",
        help="Invoke to bump minor version number",
    )
    parser.add_argument(
        "--patch",
        action="store_true",
        dest="patch",
        help="Invoke to bump patch version number",
    )
    parser.add_argument(
        "--prerelease",
        action=BooleanOptionalAction,
        default=False,
        dest="prerelease",
        help="Invoke to bump pre-release version number",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        dest="build",
        help="Invoke to bump build version number",
    )

    args = parser.parse_args()

    main(
        major=args.major,
        minor=args.minor,
        patch=args.patch,
        prerelease=args.prerelease,
        build=args.build,
    )
