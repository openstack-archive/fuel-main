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

        try:
            parsed_body = json.loads(request.body)
        except:
            response = rc.BAD_REQUEST
            response.content = "Invalid JSON object"
            raise HttpStatusCode(response)

        if not isinstance(parsed_body, dict):
            response = rc.BAD_REQUEST
            response.content = "Dictionary expected"
            raise HttpStatusCode(response)

        form = v_form(parsed_body, request.FILES)

        if form.is_valid():
            setattr(request, 'form', form)
            return f(self, request, *a, **kwa)
        else:
            raise FormValidationError(form)
    return wrap


def validate_json_list(v_form):
    @decorator
    def wrap(f, self, request, *a, **kwa):
        content_type = request.content_type.split(';')[0]
        if content_type != "application/json":
            response = rc.BAD_REQUEST
            response.content = "Invalid content type, must be application/json"
            raise HttpStatusCode(response)

        try:
            parsed_body = json.loads(request.body)
        except:
            response = rc.BAD_REQUEST
            response.content = "Invalid JSON object"
            raise HttpStatusCode(response)

        if not isinstance(parsed_body, list):
            response = rc.BAD_REQUEST
            response.content = "List expected"
            raise HttpStatusCode(response)

        if not len(parsed_body):
            response = rc.BAD_REQUEST
            response.content = "No entries to update"
            raise HttpStatusCode(response)

        forms = []
        for entry in parsed_body:
            form = v_form(entry, request.FILES)
            if form.is_valid():
                forms.append(form)
            else:
                raise FormValidationError(form)
        setattr(request, 'forms', forms)
        return f(self, request, *a, **kwa)
    return wrap
