# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
from mock import Mock
import pytest

from h.views import client
from h import __version__


def test_annotator_token_calls_generate_jwt(generate_jwt, pyramid_request):
    client.annotator_token(pyramid_request)

    generate_jwt.assert_called_once_with(pyramid_request, 3600)


def test_annotator_token_returns_token(generate_jwt, pyramid_request):
    result = client.annotator_token(pyramid_request)

    assert result == generate_jwt.return_value


@pytest.mark.usefixtures('routes')
class TestSidebarApp(object):

    def test_it_includes_client_config(self, pyramid_request_):
        ctx = client.sidebar_app(pyramid_request_)
        expected_config = {
                'apiUrl': 'http://example.com/api',
                'websocketUrl': 'wss://example.com/ws',
                'serviceUrl': 'http://example.com/',
                'release': __version__,
                'raven': {
                    'dsn': 'test-sentry-dsn',
                    'release': __version__
                },
                'googleAnalytics': 'UA-4567'
                }
        actual_config = json.loads(ctx['app_config'])
        assert actual_config == expected_config

    def test_it_sets_asset_urls(self, pyramid_request_):
        ctx = client.sidebar_app(pyramid_request_)
        assert ctx['app_css_urls'] == ['/assets/client/app.css']
        assert ctx['app_js_urls'] == ['/assets/client/app.js']


@pytest.mark.usefixtures('routes')
class TestEmbed(object):
    def test_it_sets_sidebar_app_url(self, pyramid_request_):
        ctx = client.embed(pyramid_request_)
        assert ctx['app_html_url'] == 'http://example.com/app.html'

    def test_it_sets_asset_urls(self, pyramid_request_):
        ctx = client.embed(pyramid_request_)
        assert ctx['inject_resource_urls'] == [
            'http://example.com/assets/client/polyfills.js',
            'http://example.com/assets/client/inject.js',
            'http://example.com/assets/client/inject.css',
            ]

    def test_it_sets_content_type(self, pyramid_request_):
        client.embed(pyramid_request_)
        assert pyramid_request_.response.content_type == 'text/javascript'


@pytest.fixture
def pyramid_request_(pyramid_request):
    assets_client_env = Mock(spec_set=['urls'])

    bundles = {
        'app_js': ['/assets/client/app.js'],
        'app_css': ['/assets/client/app.css'],
        'inject_js': ['/assets/client/polyfills.js', '/assets/client/inject.js'],
        'inject_css': ['/assets/client/inject.css'],
    }

    def urls(bundle_name):
        return bundles[bundle_name]
    assets_client_env.urls = urls
    pyramid_request.registry['assets_client_env'] = assets_client_env

    pyramid_request.registry.settings['ga_client_tracking_id'] = 'UA-4567'
    pyramid_request.registry.settings['h.client.sentry_dsn'] = 'test-sentry-dsn'
    pyramid_request.registry.settings['h.websocket_url'] = 'wss://example.com/ws'
    return pyramid_request


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('api.index', '/api')
    pyramid_config.add_route('assets_client', '/assets/client/{subpath}')
    pyramid_config.add_route('index', '/')
    pyramid_config.add_route('sidebar_app', '/app.html')


@pytest.fixture
def generate_jwt(patch):
    func = patch('h.views.client.generate_jwt')
    func.return_value = 'abc123'
    return func
