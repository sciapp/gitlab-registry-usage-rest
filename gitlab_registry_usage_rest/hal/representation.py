from collections import OrderedDict
import flask_restful as rest
from flask_restful.representations.json import output_json


class Api(rest.Api):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default_mediatype', 'applicaton/hal+json')
        super().__init__(*args, **kwargs)
        self.representations = OrderedDict([('applicaton/hal+json', output_json)])

    def add_resource(self, resource, *urls, **kwargs):
        super().add_resource(resource, *urls, **kwargs)
        resource._primary_url = urls[0]
