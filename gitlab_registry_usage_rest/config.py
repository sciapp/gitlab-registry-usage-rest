import datetime
from configparser import ConfigParser
from typing import Any, Dict, Optional, TextIO, Union  # noqa: F401  # pylint: disable=unused-import

DEFAULT_CONFIG_FILENAME = '/etc/gitlab_registry_usage_rest.conf'


class ParseTimeDeltaError(Exception):
    def __init__(self, timedelta_string: str) -> None:
        super().__init__('"{}" cannot be parsed.'.format(timedelta_string))


def parse_timedelta(timedelta_string: str) -> datetime.timedelta:
    units_to_keyword = {
        ('s', 'second', 'seconds'): 'seconds',
        ('m', 'minute', 'minutes'): 'minutes',
        ('h', 'hour', 'hours'): 'hours',
        ('d', 'day', 'days'): 'days',
        ('w', 'week', 'weeks'): 'weeks'
    }
    timedelta_string = timedelta_string.lower()
    timedelta_split = tuple(timedelta_string.split())
    if len(timedelta_split) == 1:
        timedelta_split = (timedelta_string[:-1], timedelta_string[-1])
    elif len(timedelta_split) == 2:
        pass
    else:
        raise ParseTimeDeltaError(timedelta_string)
    if not timedelta_split[0].isdigit():
        raise ParseTimeDeltaError(timedelta_string)
    value, unit = int(timedelta_split[0]), timedelta_split[1]
    for units, keyword in units_to_keyword.items():
        if unit in units:
            return datetime.timedelta(**{keyword: value})
    raise ParseTimeDeltaError(timedelta_string)


class Config:
    _default_config = {
        'general': {
            'socket_host': '127.0.0.1',
            'socket_port': 5000,
            'server_prefix': '/',
            'debug': False
        },
        'ldap': {
            'host': 'myldap.com',
            'base_dn': 'dc=example,dc=com',
            'valid_gid': '00000',
            'username_attribute': 'uid',
            'gid_attribute': 'gidNumber'
        },
        'jwt': {
            'auth_token_expires': '2 weeks',
            'secret_key': '00000000000000000000000000000000'
        },
        'registry': {
            'gitlab_base_url': 'https://mygitlab.com/',
            'registry_base_url': 'https://registry.mygitlab.com/',
            'username': 'root',
            'access_token': '00000000000000000000'
        }
    }  # type: Dict[str, Dict[str, Any]]

    @classmethod
    def write_default_config(cls, config_filename_or_file: Union[str, TextIO]) -> None:
        default_config = ConfigParser()
        default_config.read_dict(cls._default_config)
        if isinstance(config_filename_or_file, str):
            with open(config_filename_or_file, 'w') as config_file:
                default_config.write(config_file)
        else:
            config_file = config_filename_or_file
            default_config.write(config_file)

    def __init__(self, config_filename: Optional[str] = DEFAULT_CONFIG_FILENAME) -> None:
        self._config_filename = config_filename
        self._config = ConfigParser()
        self._config.read_dict(self._default_config)
        self.read_config()

    def read_config(self, config_filename: Optional[str] = None) -> None:
        if config_filename is not None:
            self._config_filename = config_filename
        if self._config_filename is not None:
            self._config.read(self._config_filename)

    @property
    def socket_host(self) -> str:
        return self._config['general']['socket_host']

    @property
    def socket_port(self) -> int:
        return int(self._config['general']['socket_port'])

    @property
    def server_prefix(self) -> str:
        return self._config['general']['server_prefix']

    @property
    def debug(self) -> bool:
        return self._config['general']['debug'].lower() in ('true', 'yes', 't', 'y', '1')

    @property
    def ldap_host(self) -> str:
        return self._config['ldap']['host']

    @property
    def ldap_base_dn(self) -> str:
        return self._config['ldap']['base_dn']

    @property
    def ldap_valid_gid(self) -> str:
        return self._config['ldap']['valid_gid']

    @property
    def ldap_username_attribute(self) -> str:
        return self._config['ldap']['username_attribute']

    @property
    def ldap_gid_attribute(self) -> str:
        return self._config['ldap']['gid_attribute']

    @property
    def jwt_auth_token_expires(self) -> datetime.timedelta:
        return parse_timedelta(self._config['jwt']['auth_token_expires'])

    @property
    def jwt_secret_key(self) -> str:
        return self._config['jwt']['secret_key']

    @property
    def gitlab_base_url(self) -> str:
        return self._config['registry']['gitlab_base_url']

    @property
    def registry_base_url(self) -> str:
        return self._config['registry']['registry_base_url']

    @property
    def username(self) -> str:
        return self._config['registry']['username']

    @property
    def access_token(self) -> str:
        return self._config['registry']['access_token']


config = Config(None)
