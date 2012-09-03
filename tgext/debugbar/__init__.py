from initialize import DebugBar, enable_debugbar

try:
    from tgext.pluggable.plug import ApplicationPlugger
except ImportError:
    ApplicationPlugger = None

def plugme(app_config, options):
    if ApplicationPlugger:
        DebugBar(app_config)()
    else:
        enable_debugbar(app_config)
    return dict(appid='tgext.debugbar')
