#!/usr/bin/env python3

import argparse
import cherrypy
import os
import sys
from flask import Flask
from flask_cors import CORS
from . import resources
from .config import Config, config, DEFAULT_CONFIG_FILENAME
from ._version import __version__, __version_info__  # noqa: F401 # pylint: disable=unused-import


class ConfigFileNotAccessibleError(Exception):
    pass


class AttributeDict(dict):
    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value


def setup_app():
    app = Flask(__name__)
    CORS(app)
    resources.init_resources(app)
    return app


def get_argumentparser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''
%(prog)s is a RESTful web service for querying the memory usage of images in a GitLab registry.
'''
    )
    parser.add_argument(
        '-c',
        '--config-file',
        action='store',
        dest='config_filename',
        type=os.path.abspath,
        default=DEFAULT_CONFIG_FILENAME,
        help='web service config file (default: %(default)s)'
    )
    parser.add_argument(
        '--print-default-config',
        action='store_true',
        dest='print_default_config',
        help='print the default config to stdout and exit'
    )
    parser.add_argument(
        '-V',
        '--version',
        action='store_true',
        dest='print_version',
        help='print the version number and exit'
    )
    return parser


def parse_arguments():
    parser = get_argumentparser()
    args = AttributeDict({key: value for key, value in vars(parser.parse_args()).items()})
    if not args.print_default_config and not args.print_version:
        if not os.path.isfile(args.config_filename) or not os.access(args.config_filename, os.R_OK):
            raise ConfigFileNotAccessibleError('The config file {} is not readable.'.format(args.config_filename))
    return args


def main():
    args = parse_arguments()
    if args.print_version:
        print('{}, version {}'.format(os.path.basename(sys.argv[0]), __version__))
        sys.exit(0)
    elif args.print_default_config:
        Config.write_default_config(sys.stdout)
        sys.exit(0)
    config.read_config(args.config_filename)
    app = setup_app()
    cherrypy.tree.graft(app, config.server_prefix)
    cherrypy.config.update(
        {
            'environment': 'test_suite' if config.debug else 'production',
            'server.socket_host': config.socket_host,
            'server.socket_port': config.socket_port
        }
    )
    cherrypy.engine.start()
    cherrypy.engine.block()


if __name__ == '__main__':
    main()
