from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Address, UserPreferences, VerificationCode
from .serializers import (
    UserRegisterSerializer, UserLoginSerializer, UserInfoSerializer,
    ChangePasswordSerializer, AddressSerializer, UserPreferencesSerializer
)


# ==================== 认证相关视图 ====================

class RegisterView(generics.CreateAPIView):
    """
    用户注册视图
    接收POST请求，创建新用户
    """
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]  # 允许任何人访问
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'

    def create(self, request, *args, **kwargs):
        """处理注册请求"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # 生成JWT Token
        refresh = RefreshToken.for_user(user)

        return Response({
            'code': 200,
            'message': '注册成功',
            'data': {
                'user': UserInfoSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    用户登录视图
    接收POST请求，验证用户身份
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        """处理登录请求"""
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        return Response({
            'code': 200,
            'message': '登录成功',
            'data': {
                'user': UserInfoSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }
        })


# ==================== 用户信息视图 ====================

class UserInfoView(generics.RetrieveUpdateAPIView):
    """
    用户信息视图
    GET - 获取当前用户信息
    PUT/PATCH - 更新当前用户信息
    """
    serializer_class = UserInfoSerializer
    permission_classes = [permissions.IsAuthenticated]  # 需要登录

    def get_object(self):
        """获取当前登录的用户"""
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        """获取用户信息"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': 'success',
            'data': serializer.data
        })

    def update(self, request, *args, **kwargs):
        """更新用户信息"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'code': 200,
            'message': '更新成功',
            'data': serializer.data
        })


class ChangePasswordView(APIView):
    """
    修改密码视图
    """
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        """处理修改密码请求"""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        return Response({
            'code': 200,
            'message': '密码修改成功'
        })


class UploadAvatarView(APIView):
    """
    上传头像视图
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """处理上传头像请求"""
        avatar = request.FILES.get('avatar')

        if not avatar:
            return Response({
                'code': 400,
                'message': '请上传头像文件'
            }, status=status.HTTP_400_BAD_REQUEST)

        request.user.avatar = avatar
        request.user.save()

        return Response({
            'code': 200,
            'message': '上传成功',
            'data': {
                'avatar': request.user.avatar.url if request.user.avatar else None
            }
        })


# ==================== 收货地址视图 ====================

class AddressListCreateView(generics.ListCreateAPIView):
    """
    收货地址列表/创建视图
    GET - 获取地址列表
    POST - 创建新地址
    """
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """获取当前用户的地址列表"""
        return Address.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        """返回地址列表"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 200,
            'message': 'success',
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """创建新地址"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return Response({
            'code': 200,
            'message': '添加成功',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    收货地址详情/修改/删除视图
    """
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """只允许操作自己的地址"""
        return Address.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """获取地址详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': 'success',
            'data': serializer.data
        })

    def update(self, request, *args, **kwargs):
        """修改地址"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'code': 200,
            'message': '修改成功',
            'data': serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        """删除地址"""
        instance = self.get_object()
        instance.delete()
        return Response({
            'code': 200,
            'message': '删除成功'
        })


class SetDefaultAddressView(APIView):
    """
    设置默认地址视图
    """
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        """设置默认地址"""
        try:
            address = Address.objects.get(pk=pk, user=request.user)
        except Address.DoesNotExist:
            return Response({
                'code': 404,
                'message': '地址不存在'
            }, status=status.HTTP_404_NOT_FOUND)

        # 取消其他默认地址
        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)

        # 设置当前为默认
        address.is_default = True
        address.save()

        return Response({
            'code': 200,
            'message': '设置成功'
        })


# ==================== 用户偏好视图 ====================

class UserPreferencesView(generics.RetrieveUpdateAPIView):
    """
    用户偏好设置视图
    """
    serializer_class = UserPreferencesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """获取或创建用户偏好设置"""
        obj, created = UserPreferences.objects.get_or_create(user=self.request.user)
        return obj

    def retrieve(self, request, *args, **kwargs):
        """获取偏好设置"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': 'success',
            'data': serializer.data
        })

    def update(self, request, *args, **kwargs):
        """更新偏好设置"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'code': 200,
            'message': '更新成功',
            'data': serializer.data
        })


# ==================== 升级为商家视图 ====================

class UpgradeToSellerView(APIView):
    """
    升级为商家视图
    仅普通用户可调用
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """处理升级请求"""
        user = request.user

        # 检查是否已经是商家
        if user.role == 'seller':
            return Response({
                'code': 400,
                'message': '您已经是商家，无需重复升级'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 获取表单数据
        shop_name = request.data.get('shop_name')
        shop_description = request.data.get('shop_description', '')
        contact_phone = request.data.get('contact_phone', '')

        # 验证店铺名称
        if not shop_name:
            return Response({
                'code': 400,
                'message': '请输入店铺名称'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 更新用户角色和店铺信息
        user.role = 'seller'
        user.shop_name = shop_name
        user.shop_description = shop_description
        user.save()

        return Response({
            'code': 200,
            'message': '升级成功',
            'data': {
                'role': user.role,
                'shop_name': user.shop_name
            }
        })


class ShopSettingsView(APIView):
    """
    店铺设置视图
    仅商家可访问
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """获取店铺设置"""
        user = request.user
        if user.role != 'seller':
            return Response({
                'code': 403,
                'message': '无权限访问'
            }, status=status.HTTP_403_FORBIDDEN)

        return Response({
            'code': 200,
            'data': {
                'shop_name': user.shop_name,
                'shop_description': user.shop_description,
                'contact_phone': user.phone
            }
        })

    def put(self, request):
        """更新店铺设置"""
        user = request.user
        if user.role != 'seller':
            return Response({
                'code': 403,
                'message': '无权限访问'
            }, status=status.HTTP_403_FORBIDDEN)

        user.shop_name = request.data.get('shop_name', user.shop_name)
        user.shop_description = request.data.get('shop_description', user.shop_description)
        user.save()

        return Response({
            'code': 200,
            'message': '更新成功'
        })


class SendCodeView(APIView):
    """
    发送验证码
    POST /api/v1/users/send_code/
    模拟发送，返回验证码（开发环境）
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'send_code'

    def post(self, request):
        target = request.data.get('target', '')
        code_type = request.data.get('code_type', 'register')
        if not target:
            return Response({'code': 400, 'message': '请输入手机号或邮箱'}, status=400)
        # [修复14] 使用secrets生成验证码（密码学安全随机数）
        import secrets
        from django_redis import get_redis_connection
        code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        con = get_redis_connection('default')
        key = f'code:{target}:{code_type}'
        con.setex(key, 600, code)  # 600秒 = 10分钟
        return Response({
            'code': 200,
            'message': '验证码已发送',
            'data': {'code': code, 'target': target, 'code_type': code_type}
        })


class BindPhoneView(APIView):
    """
    绑定/换绑手机号
    POST /api/v1/users/me/phone/bind/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        phone = request.data.get('phone', '')
        if not phone or len(phone) != 11:
            return Response({'code': 400, 'message': '请输入正确的11位手机号'}, status=400)
        request.user.phone = phone
        request.user.save()
        return Response({
            'code': 200,
            'message': '绑定成功',
            'data': {'phone': phone}
        })
