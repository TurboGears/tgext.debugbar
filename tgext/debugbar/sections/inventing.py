import hashlib
from datetime import datetime

from tg import config
from tg.render import render
from tg.i18n import ugettext as _

from paste.deploy.converters import asbool
from tgext.debugbar.sections.base import DebugSection

from markupsafe import Markup

_reload_datetime = datetime.now().strftime('%Y%m%d%H%M%S')

def on_after_render(response, *args, **kw):
    content_type = response.get('content_type', '')
    template = response.get('template_name')
    page = response.get('response')

    if content_type and 'text/html' in content_type and template and isinstance(page, unicode):
        m = hashlib.md5()
        m.update(page.encode('utf-8'))
        m = m.hexdigest() + _reload_datetime

        pos_head = page.find('</head>')
        if pos_head > 0:
            pos_body = page.find('</body>', pos_head + 7)
            if pos_body > 0:
                response['response'] = ''.join([page[:pos_head],
                                                Markup('<script>var tgext_debugbar_page_hash="%s";</script>' % m),
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

        result = u''
        result += Markup(self.js_reloadscript)
        if inventing_enabled:
            result += Markup('<script>tgext_debugbar_init_inventing()</script>')
        result += render(dict(enabled=inventing_enabled),
                         'genshi', 'tgext.debugbar.sections.templates.inventing')
        return result

