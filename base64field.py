# Adapted from: https://gist.github.com/klipstein/709890

import base64
import mimetypes
import os
from tastypie.fields import FileField
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.fields.files import FieldFile
 
class Base64FileField(FileField):
    """
    A django-tastypie field for handling file-uploads through raw post data.
    It uses base64 for en-/decoding the contents of the file.
    Usage:
 
    class MyResource(ModelResource):
        file_field = Base64FileField("file_field")
        
        class Meta:
            queryset = ModelWithFileField.objects.all()
 
    In the case of multipart for submission, it would also pass the filename.
    By using a raw post data stream, we have to pass the filename within our
    file_field structure:
 
    file_field = {
        "name": "myfile.png",
        "file": "longbas64encodedstring",
        "content_type": "image/png" # on hydrate optional
    }
    """
    def dehydrate(self, bundle, for_list=True):
        if not bundle.data.has_key(self.instance_name) and hasattr(bundle.obj, self.instance_name):
            file_field = getattr(bundle.obj, self.instance_name)
            if file_field:
                try:
                    content_type, encoding = mimetypes.guess_type(file_field.file.name)
                    b64 = open(file_field.file.name, "rb").read().encode("base64")
                    ret = {
                        "name": os.path.basename(file_field.file.name),
                        "file": b64,
                        "content-type": content_type or "application/octet-stream"
                    }
                    return ret
                except:
                    pass
        return None
 
    def hydrate(self, obj):
        value = super(FileField, self).hydrate(obj)
        # Don't try to hydrate if value is a FieldFile, as no file was 
        # uploaded (i.e. during a PUT that doesn't modify the file).
        # Only try to hydrate if value is a dict (i.e. came from a JSON object)
        if not isinstance(value, FieldFile) and isinstance(value, dict):
            value = SimpleUploadedFile(value["name"], base64.b64decode(value["file"]), 
                                       getattr(value, "content_type", "application/octet-stream"))
        return value
