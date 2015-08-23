import logging

from markupsafe import Markup

from tg import config, request, url
from tg import hooks as tg_hooks
from tg.render import render

from tgext.debugbar.sections import __sections__
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
                        try:
                            if hook_name == 'controller_wrapper':
                                tg_hooks.wrap_controller(hook)
                            else:
                                tg_hooks.register(hook_name, hook)
                        except:
                            log.exception('Unable to register hook: %s', hook_name)

        tg_hooks.register('after_render', self.render_first)

    def render_first(self, response):
        try:
            tg_hooks.disconnect('after_render', self.render_first)
        except ValueError:
            pass  # pre-empted by another request
        else:
            from tgext.debugbar.controller import DebugBarController
            get_root_controller()._debugbar = DebugBarController()
            tg_hooks.register('after_render', self.render_bars)
        self.render_bars(response)

    def render_bars(self, response):
        page = response.get('response')
        if (not page or not isinstance(page, unicode)
                or 'text/html' not in response['content_type']
                or request.headers.get(
                    'X-Requested-With') == 'XMLHttpRequest'):

            if config.get('debugbar.enable_logs', False):
                for section in __sections__:
                    if hasattr(section, 'log_content'):
                        section.log_content()

            return

        pos_head = page.find('</head>')
        if pos_head > 0:
            pos_body = page.find('</body>', pos_head + 7)
            if pos_body > 0:
                response['response'] = ''.join(
                    [page[:pos_head],
                    Markup(self.css_link % url(self.css_path)),
                    page[pos_head:pos_body],
                    Markup(render(dict(sections=__sections__),
                        'genshi', self.template,).split('\n', 1)[-1]),
                    page[pos_body:]])


def enable_debugbar(app_config):
    tg_hooks.register('startup', DebugBar(app_config))
