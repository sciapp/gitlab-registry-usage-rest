import re
import flask_restful as rest
import sys
from flask_jwt_extended import jwt_required
from flask_restful.reqparse import RequestParser
from urllib.parse import quote


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
                if isinstance(params, (list, tuple)) else
                self._resource.to_dict(**params, embed=embed - 1, include_links=include_links)
                for params in self._params_list
            ]
        elif len(self._params_list) == 1:
            params = self._params_list[0]
            if isinstance(params, (list, tuple)):
                return self._resource.to_dict(*params, embed=embed - 1, include_links=include_links)
            else:
                return self._resource.to_dict(**params, embed=embed - 1, include_links=include_links)
        else:
            return None


class Link:
    def __init__(self, rel, *links, always_as_list=False, quote=True):
        self._rel = rel
        self._always_as_list = always_as_list
        self._quote = quote
        self._links = []
        for link in links:
            link_dict = self._create_link_dict(link)
            self._links.append(link_dict)

    def _create_link_dict(self, link):
        if isinstance(link, (list, tuple)):
            href, extra_attributes = link
        else:
            href, extra_attributes = link, {}
        link_dict = {'href': quote(href) if self._quote else href}
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
    def to_dict(cls, *args, embed=0, include_links=True, **kwargs):
        def extract_keywords_from_url(url):
            found_keywords = []

            def save_found_keyword(match_obj):
                found_keywords.append(match_obj.group(1))

            re.sub(r'<(?:[^:>]*:)?([^>]*)>', save_found_keyword, url)
            return found_keywords

        def merge_args_and_kwargs(*args, **kwargs):
            url_keywords = extract_keywords_from_url(cls._primary_url)
            merged_kwargs = {url_keyword: arg for url_keyword, arg in zip(url_keywords, args)}
            merged_kwargs.update(kwargs)
            # cheroot / CherryPy unquotes URLs but not ``%2F`` which is the path separator -> unquote it explicitly
            # see https://github.com/cherrypy/cheroot/blob/v6.0.0/cheroot/server.py#L826 for more explanation
            for url_keyword in url_keywords:
                merged_kwargs[url_keyword] = '/'.join(re.split(r'%2F', merged_kwargs[url_keyword], flags=re.IGNORECASE))
            return merged_kwargs

        def add_links(resource, **kwargs):
            def substitute(match_obj):
                keyword = match_obj.group(1)
                return quote(kwargs[keyword], safe='')

            self_link = Link('self', re.sub(r'<(?:.*:)?([^>]*)>', substitute, cls._primary_url), quote=False)
            resource['_links'] = {self_link.rel: self_link.link}
            try:
                links = cls.links(**kwargs)
            except AttributeError:
                return
            if links is None:
                return
            if isinstance(links, Link):
                links = [links]
            links = [link for link in links if link.link is not None]
            resource['_links'].update({link.rel: link.link for link in links})

        def embed_resources(resource, **kwargs):
            try:
                embeddeds = cls.embedded(**kwargs)
            except AttributeError:
                return
            if embeddeds is None:
                return
            if isinstance(embeddeds, Embedded):
                embeddeds = [embeddeds]
            embeddeds = [embedded for embedded in embeddeds if embedded.has_data]
            resource['_embedded'] = {}
            resource['_embedded'].update({embedded.rel: embedded.data(embed, include_links) for embedded in embeddeds})

        merged_kwargs = merge_args_and_kwargs(*args, **kwargs)
        resource = dict(cls.data(**merged_kwargs))
        if include_links:
            add_links(resource, **merged_kwargs)
        if embed > 0:
            embed_resources(resource, **merged_kwargs)
        return resource

    @jwt_required
    def get(self, **kwargs):
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
        return self.to_dict(embed=embed, include_links=include_links, **kwargs)
