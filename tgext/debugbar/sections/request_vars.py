from pprint import saferepr

import tg
from tg.i18n import ugettext as _
from tg.util import odict
from tg.render import render

from tgext.debugbar.sections.base import DebugSection


request_header_filter = (
    'CONTENT_TYPE',
    'QUERY_STRING',
    'REMOTE_ADDR',
    'REMOTE_HOST',
    'REQUEST_METHOD',
    'SCRIPT_NAME',
    'SERVER_NAME',
    'SERVER_PORT',
    'SERVER_PROTOCOL',
    'SERVER_SOFTWARE',
    'PATH_INFO',
)


class RequestDebugSection(DebugSection):
    name = 'Request'
    is_active = True

    def title(self):
        return _('Request')

    def content(self):
        vars = odict()
        request = tg.request._current_obj()
        response = tg.response._current_obj()
        attr_dict = request.environ['webob.adhoc_attrs'].copy()
        attr_dict['response'] = repr(response.__dict__)

        for entry in attr_dict.keys():
            if entry.startswith('tgdb_'):
                del attr_dict[entry]

        vars['GET'] = [(k, request.GET.getall(k)) for k in request.GET]
        vars['POST'] = [(k, [saferepr(p)
            for p in request.POST.getall(k)]) for k in request.POST]
        vars['Cookies'] = [(k, request.cookies.get(k))
            for k in request.cookies]
        vars['Headers'] = [(k, saferepr(v))
            for k, v in request.environ.iteritems()
            if k.startswith('HTTP_') or k in request_header_filter]
        vars['Request Attributes'] = [(k, saferepr(v))
            for k, v in attr_dict.iteritems() if not callable(v)]
        vars['Environ'] = [(k, saferepr(v))
            for k, v in request.environ.iteritems()]

        return unicode(render(
            dict(vars=vars),
            'genshi', 'tgext.debugbar.sections.templates.request'
            ).split('\n', 1)[-1])
