"""
权限控制工具

包含：
1. IsSeller - 只允许商家访问
2. IsUser - 只允许普通用户访问
"""
from rest_framework import permissions


class IsSeller(permissions.BasePermission):
    """
    只允许商家访问
    """
    message = '该功能仅限商家使用'

    def has_permission(self, request, view):
        # 检查用户是否已认证
        if not request.user or not request.user.is_authenticated:
            return False
        # 检查用户是否是商家
        return request.user.role == 'seller'


class IsUser(permissions.BasePermission):
    """
    只允许普通用户访问
    """
    message = '该功能仅限普通用户使用'

    def has_permission(self, request, view):
        # 检查用户是否已认证
        if not request.user or not request.user.is_authenticated:
            return False
        # 检查用户是否是普通用户
        return request.user.role == 'user'


class IsSellerOrReadOnly(permissions.BasePermission):
    """
    商家可以进行所有操作，普通用户只能读取
    GET请求允许匿名访问，POST/PUT/DELETE需要商家权限
    """
    message = '该功能仅限商家使用'

    def has_permission(self, request, view):
        # GET/HEAD/OPTIONS请求允许匿名访问
        if request.method in permissions.SAFE_METHODS:
            return True

        # 写入操作需要登录
        if not request.user or not request.user.is_authenticated:
            return False

        # 写入权限仅限商家
        return request.user.role == 'seller'
