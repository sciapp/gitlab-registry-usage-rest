import ldap3
from flask import g
from flask_httpauth import HTTPBasicAuth
from flask_jwt_extended import create_access_token
from .config import config
from typing import cast

http_basic_auth = HTTPBasicAuth()


def create_jwt() -> str:
    return cast(str, create_access_token(identity=g.username))


@http_basic_auth.verify_password  # type: ignore
def _verify_password(username: str, password: str) -> bool:
    ldap_url = config.ldap_host
    if not ldap_url.startswith('ldaps://'):
        ldap_url = 'ldaps://{}'.format(ldap_url)
    base_dn = config.ldap_base_dn
    valid_gid = config.ldap_valid_gid
    username_attribute = config.ldap_username_attribute
    gid_attribute = config.ldap_gid_attribute
    if gid_attribute:
        search_string = '(&({}={})({}={}))'.format(username_attribute, username, gid_attribute, valid_gid)
    else:
        search_string = '(&({}={}))'.format(username_attribute, username)
    is_verified = False
    try:
        ldap_server = ldap3.Server(ldap_url, use_ssl=True)
        ldap_connection = ldap3.Connection(ldap_server)
        ldap_connection.open()
        success = ldap_connection.search(base_dn, search_string)
        if success:
            # select user_dn string of first user found (if exactly one user is found) for given uid and groupId
            if len(ldap_connection.entries) == 1:
                user_dn = ldap_connection.entries[0].entry_dn
                # try to bind with credentials. throws exception if credentials are invalid
                ldap_connection.unbind()
                ldap_connection = ldap3.Connection(ldap_server, user_dn, password)
                is_verified = ldap_connection.bind()
                g.username = username
    finally:
        ldap_connection.unbind()
    return is_verified
