import time, threading

from tg import request
from tg.i18n import ugettext as _
from tg.render import render

from tgext.debugbar.sections.base import DebugSection
from tgext.debugbar.utils import format_fname

try:
    import cPprofile as profile
except ImportError:
    try:
        import profile
    except:
        profile = None

try:
    import pstats
except ImportError:
    pstats = None

def on_before_render(*args, **kw):
    request.tgdb_render_start_time = time.time()


def on_after_render(response, *args, **kw):
    now = time.time()
    request.tgdb_render_info = response
    request.tgdb_render_time = (now - request.tgdb_render_start_time) * 1000

    try:
        request.tgdb_total_time = (now - request.tgdb_call_start_time) * 1000
    except:
        request.tgdb_total_time = -1
        request.tgdb_call_start_time = -1
        request.tgdb_call_time = -1
        request.tgdb_profiling_function_calls = []
        request.tgdb_profiling_stats = []


def profile_wrapper(decoration, controller):

    def wrapped_controller(*args, **kw):
        profiler = profile.Profile()

        try:
            request.tgdb_call_start_time = time.time()
            result = profiler.runcall(controller, *args, **kw)
            request.tgdb_call_time = (
                time.time() - request.tgdb_call_start_time) * 1000
        except:
            raise
        finally:
            stats = pstats.Stats(profiler)
            function_calls = []
            flist = stats.sort_stats('cumulative').fcn_list
            for func in flist:
                current = {}
                info = stats.stats[func]

                # Number of calls
                if info[0] != info[1]:
                    current['ncalls'] = '%d/%d' % (info[1], info[0])
                else:
                    current['ncalls'] = info[1]

                # Total time
                current['tottime'] = info[2] * 1000

                # Quotient of total time divided by number of calls
                if info[1]:
                    current['percall'] = info[2] * 1000 / info[1]
                else:
                    current['percall'] = 0

                # Cumulative time
                current['cumtime'] = info[3] * 1000

                # Quotient of the cumulative time divded by the number
                # of primitive calls.
                if info[0]:
                    current['percall_cum'] = info[3] * 1000 / info[0]
                else:
                    current['percall_cum'] = 0

                # Filename
                filename = pstats.func_std_string(func)
                current['filename_long'] = filename
                current['filename'] = format_fname(filename)
                function_calls.append(current)

            request.tgdb_profiling_stats = stats
            request.tgdb_profiling_function_calls = function_calls

        return result

    return wrapped_controller


class TimingDebugSection(DebugSection):

    name = 'Timings'
    is_active = True
    hooks = dict(controller_wrapper=[profile_wrapper],
                 before_render=[on_before_render],
                 after_render=[on_after_render])

    def title(self):
        return _('Timings')

    def content(self):
        try:
            return unicode(render(dict(
                    render_info=request.tgdb_render_info,
                    stats=request.tgdb_profiling_stats,
                    function_calls=request.tgdb_profiling_function_calls,
                    vars={'Total Time': request.tgdb_total_time,
                        'Controller Time': request.tgdb_call_time,
                        'Render Time': request.tgdb_render_time}),
                'genshi', 'tgext.debugbar.sections.templates.timing'
                ).split('\n', 1)[-1])
        finally:
            delattr(request, 'tgdb_render_info')
            delattr(request, 'tgdb_call_start_time')
            delattr(request, 'tgdb_call_time')
            delattr(request, 'tgdb_render_start_time')
            delattr(request, 'tgdb_total_time')
            delattr(request, 'tgdb_render_time')
            delattr(request, 'tgdb_profiling_stats')
            delattr(request, 'tgdb_profiling_function_calls')
