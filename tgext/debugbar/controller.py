import tg, sys, os, json
from tg import expose, app_globals
from tg.controllers import TGController, WSGIAppController
from paste.urlparser import StaticURLParser
from webob.exc import HTTPBadRequest
from utils import format_sql, format_json

statics_path = os.path.join(os.path.split(sys.modules['tgext.debugbar'].__file__)[0], 'statics')

class StaticsController(TGController):
    @expose()
    def _lookup(self, *args):
        return WSGIAppController(StaticURLParser(statics_path)), args

class DebugBarController(TGController):
    statics = StaticsController()

    @expose('tgext.debugbar.templates.perform_sql')
    def perform_sql(self, stmt, params, engine_id, duration):
        # Make sure it is a select statement
        if not stmt.lower().strip().startswith('select'):
          raise HTTPBadRequest('Not a SELECT SQL statement')

        if not engine_id:
          raise HTTPBadRequest('No valid database engine')

        engine = getattr(app_globals, 'tgdb_sqla_engines')[int(engine_id)]()
        result = engine.execute(stmt, json.loads(params))

        return {
          'result': result.fetchall(),
          'params': params,
          'headers': result.keys(),
          'sql': format_sql(stmt),
          'duration': float(duration),
        }

    @expose('tgext.debugbar.templates.explain_sql')
    def explain_sql(self, stmt, params, engine_id, duration):
        # Make sure it is a select statement
        if not stmt.lower().strip().startswith('select'):
          raise HTTPBadRequest('Not a SELECT SQL statement')

        if not engine_id:
          raise HTTPBadRequest('No valid database engine')

        engine = getattr(app_globals, 'tgdb_sqla_engines')[int(engine_id)]()

        if engine.name.startswith('sqlite'):
            query = 'EXPLAIN QUERY PLAN %s' % stmt
        else:
            query = 'EXPLAIN %s' % stmt

        result = engine.execute(query, json.loads(params))

        return {
          'result': result.fetchall(),
          'params': params,
          'headers': result.keys(),
          'sql': format_sql(stmt),
          'duration': float(duration),
        }

    @expose('tgext.debugbar.templates.perform_ming')
    def perform_ming(self, collection, command, params, duration):
        if not command.startswith('find'):
            raise HTTPBadRequest('Not a find statement')

        query_params = json.loads(params)
        session =  tg.config['package'].model.DBSession

        cursor = []
        for i, step in enumerate(command.split('.')):
            if step == 'find':
                args = query_params[i]
                cursor = session.find(collection, args)
            else:
                args = query_params[i]
                cmd = getattr(cursor, step)
                cursor = cmd(*args)

        return {
          'result': cursor,
          'params': format_json(params),
          'action': command,
          'collection': collection,
          'duration': float(duration),
        }
