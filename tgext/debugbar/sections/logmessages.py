import datetime
import logging
import threading

from tg.i18n import ugettext as _
from tg.render import render

from tgext.debugbar.sections.base import DebugSection
from tgext.debugbar.utils import format_fname


class ThreadTrackingHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        self.records = {}

    def emit(self, record):
        self.get_records().append(record)

    def get_records(self, thread=None):
        if thread is None:
            thread = threading.currentThread()
        if thread not in self.records:
            self.records[thread] = []
        return self.records[thread]

    def clear_records(self, thread=None):
        if thread is None:
            thread = threading.currentThread()
        if thread in self.records:
            del self.records[thread]

handler = ThreadTrackingHandler()
logging.root.addHandler(handler)


class LoggingDebugSection(DebugSection):
    name = 'Logging'
    is_active = True

    def get_and_clear(self):
        records = handler.get_records()
        handler.clear_records()
        return records

    def title(self):
        return _('Logging')

    def content(self):
        records = []
        for record in self.get_and_clear():
            records.append({
                'message': record.getMessage(),
                'time': datetime.datetime.fromtimestamp(record.created),
                'level': record.levelname,
                'file': format_fname(record.pathname),
                'file_long': record.pathname,
                'line': record.lineno,
            })

        records = reversed(records)
        return unicode(render(
            dict(records=records),
            'genshi', 'tgext.debugbar.sections.templates.logging'
            ).split('\n', 1)[-1])
