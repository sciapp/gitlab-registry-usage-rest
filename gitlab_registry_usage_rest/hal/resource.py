import re
import flask_restful as rest
import sys
from flask_jwt_extended import jwt_required
from flask_restful.reqparse import RequestParser


class Embedded:
    def __init__(self, rel, resource, *params_list, always_as_list=False):
        self._rel = rel
        self._resource = resource
        self._params_list = params_list
        self._always_as_list = always_as_list

    @property
    def rel(self):
        return self._rel

    @property
    def resource(self):
        return self._resource

    @property
    def params_list(self):
        return self._params_list

    @property
    def has_data(self):
        return len(self._params_list) > 0

    def data(self, embed=0, include_links=True):
        if len(self._params_list) > 1 or (self._always_as_list and self._params_list):
            return [
                self._resource.to_dict(*params, embed=embed - 1, include_links=include_links)
                for params in self._params_list
            ]
        elif len(self._params_list) == 1:
            return self._resource.to_dict(*self._params_list[0], embed=embed - 1, include_links=include_links)
        else:
            return None


class Link:
    def __init__(self, rel, *links, always_as_list=False):
        self._rel = rel
        self._links = []
        for link in links:
            link_dict = self._create_link_dict(link)
            self._links.append(link_dict)
        self._always_as_list = always_as_list

    @staticmethod
    def _create_link_dict(link):
        if isinstance(link, (list, tuple)):
            href, extra_attributes = link
        else:
            href, extra_attributes = link, {}
        link_dict = {'href': href}
        link_dict.update(extra_attributes)
        return link_dict

    @property
    def rel(self):
        return self._rel

    @property
    def link(self):
        if len(self._links) > 1 or (self._always_as_list and self._links):
            return self._links
        elif len(self._links) == 1:
            return self._links[0]
        else:
            return None


class Resource(rest.Resource):
    _request_parser = RequestParser()
    _request_parser.add_argument('embed')
    _request_parser.add_argument('links')

    @classmethod
    def to_dict(cls, *args, embed=0, include_links=True):
        def add_links(resource):
            resource['_links'] = {'self': {'href': re.sub(r'<.*>', '{}', cls._primary_url).format(*args)}}
            try:
                links = cls.links(*args)
                if isinstance(links, Link):
                    links = [links]
                links = [link for link in links if link.link is not None]
                resource['_links'].update({link.rel: link.link for link in links})
            except AttributeError:
                pass

        def embed_resources(resource):
            try:
                embeddeds = cls.embedded(*args)
                if isinstance(embeddeds, Embedded):
                    embeddeds = [embeddeds]
                embeddeds = [embedded for embedded in embeddeds if embedded.has_data]
                resource['_embedded'] = {}
                resource['_embedded'].update(
                    {embedded.rel: embedded.data(embed, include_links)
                     for embedded in embeddeds}
                )
            except AttributeError:
                pass

        resource = dict(cls.data(*args))
        if include_links:
            add_links(resource)
        if embed > 0:
            embed_resources(resource)
        return resource

    @jwt_required
    def get(self, *args):
        def parse_args():
            def is_valid_true_string(string):
                return string is not None and string.lower() in ('true', 'yes', '1', 't', 'y')

            args = self._request_parser.parse_args()
            if args['embed'] is not None and args['embed'].isdigit():
                embed = int(args['embed'])
            else:
                embed = sys.maxsize if is_valid_true_string(args['embed']) else 0
            links = is_valid_true_string(args['links'])
            return embed, links

        embed, include_links = parse_args()
        print('embed:', embed, 'include_links:', include_links)
        return self.to_dict(*args, embed=embed, include_links=include_links)
