import json
from piston.utils import FormValidationError, HttpStatusCode, rc
from piston.decorator import decorator

def validate_json(v_form):
    @decorator
    def wrap(f, self, request, *a, **kwa):
        content_type = request.content_type.split(';')[0]
        if content_type != "application/json":
            response = rc.BAD_REQUEST
            response.content = "Invalid content type, must be application/json"
            raise HttpStatusCode(response)
        
        form = v_form(json.loads(request.body), request.FILES)
        
        if form.is_valid():
            setattr(request, 'form', form)
            return f(self, request, *a, **kwa)
        else:
            raise FormValidationError(form)
    return wrap
