from django.test import TestCase
from django.conf import settings
from django import forms

from jpic.voodoo import media

class MediaTest(TestCase):
    def test_empty_media_with_js(self):
        t = media.converter(js=['foo.js', 'bar.js'])
        result = unicode(t)

        expected = u"\n".join([
            '<script type="text/javascript" src="%(prefix)sjs/foo.js"></script>',
            '<script type="text/javascript" src="%(prefix)sjs/bar.js"></script>'
        ])
        expected = expected % {'prefix': settings.JSITES_MEDIA_PREFIX}

        self.assertEqual(expected, result)

    def test_empty_media_with_js_and_absolute_path(self):
        t = media.converter(js=['foo.js', '/bar.js'])
        result = unicode(t)

        expected = u"\n".join([
            '<script type="text/javascript" src="%(prefix)sjs/foo.js"></script>',
            '<script type="text/javascript" src="/bar.js"></script>'
        ])
        expected = expected % {'prefix': settings.JSITES_MEDIA_PREFIX}

        self.assertEqual(expected, result)

    def test_empty_media_with_css(self):
        t = media.converter(css={'all': ['foo.css', 'bar.css']})
        result = unicode(t)

        expected = u"\n".join([
            '<link href="%(prefix)scss/foo.css" type="text/css" media="all" rel="stylesheet" />',
            '<link href="%(prefix)scss/bar.css" type="text/css" media="all" rel="stylesheet" />'
        ])
        expected = expected % {'prefix': settings.JSITES_MEDIA_PREFIX}

        self.assertEqual(expected, result)

    def test_empty_media_with_css_with_absolute_path(self):
        t = media.converter(css={'all': ['foo.css', '/bar.css']})
        result = unicode(t)

        expected = u"\n".join([
            '<link href="%(prefix)scss/foo.css" type="text/css" media="all" rel="stylesheet" />',
            '<link href="/bar.css" type="text/css" media="all" rel="stylesheet" />'
        ])
        expected = expected % {'prefix': settings.JSITES_MEDIA_PREFIX}
        self.assertEqual(expected, result)

    def test_empty_media_with_css_with_two_types(self):
        t = media.converter(css={'all': ['foo.css', '/bar.css'], 'screen': ['screen.css']})
        result = unicode(t)

        expected = u"\n".join([
            '<link href="%(prefix)scss/foo.css" type="text/css" media="all" rel="stylesheet" />',
            '<link href="/bar.css" type="text/css" media="all" rel="stylesheet" />',
            '<link href="%(prefix)scss/screen.css" type="text/css" media="screen" rel="stylesheet" />'
        ])
        expected = expected % {'prefix': settings.JSITES_MEDIA_PREFIX}
        self.assertEqual(expected, result)

    def test_behaviour(self):
        m = forms.Media(
            js=[
                'base.js',
                '/base_abs.js'
            ],
            css={
                'all': [
                    'base.css',
                    '/base_abs.css',
                ],
                'screen': [
                    'base_screen.css',
                    '/base_screen_abs.css',
                ],
            }
        )
        m = media.converter(
            m,
            js=[
                'my_base.js',
                '/my_base_abs.js'
            ],
            css={
                'all': [
                    'my_base.css',
                    '/my_base_abs.css',
                ],
                'screen': [
                    'my_base_screen.css',
                    '/my_base_screen_abs.css',
                ],
            }
        )

        result = unicode(m)

        expected = u"\n".join([
            '<link href="/static/jsites/css/base.css" type="text/css" media="all" rel="stylesheet" />',
            '<link href="/base_abs.css" type="text/css" media="all" rel="stylesheet" />',
            '<link href="/static/jsites/css/my_base.css" type="text/css" media="all" rel="stylesheet" />',
            '<link href="/my_base_abs.css" type="text/css" media="all" rel="stylesheet" />',
            '<link href="/static/jsites/css/base_screen.css" type="text/css" media="screen" rel="stylesheet" />',
            '<link href="/base_screen_abs.css" type="text/css" media="screen" rel="stylesheet" />',
            '<link href="/static/jsites/css/my_base_screen.css" type="text/css" media="screen" rel="stylesheet" />',
            '<link href="/my_base_screen_abs.css" type="text/css" media="screen" rel="stylesheet" />',
            '<script type="text/javascript" src="/static/jsites/js/base.js"></script>',
            '<script type="text/javascript" src="/base_abs.js"></script>',
            '<script type="text/javascript" src="/static/jsites/js/my_base.js"></script>',
            '<script type="text/javascript" src="/my_base_abs.js"></script>',
        ])


        expected = expected % {'prefix': settings.JSITES_MEDIA_PREFIX}
        self.assertEqual(expected, result)
