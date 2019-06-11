from .initialize import DebugBar, enable_debugbar


def plugme(app_config, options):
    try:
        app_config.update_blueprint({
            'debugbar.inventing': options.get('inventing', False),
            'debugbar.inventing_css': options.get('inventing_css', True),
            'debugbar.enable_logs': options.get('enable_logs', False)
        })
    except AttributeError:
        app_config['debugbar.inventing'] = options.get('inventing', False)
        app_config['debugbar.inventing_css'] = options.get('inventing_css', True)
        app_config['debugbar.enable_logs'] = options.get('enable_logs', False)
    
    enable_debugbar(app_config)
    return dict(appid='tgext.debugbar')
