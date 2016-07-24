import sys
import os
import pprint

try:
    import json
except:
    import simplejson as json

from tg import app_globals, config, expose, request
from tg.controllers import TGController, WSGIAppController
from webob.exc import HTTPBadRequest
from .utils import format_sql, format_json
from .sections import __sections__

STATICS_PATH = os.path.join(os.path.split(sys.modules['tgext.debugbar'].__file__)[0], 'statics')


try:
    from webob.static import DirectoryApp
except ImportError:
    from paste.urlparser import StaticURLParser as DirectoryApp

try:
    from pymongo import json_util
except ImportError:
    try:
        from bson import json_util
    except ImportError:
        pass


class StaticsController(TGController):
    _directory_app = DirectoryApp(STATICS_PATH)

    @expose()
    def _default(self, *args):
        new_req = request.copy()
        to_pop = len(new_req.path_info.strip('/').split('/')) - len(args)
        for i in range(to_pop):
            new_req.path_info_pop()
        return new_req.get_response(self._directory_app)


class DebugBarController(TGController):
    statics = StaticsController()

    @expose('genshi:tgext.debugbar.templates.perform_sql!html')
    @expose('kajiki:tgext.debugbar.templates.perform_sql!html')
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

    @expose('genshi:tgext.debugbar.templates.perform_ming!html')
    @expose('kajiki:tgext.debugbar.templates.perform_ming!html')
    def perform_ming(self, collection, command, params, duration, modify=None):
        if not command.startswith('find'):
            raise HTTPBadRequest('Not a find statement')

        query_params = json.loads(params, object_hook=json_util.object_hook)
        session = config['package'].model.DBSession

        cursor = []
        for i, step in enumerate(command.split('.')):
            if step == 'find':
                args = query_params[i]
                query = args[0]
                options = args[1]
                cursor = session.find(collection, query, **options)
            else:
                args = query_params[i]
                cmd = getattr(cursor, step)
                cursor = cmd(*args)

        isexplain = False
        if modify and modify.lower() == 'explain':
            cursor = cursor.ming_cursor.cursor.explain()
            isexplain = True

        return dict(
            pformat=pprint.pformat,
            action=command,
            params=format_json(params),
            result=cursor,
            collection=collection,
            duration=float(duration),
            isexplain=isexplain)
