from __future__ import with_statement

import threading
import time
import weakref
import logging
import datetime

from tg._compat import unicode_text

try:
    import json
except:
    import simplejson as json

class ExtendedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)
json_encoder = ExtendedJSONEncoder()

import tg
from tg import config, request, app_globals
from tg.i18n import ugettext as _
from tg.render import render

from tgext.debugbar.sections.base import DebugSection
from tgext.debugbar.utils import format_sql

log = logging.getLogger('tgext.debugbar.sqla')
lock = threading.Lock()

try:
    from sqlalchemy import event
    from sqlalchemy.engine.base import Engine

    def _before_cursor_execute(conn, cursor, stmt, params, context, execmany):
        setattr(conn, 'tgdb_start_timer', time.time())

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


def enable_sqlalchemy(*args, **kw):
    if has_sqla:
        event.listen(Engine, "before_cursor_execute", _before_cursor_execute)
        event.listen(Engine, "after_cursor_execute", _after_cursor_execute)


class SQLADebugSection(DebugSection):

    name = 'SQLAlchemy'
    hooks = dict(startup=[enable_sqlalchemy])

    @property
    def is_active(self):
        if not has_sqla:
            return False

        return config.get('use_sqlalchemy', False)

    def title(self):
        return _('SQLAlchemy')

    def _gather_queries(self):
        queries = getattr(request, 'tgdb_sqla_queries', [])
        if not queries:
            return []

        data = []
        for query in queries:
            is_select = query['statement'].strip().lower().startswith('select')
            params = ''
            try:
                params = json_encoder.encode(query['parameters'])
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
        return data

    def log_content(self):
        data = self._gather_queries()
        for query in data:
            explain_link = tg.url('/_debugbar/perform_sql', qualified=True, params=dict(stmt=query['raw_sql'], params=query['params'], engine_id=query['engine_id'], duration=query['duration'], modify='explain'))
            log.info('%s %s -> %s\n\t%s', request.path, query['params'], query['raw_sql'], explain_link)

    def content(self):
        data = self._gather_queries()
        if not data:
            return 'No queries in executed by the controller.'

        if isinstance(data, str):
            return data

        return unicode_text(render(dict(queries=data, tg=tg),
                              config['debugbar.engine'],
                              'tgext.debugbar.sections.templates.sqla!html').split('\n', 1)[-1])
