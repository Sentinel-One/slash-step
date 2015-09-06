import logbook
from . import hooks
import inspect

def caller_name(skip=2):
    """Get a name of a caller in the format module.class.method

       `skip` specifies how many levels of stack to skip while getting caller
       name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.

       An empty string is returned if skipped levels exceed stack height
    """
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
      return ''
    parentframe = stack[start][0]

    name = []
    module = inspect.getmodule(parentframe)
    # `modname` can be None when frame is executed directly in console
    # TODO(techtonik): consider using __main__
    if module:
        name.append(module.__name__)
    # detect classname
    if 'self' in parentframe.f_locals:
        # I don't know any way to detect call from the object method
        # XXX: there seems to be no way to detect static method call - it will
        #      be just a function call
        name.append(parentframe.f_locals['self'].__class__.__name__)
    codename = parentframe.f_code.co_name
    if codename != '<module>':  # top level usually
        name.append( codename ) # function or a method
    del parentframe
    return ".".join(name)

_LOGGER_NAME = "slash.step"
_STEP_LOG_LEVEL = logbook.NOTICE

_logger = logbook.Logger(_LOGGER_NAME)


class Step(object):

    def __init__(self, msg, *args, **kwargs):
        super(Step, self).__init__()
        self.message = msg.format(*args, **kwargs) if args or kwargs else msg
        self.context = repr(caller_name())

    def __str__(self):
        return self.message

    def __repr__(self):
        return "<Step {0!r}>".format(self.message)

    def _start(self):
        _logger.log(_STEP_LOG_LEVEL, self.message)
        hooks.step_start.trigger({"message": self.message, "context": self.context})

    def _success(self):
        hooks.step_success.trigger({"message": self.message, "context": self.context})

    def _error(self):
        hooks.step_error.trigger({"message": self.message, "context": self.context})

    def _end(self):
        hooks.step_end.trigger({"message": self.message, "context": self.context})

    def __enter__(self):
        self._start()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        try:
            if exc_type is None:
                self._success()
            else:
                self._error()
        finally:
            self._end()
