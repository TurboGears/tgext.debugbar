import tg, logging
from webhelpers.html import literal
from tgext.debugbar.sections import __sections__
from tgext.debugbar.controller import DebugBarController
from tgext.debugbar.utils import get_root_controller

log = logging.getLogger('tgext.debugbar')

class DebugBarSetupper():
    def __init__(self, app_config):
        self.app_config = app_config

    def __call__(self):
        if not tg.config.get('debug', False):
            return

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

        self.app_config.register_hook('after_render', render_bars)

def mount_debugbar_controller(app):
    root = get_root_controller()
    root._debugbar = DebugBarController()
    return app

def render_bars(response):
    if 'text/html' not in response['content_type'] or not isinstance(response['response'], unicode):
        return

    resources = '''<link rel="stylesheet" type="text/css" href="/_debugbar/statics/style.css"></link>'''
    html = tg.render.render(dict(sections=__sections__), 'genshi',
        'tgext.debugbar.templates.debugbar').split('\n', 1)[-1]
    response['response'] = response['response'].replace(literal('</head>'),
                                                        literal('%s</head>' % resources))
    response['response'] = response['response'].replace(literal('</body>'),
                                                        literal('%s</body>' % html))

def enable_debugbar(app_config):
    app_config.register_hook('startup', DebugBarSetupper(app_config))
    app_config.register_hook('after_config', mount_debugbar_controller)
