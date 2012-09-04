from initialize import DebugBar, enable_debugbar

def plugme(app_config, options):
    app_config['debugbar.inventing'] = options.get('inventing', False)
    enable_debugbar(app_config)
    return dict(appid='tgext.debugbar')
