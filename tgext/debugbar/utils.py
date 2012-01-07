import sys
import os

from tg import config

try:
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import SqlLexer, JavascriptLexer
    from pygments.lexer import using, bygroups
    from pygments.token import Punctuation, Other, Generic
    from pygments.styles import get_style_by_name
    SQL_STYLE = get_style_by_name('colorful')
    JSON_STYLE = get_style_by_name('tango')

    class InsideStringJavascriptLexer(JavascriptLexer):
        def get_tokens_unprocessed(self, text, stack=('root',)):
            text = text[1:-1]
            text = text.replace('\\n', '\n')
            return JavascriptLexer.get_tokens_unprocessed(self, text, stack)

    mongo_tokens = {}
    mongo_tokens.update(JavascriptLexer.tokens)
    mongo_tokens['root'].insert(0, (r'"(function(\\\\|\\"|[^"])*)"',
        using(InsideStringJavascriptLexer)))

    class MongoLexer(JavascriptLexer):
        tokens = mongo_tokens

    HAVE_PYGMENTS = True
except ImportError:  # pragma: no cover
    HAVE_PYGMENTS = False


def get_root_controller():
    """Return the root controller of the application."""
    module = config['application_root_module']
    if module not in sys.modules:
        __import__(module)
    return sys.modules[module].RootController


def format_sql(query):
    """Format the given SQL query."""
    if not HAVE_PYGMENTS:  # pragma: no cover
        return query

    return highlight(
        query,
        SqlLexer(encoding='utf-8'),
        HtmlFormatter(encoding='utf-8', noclasses=True, style=SQL_STYLE))


def format_json(json):
    """Format the given JSON string."""
    if not HAVE_PYGMENTS:  # pragma: no cover
        return json

    return highlight(
        json,
        MongoLexer(encoding='utf-8'),
        HtmlFormatter(encoding='utf-8', noclasses=True, style=JSON_STYLE))


def common_segment_count(path, value):
    """Return the number of path segments common to both"""
    i = 0
    if len(path) <= len(value):
        for x1, x2 in zip(path, value):
            if x1 == x2:
                i += 1
            else:
                return 0
    return i


def format_fname(value, _sys_path=None):
    """Format the given file name."""
    if _sys_path is None:
        _sys_path = sys.path  # dependency injection
    # If the value is not an absolute path, the it is a built-in
    # or a relative file (thus a project file).
    if not os.path.isabs(value):
        if value.startswith(('{', '<')):
            return value
        if value.startswith('.' + os.path.sep):
            return value
        return '.' + os.path.sep + value

    # Loop through sys.path to find the longest match and return
    # the relative path from there.
    prefix_len = 0
    value_segs = value.split(os.path.sep)
    for path in _sys_path:
        count = common_segment_count(path.split(os.path.sep), value_segs)
        if count > prefix_len:
            prefix_len = count
    return '<%s>' % os.path.sep.join(value_segs[prefix_len:])
