import time
import inspect

try:
    import json
except:
    import simplejson as json

import tg
from tg import config, request
from tg.i18n import ugettext as _
from tg.render import render

from tgext.debugbar.sections.base import DebugSection
from tgext.debugbar.utils import format_json

try:
    import ming
    import ming.orm
    from ming.orm.ormsession import SessionExtension
    from pymongo import json_util

    class TraceCursorExtension(SessionExtension):

        def cursor_created(self, cursor, action, *args, **kw):
            if action in ('find'):
                cursor.tgdb_action = action
                cursor.tgdb_class = inspect.isclass(
                    args[0]) and args[0].__name__ or args[0]
                try:
                    cursor.tgdb_args = [args[1]]
                except:
                    cursor.tgdb_args = [{}]
            elif action in ('limit', 'sort', 'skip', 'hint'):
                parent_cursor = args[0]
                cursor.tgdb_action = parent_cursor.tgdb_action + '.' + action
                cursor.tgdb_class = parent_cursor.tgdb_class
                cursor.tgdb_args = parent_cursor.tgdb_args + [args[1:]]

        def before_cursor_next(self, cursor):
            cursor.tgdb_ming_timer = time.time()

        def after_cursor_next(self, cursor):
            spent = (time.time() - cursor.tgdb_ming_timer) * 1000

            try:
                req = request._current_obj()
            except Exception:
                req = None

            if req is not None:
                try:
                    active_cursors = req.tgdb_ming_cursors
                except Exception:
                    active_cursors = req.tgdb_ming_cursors = {}
                info = active_cursors.setdefault(id(cursor), {
                  'duration': 0,
                  'command': '',
                  'collection': '',
                  'params': ''})
                info['duration'] += spent
                if not hasattr(cursor, 'tgdb_action'):
                    return

                info['command'] = cursor.tgdb_action
                info['collection'] = cursor.tgdb_class
                info['params'] = cursor.tgdb_args

    has_ming = True
except ImportError:
    has_ming = False


def hook_ming(*args, **kw):
    global has_ming
    if not has_ming:
        return

    try:
        config['package'].model.DBSession.register_extension(
            TraceCursorExtension)
    except Exception:
        has_ming = False


class MingDebugSection(DebugSection):

    name = 'Ming'
    hooks = dict(startup=[hook_ming])

    @property
    def is_active(self):
        if not has_ming:
            return False

        return config.get('use_ming', False)

    def title(self):
        return _('Ming')

    def content(self):
        queries = getattr(request, 'tgdb_ming_cursors', [])
        if not queries:
            return 'No queries in executed by the controller.'

        data = []
        for query in queries.values():
            params = json.dumps(query['params'], default=json_util.default)
            data.append({
                'duration': query['duration'],
                'command': query['command'],
                'collection': query['collection'],
                'filter': format_json(params),
                'params': params
            })

        delattr(request, 'tgdb_ming_cursors')
        return unicode(render(
            dict(queries=data, tg=tg),
            'genshi', 'tgext.debugbar.sections.templates.ming'
            ).split('\n', 1)[-1])
