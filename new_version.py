#!/usr/bin/env python
# encoding: utf-8

import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import xml.etree.ElementTree as ET
import yaml
from git import Repo

from shellfoundry.commands.pack_command import PackCommandExecutor
from shellfoundry.commands.install_command import InstallCommandExecutor
from shellfoundry.commands.dist_command import DistCommandExecutor


def main(args):

    #
    # CLI
    #
    parser = ArgumentParser(description='create new TG release',
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-r", "--release", help="New release version")
    parser.add_argument("-m", "--message", help="New commit message")
    parsed_args = parser.parse_args(args)

    #
    # Write new version
    #
    with open("shell.yml", 'r') as f:
        shell = yaml.safe_load(f)
    shell['shell']['version'] = parsed_args.release
    with open("shell.yml", 'w') as f:
        yaml.safe_dump(shell, f, default_flow_style=False)

    with open("version.txt", 'w') as f:
        f.write(parsed_args.release)

    drivermetadata = ET.parse('src/drivermetadata.xml')
    driver = drivermetadata.getroot()
    driver.attrib['Version'] = parsed_args.release
    drivermetadata.write('src/drivermetadata.xml')

    #
    # Shellfoundry
    #
    PackCommandExecutor().pack()
    DistCommandExecutor().dist()
    InstallCommandExecutor().install()

    #
    # git
    #
    if parsed_args.message:
        repo = Repo('.')
        repo.git.add('.')
        repo.git.commit('-m version {}'.format(parsed_args.message))
        repo.git.push()

# git push . development:master
# git push origin master:master

# Testing
# delete C:\Users\yoram-s\AppData\Local\pip
# remove virtual environments
# shellfoundry dist
# shellfoundry install
# test both online and offline
# test both Windows and Linux

# Create interactive cli (version, git comment)

if __name__ == "__main__":
    sys.argv.append('-r 1.2.3')
    sys.exit(main((sys.argv[1:])))
