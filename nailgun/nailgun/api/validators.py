import json
from piston.utils import FormValidationError
from piston.decorator import decorator

def validate_json(v_form):
    @decorator
    def wrap(f, self, request, *a, **kwa):
        form = v_form(json.loads(request.body), request.FILES)
        
        if form.is_valid():
            setattr(request, 'form', form)
            return f(self, request, *a, **kwa)
        else:
            raise FormValidationError(form)
    return wrap
