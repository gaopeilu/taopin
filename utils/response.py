from rest_framework.response import Response


def success_response(data=None, message="success", code=200):
    return Response({"code": code, "message": message, "data": data})


def error_response(message="error", code=400, errors=None):
    response_data = {"code": code, "message": message}
    if errors:
        response_data["errors"] = errors
    return Response(response_data, status=code)
