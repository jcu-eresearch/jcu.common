
from pyramid_deform import SessionFileUploadTempStore
import deform.widget
import colander


@colander.deferred
def file_upload_widget(node, kw):
    request = kw['request']
    tmpstore = SessionFileUploadTempStore(request)
    return deform.widget.FileUploadWidget(tmpstore)


@colander.deferred
def image_upload_widget(node, kw):
    widget = file_upload_widget(node, kw)
    widget.template = 'image_upload'
    return widget


class InlineMappingWidget(deform.widget.MappingWidget):
    template = "inline_mapping"
    error_class = "deform-error"


import httplib2
from urllib import urlencode
from deform.widget import CheckedInputWidget

@colander.deferred
def recaptcha_widget(node, kw):
    request = kw['request']
    class RecaptchaWidget(CheckedInputWidget):
        template = 'recaptcha'
        readonly_template = 'recaptcha'
        requirements = ()
        url = "https://www.google.com/recaptcha/api/verify"
        headers={'Content-type': 'application/x-www-form-urlencoded'}

        def serialize(self, field, cstruct, readonly=False):
            if cstruct in (colander.null, None):
                cstruct = ''
            confirm = getattr(field, 'confirm', '')
            template = readonly and self.readonly_template or self.template
            return field.renderer(
                template,
                field=field,
                cstruct=cstruct,
                public_key=self.request.registry.settings['recaptcha.public_key']
            )

        def deserialize(self, field, pstruct):
            if pstruct is colander.null:
                return colander.null
            challenge = pstruct.get('recaptcha_challenge_field') or ''
            response = pstruct.get('recaptcha_response_field') or ''
            if not response:
                raise colander.Invalid(
                    field.schema,
                    'Please enter the characters you see.')
            if not challenge:
                raise colander.Invalid(
                    field.schema,
                    'Challenge data was missing.')
            privatekey = self.request.registry.settings['recaptcha.private_key']
            remoteip = self.request.remote_addr
            data = urlencode(dict(privatekey=privatekey,
                                  remoteip=remoteip,
                                  challenge=challenge,
                                  response=response))
            timeout = int(
                self.request.registry.settings.get('recaptcha.timeout', 10))
            h = httplib2.Http(timeout=timeout)
            try:
                resp, content = h.request(self.url,
                                          "POST",
                                          headers=self.headers,
                                          body=data)
            except AttributeError as e:
                if e=="'NoneType' object has no attribute 'makefile'":
                    ## XXX: catch a possible httplib regression in 2.7 where
                    ## XXX: there is no connection made to the socket so
                    ## XXX sock is still None when makefile is called.
                    raise colander.Invalid(field.schema,
                                  "Could not connect to the CAPTCHA service.")
            if not resp['status'] == '200':
                raise colander.Invalid(field.schema,
                              "There was an error talking to the reCAPTCHA \
                              server{0}".format(resp['status']))
            valid, reason = content.split('\n')
            if not valid == 'true':
                if reason == 'incorrect-captcha-sol':
                    reason = "Please retry and enter the characters you see below."
                raise colander.Invalid(field.schema,
                                       reason.replace('\\n', ' ').strip("'"))
            return pstruct

    return RecaptchaWidget(request=request)
