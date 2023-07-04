from threading import local

from pylibmc import Client

from zope.interface import implementer

from plone.memoize.interfaces import ICacheChooser
from plone.memoize.ram import MemcacheAdapter


@implementer(ICacheChooser)
class MemcachedCacheChooser:
    _v_thread_local = local()

    def getClient(self):
        """Return thread local connection to memcached."""
        connection = getattr(self._v_thread_local, "connection", None)
        if connection is None:
            connection = Client(["127.0.0.1:11211"])
            self._v_thread_local.connection = connection

        return connection

    def __call__(self, fun_name):
        """Create new adapter for plone.memoize.ram."""
        return MemcacheAdapter(client=self.getClient(), globalkey=fun_name)