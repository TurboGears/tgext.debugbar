import logging

from markupsafe import Markup

import tg
from tg import request, url
from tg._compat import unicode_text
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

try:
    # TG >= 2.4
    from tg import ApplicationConfigurator
except ImportError:
    # TG < 2.4
    class ApplicationConfigurator: pass

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
            # 2.1+
            self.app_config.register_hook(hook_name, handler)
        elif hasattr(tg_hooks, 'wrap_controller'):
            # 2.3+
            if hook_name == 'controller_wrapper':
                def _accept_decoration(decoration, controller):
                    return handler(controller)
                tg_hooks.wrap_controller(_accept_decoration)
            else:
                tg_hooks.register(hook_name, handler)
        else:
            # 2.4+
            if hook_name == 'controller_wrapper':
                from tg import ApplicationConfigurator
                dispatch = ApplicationConfigurator.current().get_component('dispatch')
                if dispatch is None:
                    raise RuntimeError('TurboGears application configured without dispatching')
                dispatch.register_controller_wrapper(handler)
            else:
                tg_hooks.register(hook_name, handler)

    def _disconnect_hook(self, hook_name, handler):
        if tg_hooks is None:
            self.app_config.hooks[hook_name].remove(handler)
        else:
            tg_hooks.disconnect(hook_name, handler)

    def __call__(self, configurator=None, conf=None):
        if conf is None:
            conf = tg.config
        
        if not conf.get('debug', False):
            return

        conf['debugbar.engine'] = next(
            iter(sorted(set(('genshi', 'kajiki')) & set(conf['renderers']),
                        key=lambda x: x == conf['default_renderer'],
                        reverse=True)),
            None
        )
        if not conf['debugbar.engine']:
            log.error("Genshi or Kajiki rendering engines unavailable. Please install kajiki "
                      "and add base_config.renderers.append('kajiki') to your app_cfg.py")
            raise RuntimeError('Debugbar requires Genshi or Kajiki rendering engines')

        log.log(logging.INFO, 'Enabling Debug Toolbar')
        for sec in __sections__:
            if not sec.is_active:
                continue

            log.log(logging.DEBUG, 'Enabling Section: %s' % sec.name)
            for hook_name, hooks in sec.hooks.items():
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
        if (not page or not isinstance(page, unicode_text)
                or 'text/html' not in response['content_type']
                or request.headers.get(
                    'X-Requested-With') == 'XMLHttpRequest'):

            if tg.config.get('debugbar.enable_logs', False):
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
                                  tg.config['debugbar.engine'], self.template,).split('\n', 1)[-1]),
                    page[pos_body:]])


def enable_debugbar(app_config):
    if isinstance(app_config, ApplicationConfigurator):
        tg_hooks.register('initialized_config', DebugBar(app_config))
    else:
        if tg_hooks is None:
            app_config.register_hook('startup', DebugBar(app_config))
        else:
            tg_hooks.register('startup', DebugBar(app_config))
