from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Normalize all DRF error responses to {"error": "...", "detail": "..."}.

    Keeps a consistent shape for API clients and Swagger consumers.
    """
    response = exception_handler(exc, context)
    if response is None:
        return response

    status_code = response.status_code
    data = response.data

    # Map HTTP status to a short error category label
    error_labels = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        429: "Too Many Requests",
    }
    error = error_labels.get(status_code, "Error")

    if isinstance(data, dict):
        if "detail" in data and len(data) == 1:
            detail = data["detail"]
        else:
            detail = data
    elif isinstance(data, list):
        detail = data
    else:
        detail = str(data)

    response.data = {"error": error, "detail": detail}
    return response
