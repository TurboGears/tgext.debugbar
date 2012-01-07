from __future__ import with_statement

import threading
import time
import weakref

try:
    import json
except:
    import simplejson as json

import tg
from tg import config, request, app_globals
from tg.i18n import ugettext as _
from tg.render import render

from tgext.debugbar.sections.base import DebugSection
from tgext.debugbar.utils import format_sql

lock = threading.Lock()

try:
    from sqlalchemy import event
    from sqlalchemy.engine.base import Engine

    @event.listens_for(Engine, "before_cursor_execute")
    def _before_cursor_execute(conn, cursor, stmt, params, context, execmany):
        setattr(conn, 'tgdb_start_timer', time.time())

    @event.listens_for(Engine, "after_cursor_execute")
    def _after_cursor_execute(conn, cursor, stmt, params, context, execmany):
        stop_timer = time.time()
        try:
            req = request._current_obj()
        except:
            req = None

        if req is not None:
            with lock:
                engines = getattr(app_globals, 'tgdb_sqla_engines', {})
                engines[id(conn.engine)] = weakref.ref(conn.engine)
                setattr(app_globals, 'tgdb_sqla_engines', engines)
                queries = getattr(req, 'tgdb_sqla_queries', [])
                queries.append({
                    'engine_id': id(conn.engine),
                    'duration': (stop_timer - conn.tgdb_start_timer) * 1000,
                    'statement': stmt,
                    'parameters': params,
                    'context': context
                })
                req.tgdb_sqla_queries = queries
        delattr(conn, 'tgdb_start_timer')

    has_sqla = True
except ImportError:
    has_sqla = False


class SQLADebugSection(DebugSection):

    name = 'SQLAlchemy'

    @property
    def is_active(self):
        if not has_sqla:
            return False

        return config.get('use_sqlalchemy', False)

    def title(self):
        return _('SQLAlchemy')

    def content(self):
        queries = getattr(request, 'tgdb_sqla_queries', [])
        if not queries:
            return 'No queries in executed by the controller.'

        data = []
        for query in queries:
            is_select = query['statement'].strip().lower().startswith('select')
            params = ''
            try:
                params = json.dumps(query['parameters'])
            except TypeError:
                return 'Unable to serialize parameters of the query'

            data.append({
                'engine_id': query['engine_id'],
                'duration': query['duration'],
                'sql': format_sql(query['statement']),
                'raw_sql': query['statement'],
                'params': params,
                'is_select': is_select,
                'context': query['context'],
            })

        delattr(request, 'tgdb_sqla_queries')
        return unicode(render(
            dict(queries=data, tg=tg),
            'genshi', 'tgext.debugbar.sections.templates.sqla'
            ).split('\n', 1)[-1])
