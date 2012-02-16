import logging

from webhelpers.html import literal

from tg import config, request, url
from tg.render import render

from tgext.debugbar.sections import __sections__
from tgext.debugbar.controller import DebugBarController
from tgext.debugbar.utils import get_root_controller

log = logging.getLogger('tgext.debugbar')


class DebugBar():

    css_link = u'<link rel="stylesheet" type="text/css" href="%s" />'
    css_path = '/_debugbar/statics/style.css'
    template = 'tgext.debugbar.templates.debugbar'

    def __init__(self, app_config):
        self.app_config = app_config

    def __call__(self):
        if not config.get('debug', False):
            return

        if 'genshi' not in self.app_config.renderers:
            self.app_config.renderers.append('genshi')

        log.log(logging.INFO, 'Enabling Debug Toolbar')
        for sec in __sections__:
            if not sec.is_active:
                continue

            log.log(logging.DEBUG, 'Enabling Section: %s' % sec.name)
            for hook_name, hooks in sec.hooks.iteritems():
                for hook in hooks:
                    if hook_name == 'startup':
                        hook()
                    else:
                        self.app_config.register_hook(hook_name, hook)

        self.app_config.register_hook('after_render', self.render_first)

    def render_first(self, response):
        try:
            self.app_config.hooks['after_render'].remove(self.render_first)
        except ValueError:
            pass  # pre-empted by another request
        else:
            get_root_controller()._debugbar = DebugBarController()
            self.app_config.register_hook('after_render', self.render_bars)
        self.render_bars(response)

    def render_bars(self, response):
        page = response.get('response')
        if (not page or not isinstance(page, unicode)
                or 'text/html' not in response['content_type']
                or request.headers.get(
                    'X-Requested-With') == 'XMLHttpRequest'):
            return
        pos_head = page.find('</head>')
        if pos_head > 0:
            pos_body = page.find('</body>', pos_head + 7)
            if pos_body > 0:
                response['response'] = ''.join(
                    [page[:pos_head],
                    literal(self.css_link % url(self.css_path)),
                    page[pos_head:pos_body],
                    literal(render(dict(sections=__sections__),
                        'genshi', self.template,).split('\n', 1)[-1]),
                    page[pos_body:]])


def enable_debugbar(app_config):
    app_config.register_hook('startup', DebugBar(app_config))

