import io
from configparser import ConfigParser

DEFAULT_CONFIG_FILENAME = '/etc/gitlab_registry_usage_rest.conf'


class Config:
    _default_config = {
        'general': {
            'socket_host': '127.0.0.1',
            'socket_port': 5000,
            'server_prefix': '/',
            'debug': False
        },
        'registry': {
            'gitlab_base_url': 'https://mygitlab.com/',
            'registry_base_url': 'https://registry.mygitlab.com/',
            'username': 'root',
            'access_token': '00000000'
        }
    }

    @classmethod
    def write_default_config(cls, config_filename_or_file):
        default_config = ConfigParser()
        default_config.read_dict(cls._default_config)
        if isinstance(config_filename_or_file, io.IOBase):
            config_file = config_filename_or_file
            default_config.write(config_file)
        else:
            with open(config_filename_or_file, 'w') as config_file:
                default_config.write(config_file)

    def __init__(self, config_filename=DEFAULT_CONFIG_FILENAME):
        self._config_filename = config_filename
        self._config = ConfigParser()
        self._config.read_dict(self._default_config)
        self.read_config()

    def read_config(self, config_filename=None):
        if config_filename is not None:
            self._config_filename = config_filename
        if self._config_filename is not None:
            self._config.read(self._config_filename)

    @property
    def socket_host(self):
        return self._config['general']['socket_host']

    @property
    def socket_port(self):
        return int(self._config['general']['socket_port'])

    @property
    def server_prefix(self):
        return self._config['general']['server_prefix']

    @property
    def debug(self):
        return self._config['general']['debug'].lower() in ('true', 'yes', 't', 'y', '1')

    @property
    def gitlab_base_url(self):
        return self._config['registry']['gitlab_base_url']

    @property
    def registry_base_url(self):
        return self._config['registry']['registry_base_url']

    @property
    def username(self):
        return self._config['registry']['username']

    @property
    def access_token(self):
        return self._config['registry']['access_token']


config = Config(None)
