from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        errors = None
        if isinstance(response.data, dict):
            # 处理detail字段
            if 'detail' in response.data:
                message = response.data['detail']
            else:
                # 处理验证错误
                errors = response.data
                # 提取第一个错误信息作为主消息
                first_error = []
                for key, value in response.data.items():
                    if isinstance(value, list):
                        first_error.append(f"{key}: {value[0]}")
                    else:
                        first_error.append(f"{key}: {value}")
                message = first_error[0] if first_error else '请求错误'
        elif isinstance(response.data, list):
            message = response.data[0]
        else:
            message = str(response.data)

        response.data = {
            'code': response.status_code,
            'message': message,
        }
        if errors:
            response.data['errors'] = errors
    return response
