About Debug Toolbar
-------------------------

tgext.debugbar provides a Debug Toolbar for TurboGears2 framework.

Exposed sections are:

* Controller and Rendering time reporting
* Controller Profiling
* Request Parameters, Headers, Attributes and Environ
* SQLAlchemy Queries reporting and timing
* Explain and Show result of performed SQLAlchemy queries
* List mounted controllers, their path and exposed methods
* Log Messages

Installing
-------------------------------

tgext.debugbar can be installed both from pypi or from bitbucket::

    easy_install tgext.debugbar

should just work for most of the users

Using it
----------------------------------

To use the debug toolbar all is needed is to add a few
lines to your project ``app_cfg.py``::

    from tgext.debugbar import enable_debugbar
    enable_debugbar(base_config)

The ``enable_debugbar`` function will then check for
the ``debug`` config option disabling the debugbar
when it is false.
