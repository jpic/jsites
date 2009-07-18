from django import forms
from django.conf import settings

def converter(media=None, js=[], css={}):
    """
    Prefix non absolute paths in js and css keyword arguments with:
    - settings.JSITES_MEDIA_PREFIX
    - (js)|(css)

    For example, js file 'foo.js' will become 'media_prefix/js/foo.js',
    and /bar/css/foo.css will be /bar/css/foo.css.
    """
    if media is None:
        media = forms.Media()

    final_js = []
    
    # BRAND NEWS: and django usage of metaclasses is still a pain
    media_js = getattr(media, 'js', getattr(media, '_js'))
    media_css = getattr(media, 'css', getattr(media, '_css'))

    for src in media_js + js:
        if src[0] == '/':
            final_js.append(src)
        else:
            final_js.append('%sjs/%s' % (
                    settings.JSITES_MEDIA_PREFIX,
                    src
                )
            )
    
    final_css={}
    for type in media_css.keys() + css.keys():
        final_css[type] = []

        test = []

        if type in media_css:
            test += media_css[type]
        
        if type in css:
            test += css[type]

        for src in test:
            if src[0] == '/':
                final_css[type].append(src)
            else:
                final_css[type].append('%scss/%s' % (
                        settings.JSITES_MEDIA_PREFIX,
                        src
                    )
                )
   
    return forms.Media(js=final_js, css=final_css)
