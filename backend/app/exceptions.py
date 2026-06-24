from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class ServiceError(APIException):
    status_code = 400
    default_code = "service_error"

    def __init__(self, detail, code=None):
        self.detail = {"error": detail, "code": code or self.default_code}


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        if isinstance(response.data, dict) and "detail" in response.data:
            detail = response.data["detail"]
            if isinstance(detail, list):
                message = "; ".join(str(item) for item in detail)
            else:
                message = str(detail)
            code = getattr(exc, "default_code", "error")
            if hasattr(exc, "get_codes"):
                codes = exc.get_codes()
                if isinstance(codes, str):
                    code = codes
                elif isinstance(codes, dict):
                    first = next(iter(codes.values()), None)
                    if isinstance(first, list) and first:
                        code = str(first[0])
                    elif isinstance(first, str):
                        code = first
            response.data = {"error": message, "code": code.upper() if isinstance(code, str) else "ERROR"}
        elif isinstance(response.data, dict) and "error" not in response.data:
            response.data = {
                "error": str(response.data),
                "code": "ERROR",
            }
    return response
