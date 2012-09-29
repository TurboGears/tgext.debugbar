import hashlib, re, logging, os, time
from datetime import datetime

from tg import config, tmpl_context
from tg.render import render
from tg.i18n import ugettext as _

from paste.deploy.converters import asbool
from tgext.debugbar.sections.base import DebugSection

from markupsafe import Markup

log = logging.getLogger('tgext.debugbar')

_reload_datetime = datetime.now().strftime('%Y%m%d%H%M%S')
_href_re = re.compile(r'''href=["\']([^\'\"]+)[\'"]''', re.UNICODE|re.IGNORECASE)

def detect_stylesheets(page):
    try:
        base_dir = config['pylons.paths']['static_files']
    except:
        log.warn('Unable to detect static files path, skipping inventing mode on stylesheets')
        return []

    files = []

    line = page.find('stylesheet')
    while line >= 0:
        css_link = _href_re.search(page[line:])
        if css_link:
            css_file = css_link.group(1)
            css_file = css_file.replace('/', os.sep)
            if css_file.startswith(os.sep):
                css_file = css_file[1:]

            css_file = os.path.join(base_dir, css_file)
            if os.path.exists(css_file):
                files.append(css_file)
        line = page.find('stylesheet', line+1)

    return files

def on_after_render(response, *args, **kw):
    content_type = response.get('content_type', '')
    template = response.get('template_name')
    page = response.get('response')

    if content_type and 'text/html' in content_type and template and isinstance(page, unicode):
        m = hashlib.md5()
        m.update(page.encode('utf-8'))
        m = m.hexdigest() + _reload_datetime

        if config.get('debugbar.inventing_css', False):
            newest_modified_time = 0

            for f in detect_stylesheets(page):
                modified_time = os.path.getmtime(f)
                if modified_time > newest_modified_time:
                    newest_modified_time = modified_time

            if newest_modified_time:
                m += str(newest_modified_time)

        pos_head = page.find('</head>')
        if pos_head > 0:
            pos_body = page.find('</body>', pos_head + 7)
            if pos_body > 0:
                response['response'] = ''.join([page[:pos_head],
                                                Markup('<script>if(typeof tgext_debugbar_page_hash === "undefined") window.tgext_debugbar_page_hash="%s";</script>' % m),
                                                page[pos_head:pos_body],
                                                page[pos_body:]])

class InventingDebugSection(DebugSection):
    name = 'Inventing'
    is_active = True
    hooks = dict(after_render=[on_after_render])

    js_reloadscript = '''
<script>
function tgext_debugbar_check_changed() {
    DebugBarJQuery.ajax(window.location.href, {
        'success': function(data, textStatus, jqXHR) {
            var page_hash_re = /tgext_debugbar_page_hash="(.*)";/;
            var page_hash = page_hash_re.exec(data);
            if (page_hash && page_hash.length) {
                var page_hash = page_hash[1];
                if(page_hash != tgext_debugbar_page_hash) {
                    window.location.reload();
                    return
                }
            }
            DebugBarJQuery('#tgdb_debugbar #tgdb_barcontent').removeClass('tgdb_barcontent_error');
            DebugBarJQuery('#tgdb_debugbar #tgdb_barcontent').removeClass('tgdb_barcontent_warning');
            tgext_debugbar_init_inventing();
        },
        'error':function(jqXHR, textStatus, errorThrown) {
            DebugBarJQuery('#tgdb_debugbar #tgdb_barcontent').removeClass('tgdb_barcontent_error');
            DebugBarJQuery('#tgdb_debugbar #tgdb_barcontent').removeClass('tgdb_barcontent_warning');

            if (jqXHR.status && jqXHR.status >= 500) {
                DebugBarJQuery('#tgdb_debugbar #tgdb_barcontent').addClass('tgdb_barcontent_error');
            }
            else if (jqXHR.status && jqXHR.status < 500) {
                //Probably not an error in this case, yet to decide if to alert it somehow
            }
            else {
                DebugBarJQuery('#tgdb_debugbar #tgdb_barcontent').addClass('tgdb_barcontent_warning');
            }
            tgext_debugbar_init_inventing();
        }
    });

}

function tgext_debugbar_init_inventing() {
    setTimeout(tgext_debugbar_check_changed, 1000);
}
</script>'''

    def title(self):
        return _('Inventing')

    def content(self):
        inventing_enabled = asbool(config.get('debugbar.inventing', 'false'))
        inventing_enabled = getattr(tmpl_context, 'debugbar_inventing', inventing_enabled)

        result = u''
        result += Markup(self.js_reloadscript)
        if inventing_enabled:
            result += Markup('<script>tgext_debugbar_init_inventing()</script>')
        result += render(dict(enabled=inventing_enabled),
                         'genshi', 'tgext.debugbar.sections.templates.inventing')
        return result

