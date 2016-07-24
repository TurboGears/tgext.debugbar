import inspect

import tg
from tg._compat import unicode_text
from tg.controllers.decoratedcontroller import DecoratedController
from tg.i18n import ugettext as _
from tg.render import render

try:
    from tg.util import odict
except ImportError:
    from collections import OrderedDict as odict

from tgext.debugbar.sections.base import DebugSection
from tgext.debugbar.utils import get_root_controller


def map_controllers(path, controller, output):
    if inspect.isclass(controller):
        if not issubclass(controller, DecoratedController):
            return
    else:
        if isinstance(controller, DecoratedController):
            controller = controller.__class__
        else:
            return

    exposed_methods = {}
    output[path and path or '/'] = dict(
        controller=controller, exposed_methods=exposed_methods)
    for name, cont in controller.__dict__.items():
        if hasattr(cont, 'decoration') and cont.decoration.exposed:
            exposed_methods[name] = cont
        map_controllers(path + '/' + name, cont, output)


class ControllersDebugSection(DebugSection):
    name = 'Controllers'
    is_active = True

    def title(self):
        return _('Controllers')

    def content(self):
        controllers = odict()
        map_controllers('', get_root_controller(), controllers)
        return unicode_text(render(
            dict(controllers=controllers),
            tg.config['debugbar.engine'], 'tgext.debugbar.sections.templates.controllers!html'
            ).split('\n', 1)[-1])
