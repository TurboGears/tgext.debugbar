from sqla import SQLADebugSection
from timing import TimingDebugSection
from request_vars import RequestDebugSection
from controllers import ControllersDebugSection
from logmessages import LoggingDebugSection

__sections__ = [TimingDebugSection(), RequestDebugSection(), SQLADebugSection(),
                ControllersDebugSection(), LoggingDebugSection()]