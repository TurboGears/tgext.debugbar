"""The base debug section class."""


class DebugSection(object):

    name = "Unnamed"
    is_active = False
    hooks = dict(
        startup=[],
        shutdown=[],
        before_validate=[],
        before_call=[],
        before_render=[],
        after_render=[])

    def title(self):
        raise NotImplementedError

    def content(self):
        raise NotImplementedError
