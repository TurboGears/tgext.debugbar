from initialize import enable_debugbar


def plugme(app_config, options):
    enable_debugbar(app_config)
    return dict(appid='tgext.debugbar')
