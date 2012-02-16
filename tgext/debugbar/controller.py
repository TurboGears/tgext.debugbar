import sys
import os

try:
    import json
except:
    import simplejson as json

from tg import app_globals, config, expose
from tg.controllers import TGController, WSGIAppController
from paste.urlparser import StaticURLParser
from webob.exc import HTTPBadRequest
from utils import format_sql, format_json

statics_path = os.path.join(
    os.path.split(sys.modules['tgext.debugbar'].__file__)[0], 'statics')

try:
    from pymongo import json_util
except:
    pass

class StaticsController(TGController):

    @expose()
    def _lookup(self, *args):
        return WSGIAppController(StaticURLParser(statics_path)), args


class DebugBarController(TGController):

    statics = StaticsController()

    @expose('genshi:tgext.debugbar.templates.perform_sql')
    def perform_sql(self, stmt, params, engine_id, duration, modify=None):
        # Make sure it is a select statement
        if not stmt.lower().lstrip().startswith('select'):
            raise HTTPBadRequest('Not a SELECT SQL statement')
        try:
            if not engine_id:
                raise ValueError
            engine_id = int(engine_id)
            engine = getattr(app_globals, 'tgdb_sqla_engines')[engine_id]()
        except (AttributeError, IndexError, ValueError):
            raise HTTPBadRequest('No valid database engine')

        if modify and modify.lower() == 'explain':
            if engine.name.startswith('sqlite'):
                stmt = 'EXPLAIN QUERY PLAN %s' % stmt
            else:
                stmt = 'EXPLAIN %s' % stmt
            title = 'Execution Plan'
        else:
            title = 'Query Results'

        result = engine.execute(stmt, json.loads(params))

        return dict(
            sql=format_sql(stmt),
            params=params,
            result=result.fetchall(),
            headers=result.keys(),
            duration=float(duration),
            title=title)

    @expose('genshi:tgext.debugbar.templates.perform_ming')
    def perform_ming(self, collection, command, params, duration):
        if not command.startswith('find'):
            raise HTTPBadRequest('Not a find statement')

        query_params = json.loads(params, object_hook=json_util.object_hook)
        session = config['package'].model.DBSession

        cursor = []
        for i, step in enumerate(command.split('.')):
            if step == 'find':
                args = query_params[i]
                cursor = session.find(collection, args)
            else:
                args = query_params[i]
                cmd = getattr(cursor, step)
                cursor = cmd(*args)

        return dict(
            action=command,
            params=format_json(params),
            result=cursor,
            collection=collection,
            duration=float(duration))
