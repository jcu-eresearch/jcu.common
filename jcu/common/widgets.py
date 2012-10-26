
from pyramid_deform import SessionFileUploadTempStore
import deform.widget
import colander

@colander.deferred
def file_upload_widget(node, kw):
    request = kw['request']
    tmpstore = SessionFileUploadTempStore(request)
    return deform.widget.FileUploadWidget(tmpstore)

