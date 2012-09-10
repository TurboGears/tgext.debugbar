from initialize import DebugBar, enable_debugbar

def plugme(app_config, options):
    app_config['debugbar.inventing'] = options.get('inventing', False)
    app_config['debugbar.inventing_css'] = options.get('inventing_css', True)
    enable_debugbar(app_config)
    return dict(appid='tgext.debugbar')
