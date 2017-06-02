# coding: utf-8
"""tornado IOLoop API with zmq compatibility

If you have tornado ≥ 3.0, this is a subclass of tornado's IOLoop,
otherwise we ship a minimal subset of tornado in zmq.eventloop.minitornado.

The minimal shipped version of tornado's IOLoop does not include
support for concurrent futures - this will only be available if you
have tornado ≥ 3.0.
"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

from __future__ import absolute_import, division, with_statement

import time
import warnings


try:
    import tornado
    tornado_version = tornado.version_info
except (ImportError, AttributeError):
    tornado_version = ()

try:
    # tornado ≥ 4
    from tornado import ioloop
    if not hasattr(ioloop.IOLoop, 'configurable_default'):
        raise ImportError("Tornado too old")
    from tornado.ioloop import PollIOLoop, PeriodicCallback
    from tornado.log import gen_log
except ImportError:
    from .minitornado import ioloop
    from .minitornado.ioloop import PollIOLoop, PeriodicCallback
    from .minitornado.log import gen_log


class DelayedCallback(PeriodicCallback):
    """Schedules the given callback to be called once.

    The callback is called once, after callback_time milliseconds.

    `start` must be called after the DelayedCallback is created.
    
    The timeout is calculated from when `start` is called.
    """
    def __init__(self, callback, callback_time, io_loop=None):
        # PeriodicCallback require callback_time to be positive
        warnings.warn("""DelayedCallback is deprecated.
        Use loop.add_timeout instead.""", DeprecationWarning)
        callback_time = max(callback_time, 1e-3)
        super(DelayedCallback, self).__init__(callback, callback_time, io_loop)
    
    def start(self):
        """Starts the timer."""
        self._running = True
        self._firstrun = True
        self._next_timeout = time.time() + self.callback_time / 1000.0
        self.io_loop.add_timeout(self._next_timeout, self._run)
    
    def _run(self):
        if not self._running: return
        self._running = False
        try:
            self.callback()
        except Exception:
            gen_log.error("Error in delayed callback", exc_info=True)


class ZMQIOLoop(ioloop.IOLoop.configurable_default()):
    """DEPRECATED: No longer needed as of pyzmq-17"""

    def __init__(self, *args, **kwargs):
        warnings.warn("ZMQLoop is deprecated in pyzmq 17. No special eventloop integration is needed.", DeprecationWarning)
        return super(ZMQIOLoop, self).__init__(*args, **kwargs)
    
    def initialize(self, *args, **kwargs):
        super(ZMQIOLoop, self).initialize(*args, **kwargs)
    
    @classmethod
    def instance(cls, *args, **kwargs):
        """Returns a global `IOLoop` instance.
        
        Most applications have a single, global `IOLoop` running on the
        main thread.  Use this method to get this instance from
        another thread.  To get the current thread's `IOLoop`, use `current()`.
        """
        # install ZMQIOLoop as the active IOLoop implementation
        # when using tornado 3
        if tornado_version >= (3,):
            PollIOLoop.configure(cls)
        loop = PollIOLoop.instance(*args, **kwargs)
        if not isinstance(loop, cls):
            warnings.warn("IOLoop.current expected instance of %r, got %r" % (cls, loop),
                RuntimeWarning, stacklevel=2,
            )
        return loop
    
    @classmethod
    def current(cls, *args, **kwargs):
        """Returns the current thread’s IOLoop.
        """
        # install ZMQIOLoop as the active IOLoop implementation
        # when using tornado 3
        if tornado_version >= (3,):
            PollIOLoop.configure(cls)
        loop = PollIOLoop.current(*args, **kwargs)
        if not isinstance(loop, cls):
            warnings.warn("IOLoop.current expected instance of %r, got %r" % (cls, loop),
                RuntimeWarning, stacklevel=2,
            )
        return loop


# public API name
IOLoop = ZMQIOLoop


def install():
    """DEPRECATED
    
    pyzmq 17 no longer needs any special integration for tornado.
    """
    import warnings
    warnings.warn("zmq.eventloop.install is deprecated in pyzmq-17.0. "
    "No special integration is needed.", DeprecationWarning)
    return
