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

Using it with Pluggables
----------------------------------

Like any other pluggable extension, the debugbar can be
activated through the pluggables interface inside
your ``app_cfg.py``::

    from tgext.pluggable import plug
    plug(base_config, 'tgext.debugbar')

The debugbar will then check for the ``debug`` config option
disabling itself when it is false.

Using it without pluggable
----------------------------------

While the pluggables interface makes convenient to
pass options to the debugbar, you might want to avoid
using it for various reasons. In such cases you can
enable the debugbar by adding the following
lines to your project ``app_cfg.py``::

    from tgext.debugbar import enable_debugbar
    enable_debugbar(base_config)

Enabling Logs
-----------------------------------

Whenever your response is JSON or an ajax request, or any other
kind of content which is not a plain HTML page, the debugbar bar
is not injected inside your response.
This is to prevent it from messing with your output when it would
probably break things.

There are cases when you might be interested in getting access
to some informations from the debugbar even when your output
is not HTML. For example your might be interested in knowing
which queries have been performed to retrieve your JSON response.

To enable logging such informations you can pass the ``enable_logs=True``
option to the ``plug`` call which activates the debugbar.

Inventing Mode
-------------------------------------

The DebugBar provides the inventing mode, such feature is inspired
by the *Inventing On Principle* to speed up experimenting and prototyping
with your website. Whenever the inventing mode is enable your web page
will automatically update when you change it, being it a controller, template
or css change.

The inventing mode can be enabled by passing the ``inventing=True``
option to the ``plug`` call which activates the debugbar.

If you want to disable inventing mode for CSS files, you can enable the
inventing mode and then pass the ``inventing_css=False`` option.