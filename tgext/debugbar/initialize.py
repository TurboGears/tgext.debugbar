import logging

from markupsafe import Markup

from tg import config, request, url
from tg.render import render

try:
    # Verify that we have hooks with disconnect feature,
    # which is only available since TG2.3.5, otherwise
    # use app_config to register/disconnect hooks.
    from tg import hooks as tg_hooks
    if not hasattr(tg_hooks, 'disconnect'):
        tg_hooks = None
except ImportError:
    tg_hooks = None

from tgext.debugbar.sections import __sections__
from tgext.debugbar.utils import get_root_controller

log = logging.getLogger('tgext.debugbar')


class DebugBar():
    css_link = u'<link rel="stylesheet" type="text/css" href="%s" />'
    css_path = '/_debugbar/statics/style.css'
    template = 'tgext.debugbar.templates.debugbar!html'

    def __init__(self, app_config):
        self.app_config = app_config
        self.available_engines = None

    def _register_hook(self, hook_name, handler):
        if tg_hooks is None:
            self.app_config.register_hook(hook_name, handler)
        else:
            if hook_name == 'controller_wrapper':
                tg_hooks.wrap_controller(handler)
            else:
                tg_hooks.register(hook_name, handler)

    def _disconnect_hook(self, hook_name, handler):
        if tg_hooks is None:
            self.app_config.hooks[hook_name].remove(handler)
        else:
            tg_hooks.disconnect(hook_name, handler)

    def __call__(self):
        if not config.get('debug', False):
            return

        config['debugbar.engine'] = next(
            iter(sorted(set(('genshi', 'kajiki')) & set(self.app_config['renderers']),
                        key=lambda x: x == self.app_config['default_renderer'],
                        reverse=True)),
            None
        )
        if not config['debugbar.engine']:
            log.error("Genshi or Kajiki rendering engines unavailable. Please install kajiki "
                      "and add base_config.renderers.append('kajiki') to your app_cfg.py")
            raise RuntimeError('Debugbar requires Genshi or Kajiki rendering engines')

        log.log(logging.INFO, 'Enabling Debug Toolbar')
        for sec in __sections__:
            if not sec.is_active:
                continue

            log.log(logging.DEBUG, 'Enabling Section: %s' % sec.name)
            for hook_name, hooks in sec.hooks.iteritems():
                for handler in hooks:
                    if hook_name == 'startup':
                        handler()
                    else:
                        try:
                            self._register_hook(hook_name, handler)
                        except:
                            log.exception('Unable to register hook: %s', hook_name)

        self._register_hook('after_render', self.render_first)

    def render_first(self, response):
        try:
            self._disconnect_hook('after_render', self.render_first)
        except ValueError:
            pass  # pre-emptied by another request
        else:
            from tgext.debugbar.controller import DebugBarController
            get_root_controller()._debugbar = DebugBarController()
            self._register_hook('after_render', self.render_bars)
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
                                  config['debugbar.engine'], self.template,).split('\n', 1)[-1]),
                    page[pos_body:]])


def enable_debugbar(app_config):
    if tg_hooks is None:
        app_config.register_hook('startup', DebugBar(app_config))
    else:
        tg_hooks.register('startup', DebugBar(app_config))
