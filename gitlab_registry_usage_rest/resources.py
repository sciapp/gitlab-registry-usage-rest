from flask import Flask, jsonify, Response
from flask_jwt_extended import jwt_required
from flask_restful import Resource as RestResource
from flask_restful_hal import Api, Embedded, Link, Resource as HalResource
from urllib.parse import quote
from gitlab_registry_usage.registry.high_level_api import GitLabRegistry
from .auth import http_basic_auth, create_jwt
from .config import config
from .cache import GitLabRegistryCache
from typing import cast, Any, Dict, List, NamedTuple, Optional, Union

RequestContext = NamedTuple('RequestContext', [('registry', GitLabRegistry), ('timestamp', float)])

_request_context = None  # type: Optional[RequestContext]


class ResourceNotExistingError(Exception):
    def __init__(self, resource_endpoint: str, status_code: int = 404, payload: Optional[Any] = None) -> None:
        message = 'The resource "{}" does not exist'.format(resource_endpoint)
        super().__init__(message)
        self._message = message
        self._status_code = status_code
        self._payload = payload

    def to_dict(self) -> Dict[str, Any]:
        rv = dict(self._payload or ())
        rv['message'] = self._message
        return rv

    @property
    def message(self) -> str:
        return self._message

    @property
    def status_code(self) -> int:
        return self._status_code


class SecuredHalResource(HalResource):  # type: ignore
    @jwt_required  # type: ignore
    def get(self, **kwargs: Any) -> Any:
        return super().get(**kwargs)


class AuthToken(RestResource):  # type: ignore
    @http_basic_auth.login_required  # type: ignore
    def get(self) -> str:
        auth_token = create_jwt()
        return cast(str, jsonify({'auth_token': auth_token}))


class Repositories(SecuredHalResource):
    @staticmethod
    def data() -> Dict[str, Optional[float]]:
        if _request_context is not None:
            return {'timestamp': _request_context.timestamp}
        else:
            return {'timestamp': None}

    @staticmethod
    def embedded() -> Optional[Embedded]:
        if _request_context is not None:
            return Embedded(
                'items',
                Repository,
                *[(repository, ) for repository in _request_context.registry.registry_catalog],
                always_as_list=True
            )
        else:
            return None

    @staticmethod
    def links() -> Optional[Link]:
        if _request_context is not None:
            return Link(
                'items',
                *[
                    ('/repositories/{}'.format(quote(repository_name, safe='')), {
                        'title': repository_name
                    }) for repository_name in _request_context.registry.registry_catalog
                ],
                always_as_list=True,
                quote=False
            )
        else:
            return None


class Repository(SecuredHalResource):
    @staticmethod
    def data(repository_name: str) -> Optional[Dict[str, Union[int, str]]]:
        if _request_context is not None:
            try:
                return {
                    'name': repository_name,
                    'size': _request_context.registry.repository_sizes[repository_name],
                    'disk_size': _request_context.registry.repository_disk_sizes[repository_name]
                }
            except KeyError:
                raise ResourceNotExistingError('/repositories/{}'.format(quote(repository_name, safe='')))
        else:
            return None

    @staticmethod
    def embedded(repository_name: str) -> Optional[Embedded]:
        if _request_context is not None and _request_context.registry.repository_tags[repository_name] is not None:
            return Embedded('related', Tags, (repository_name, ))
        else:
            return None

    @staticmethod
    def links(repository_name: str) -> List[Link]:
        links = [Link('collection', '/repositories')]
        if _request_context is not None and _request_context.registry.repository_tags[repository_name] is not None:
            links.append(
                Link(
                    'related', ('/repositories/{}/tags'.format(quote(repository_name, safe='')), {
                        'title': 'tags'
                    }),
                    quote=False
                )
            )
        return links


class Tags(SecuredHalResource):
    @staticmethod
    def data(repository_name: str) -> Optional[Dict[str, Any]]:
        if _request_context is not None:
            if repository_name not in _request_context.registry.registry_catalog:
                raise ResourceNotExistingError('/repositories/{}/tags'.format(quote(repository_name, safe='')))
            return {}
        else:
            return None

    @staticmethod
    def embedded(repository_name: str) -> Optional[Embedded]:
        if _request_context is not None and _request_context.registry.repository_tags[repository_name] is not None:
            return Embedded(
                'items',
                Tag,
                *[
                    (repository_name, tag_name)
                    for tag_name in _request_context.registry.repository_tags[repository_name]
                ],
                always_as_list=True
            )
        else:
            return None

    @staticmethod
    def links(repository_name: str) -> List[Link]:
        links = [Link('up', '/repositories/{}'.format(quote(repository_name, safe='')), quote=False)]
        if _request_context is not None and _request_context.registry.repository_tags[repository_name] is not None:
            links.append(
                Link(
                    'items',
                    *[
                        (
                            '/repositories/{}/tags/{}'.format(
                                quote(repository_name, safe=''), quote(tag_name, safe='')
                            ), {
                                'title': repository_name
                            }
                        ) for tag_name in _request_context.registry.repository_tags[repository_name]
                    ],
                    always_as_list=True,
                    quote=False
                )
            )
        return links


class Tag(SecuredHalResource):
    @staticmethod
    def data(repository_name: str, tag_name: str) -> Optional[Dict[str, Union[int, str]]]:
        if _request_context is not None:
            try:
                return {
                    'name': tag_name,
                    'size': _request_context.registry.tag_sizes[repository_name][tag_name],
                    'disk_size': _request_context.registry.tag_disk_sizes[repository_name][tag_name]
                }
            except KeyError:
                raise ResourceNotExistingError(
                    '/repositories/{}/tags/{}'.format(quote(repository_name, safe=''), quote(tag_name, safe=''))
                )
        else:
            return None

    @staticmethod
    def links(repository_name: str, tag_name: str) -> Link:  # pylint: disable=unused-argument
        return Link('collection', '/repositories/{}/tags'.format(quote(repository_name, safe='')), quote=False)


def init_resources(app: Flask) -> None:
    def init_registry() -> GitLabRegistryCache:
        gitlab_registry_cache = GitLabRegistryCache(
            config.gitlab_base_url, config.registry_base_url, config.username, config.access_token
        )
        gitlab_registry_cache.update()
        gitlab_registry_cache.update_continuously()
        return gitlab_registry_cache

    def init_api() -> Api:
        api = Api(app)
        api.add_resource(AuthToken, '/auth_token')
        api.add_resource(Repositories, '/repositories')
        api.add_resource(Repository, '/repositories/<path:repository_name>')
        api.add_resource(Tags, '/repositories/<path:repository_name>/tags')
        api.add_resource(Tag, '/repositories/<path:repository_name>/tags/<path:tag_name>')
        return api

    def init_errorhandlers() -> None:
        @app.errorhandler(ResourceNotExistingError)  # type: ignore
        def handle_invalid_usage(error: ResourceNotExistingError) -> Response:  # pylint: disable=unused-variable
            response = jsonify(error.to_dict())  # type: Response
            response.status_code = error.status_code
            return response

    gitlab_registry_cache = init_registry()
    init_api()
    init_errorhandlers()

    @app.before_request  # type: ignore
    def set_request_context() -> None:  # pylint: disable=unused-variable
        global _request_context
        _request_context = RequestContext(gitlab_registry_cache.registry, gitlab_registry_cache.timestamp)
