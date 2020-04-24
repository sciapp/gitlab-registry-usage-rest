#!/usr/bin/env python3

import argparse
import os
import sys
from cheroot import wsgi
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.serving import run_simple
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from . import resources
from .config import Config, config, DEFAULT_CONFIG_FILENAME
from ._version import __version__, __version_info__  # noqa: F401 # pylint: disable=unused-import
from typing import cast, Any, AnyStr, Callable


class ConfigFileNotAccessibleError(Exception):
    pass


class AttributeDict(dict):
    def __getattr__(self, attr: str) -> Any:
        return self[attr]

    def __setattr__(self, attr: str, value: Any) -> None:
        self[attr] = value


def setup_app() -> Flask:
    app = Flask(__name__)
    # `PROPAGATE_EXCEPTIONS` must be set explicitly, otherwise jwt error handling won't work with flask-restful in
    # production mode
    app.config['DEBUG'] = config.debug
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = config.jwt_auth_token_expires
    app.config['JWT_SECRET_KEY'] = config.jwt_secret_key
    CORS(app)
    JWTManager(app)
    resources.init_resources(app)
    return app


def get_argumentparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''
%(prog)s is a RESTful web service for querying the memory usage of repositories in a GitLab registry.
'''
    )
    parser.add_argument(
        '-c',
        '--config-file',
        action='store',
        dest='config_filename',
        type=cast(Callable[[str], AnyStr], os.path.abspath),
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


def parse_arguments() -> AttributeDict:
    parser = get_argumentparser()
    args = AttributeDict({key: value for key, value in vars(parser.parse_args()).items()})
    if not args.print_default_config and not args.print_version:
        if not os.path.isfile(args.config_filename) or not os.access(args.config_filename, os.R_OK):
            raise ConfigFileNotAccessibleError('The config file {} is not readable.'.format(args.config_filename))
    return args


def main() -> None:
    args = parse_arguments()
    if args.print_version:
        print('{}, version {}'.format(os.path.basename(sys.argv[0]), __version__))
        sys.exit(0)
    elif args.print_default_config:
        Config.write_default_config(sys.stdout)
        sys.exit(0)
    config.read_config(args.config_filename)
    app = setup_app()
    if config.debug:
        if config.server_prefix != '/':
            app = DispatcherMiddleware(Flask('debugging_frontend'), {config.server_prefix: app})  # type: ignore
        run_simple(config.socket_host, config.socket_port, app, use_debugger=True, use_reloader=True)  # type: ignore
    else:
        wsgi_server = wsgi.Server(
            (config.socket_host, config.socket_port), wsgi.PathInfoDispatcher({
                config.server_prefix: app
            })
        )
        wsgi_server.safe_start()


if __name__ == '__main__':
    main()
