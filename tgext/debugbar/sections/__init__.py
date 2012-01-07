from sqla import SQLADebugSection
from timing import TimingDebugSection
from request_vars import RequestDebugSection
from controllers import ControllersDebugSection
from logmessages import LoggingDebugSection
from mingorm import MingDebugSection

__sections__ = [
    TimingDebugSection(),
    RequestDebugSection(),
    SQLADebugSection(),
    MingDebugSection(),
    ControllersDebugSection(),
    LoggingDebugSection()
]
