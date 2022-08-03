import logging

from plone.namedfile.utils import set_headers
from plone.namedfile.utils import stream_data

from plone.namedfile.browser import Download as Base
from plone.rfc822.interfaces import IPrimaryFieldInfo
from zope.publisher.interfaces import NotFound

from Products.Five.browser import BrowserView


LOG = logging.getLogger(__name__)


class Download(Base):
    def _getFile(self):
        if not self.fieldname:
            info = IPrimaryFieldInfo(self.context, None)
            if info is None:
                # Ensure that we have at least a filedname
                raise NotFound(self, '', self.request)
            self.fieldname = info.fieldname
            file = info.value
        else:
            context = getattr(self.context, 'aq_explicit', self.context)
            file = getattr(context, self.fieldname, None)

        if file is None:
            raise NotFound(self, self.fieldname, self.request)

        return file


class MultiDownload(BrowserView):
    def __call__(self):
        index = self.request.get("index")
        if index:
            attachments = getattr(self.context, "attachments", [])
            try:
                idx = int(index)
                return self.stream(attachments[idx])
            except Exception:
                LOG.exception("Could not retrieve file for download!")

    def stream(self, blob_file):
        filename = blob_file.filename
        set_headers(blob_file, self.request.response, filename=filename)
        return stream_data(blob_file)

