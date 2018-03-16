import collections
import flask_restful as rest
from flask import jsonify
from .auth import http_basic_auth, create_jwt
from .config import config
from .cache import GitLabRegistryCache
from .hal.representation import Api as HalApi
from .hal.resource import Resource, Embedded, Link

RequestContext = collections.namedtuple('RequestContext', ['registry', 'timestamp'])

_request_context = None


class AuthToken(rest.Resource):
    @http_basic_auth.login_required
    def get(self):
        auth_token = create_jwt()
        return jsonify({'auth_token': auth_token})


class Images(Resource):
    @staticmethod
    def data():
        return {'timestamp': _request_context.timestamp}

    @staticmethod
    def embedded():
        return Embedded(
            'items', Image, *[(image, ) for image in _request_context.registry.registry_catalog], always_as_list=True
        )

    @staticmethod
    def links():
        return Link(
            'items',
            *[
                ('/images/{}'.format(image_name), {
                    'title': image_name
                }) for image_name in _request_context.registry.registry_catalog
            ],
            always_as_list=True
        )


class Image(Resource):
    @staticmethod
    def data(image_name):
        return {
            'name': image_name,
            'size': _request_context.registry.image_sizes[image_name],
            'disk_size': _request_context.registry.image_disk_sizes[image_name]
        }

    @staticmethod
    def embedded(image_name):
        if _request_context.registry.image_tags[image_name] is not None:
            return Embedded('related', Tags, (image_name, ))
        else:
            return None

    @staticmethod
    def links(image_name):
        links = [Link('collection', '/images')]
        if _request_context.registry.image_tags[image_name] is not None:
            links.append(Link('related', ('/images/{}/tags'.format(image_name), {'title': 'tags'})))
        return links


class Tags(Resource):
    @staticmethod
    def data(image_name):
        return {}

    @staticmethod
    def embedded(image_name):
        if _request_context.registry.image_tags[image_name] is not None:
            return Embedded(
                'items',
                Tag,
                *[(image_name, tag_name) for tag_name in _request_context.registry.image_tags[image_name]],
                always_as_list=True
            )
        else:
            return None

    @staticmethod
    def links(image_name):
        links = [Link('up', '/images/{}'.format(image_name))]
        if _request_context.registry.image_tags[image_name] is not None:
            links.append(
                Link(
                    'items',
                    *[
                        ('/images/{}/tags/{}'.format(image_name, tag_name), {
                            'title': image_name
                        }) for tag_name in _request_context.registry.image_tags[image_name]
                    ],
                    always_as_list=True
                )
            )
            return links
        else:
            return None


class Tag(Resource):
    @staticmethod
    def data(image_name, tag_name):
        return {
            'name': tag_name,
            'size': _request_context.registry.tag_sizes[image_name][tag_name],
            'disk_size': _request_context.registry.tag_disk_sizes[image_name][tag_name]
        }

    @staticmethod
    def links(image_name, tag_name):
        return Link('collection', '/images/{}/tags'.format(image_name))


def init_resources(app):
    def init_registry():
        gitlab_registry_cache = GitLabRegistryCache(
            config.gitlab_base_url, config.registry_base_url, config.username, config.access_token
        )
        gitlab_registry_cache.update()
        gitlab_registry_cache.update_continuously()
        return gitlab_registry_cache

    def init_api():
        api = HalApi(app)
        api.add_resource(AuthToken, '/auth_token')
        api.add_resource(Images, '/images')
        api.add_resource(Image, '/images/<image_name>')
        api.add_resource(Tags, '/images/<image_name>/tags')
        api.add_resource(Tag, '/images/<image_name>/tags/<tag_name>')
        return api

    gitlab_registry_cache = init_registry()
    init_api()

    @app.before_request
    def set_request_context():
        global _request_context
        _request_context = RequestContext(gitlab_registry_cache.registry, gitlab_registry_cache.timestamp)
