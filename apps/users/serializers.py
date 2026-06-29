from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Address, UserPreferences


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    用户注册序列化器
    功能：验证注册数据，创建用户
    """
    # 密码字段，write_only=True表示只在写入时使用，不会返回给前端
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=20
    )
    # 确认密码
    password_confirm = serializers.CharField(write_only=True)
    # 角色字段
    role = serializers.ChoiceField(
        choices=['user', 'seller'],
        default='user'
    )
    # 店铺名称（商家注册时必填）
    shop_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password', 'password_confirm', 'role', 'shop_name']

    def validate_username(self, value):
        """验证用户名是否已存在"""
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError("用户名至少3个字符")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已存在")
        return value

    def validate_email(self, value):
        """处理邮箱空字符串"""
        if not value or value.strip() == '':
            return None
        return value

    def validate_phone(self, value):
        """验证手机号是否已注册"""
        # 处理空字符串
        if not value or value.strip() == '':
            return None
        # 验证手机号格式
        if not value.isdigit() or len(value) != 11:
            raise serializers.ValidationError("请输入正确的11位手机号")
        # 验证是否已注册
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("手机号已注册")
        return value

    def validate(self, data):
        """验证数据"""
        # 验证两次密码是否一致
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "两次密码不一致"})

        # 如果是商家注册，验证店铺名称
        if data.get('role') == 'seller':
            if not data.get('shop_name'):
                raise serializers.ValidationError({"shop_name": "商家注册请输入店铺名称"})

        return data

    def create(self, validated_data):
        """创建用户"""
        # 移除确认密码字段（数据库不需要）
        validated_data.pop('password_confirm')
        # 获取密码和角色
        password = validated_data.pop('password')
        role = validated_data.pop('role', 'user')
        shop_name = validated_data.pop('shop_name', '')
        # 处理空字符串字段
        if validated_data.get('phone') == '':
            validated_data['phone'] = None
        if validated_data.get('email') == '':
            validated_data['email'] = None
        # 创建用户对象
        user = User(**validated_data)
        user.role = role
        user.shop_name = shop_name
        # 设置密码（自动加密）
        user.set_password(password)
        # 保存到数据库
        user.save()
        # 创建用户偏好设置
        UserPreferences.objects.create(user=user)
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    用户登录序列化器
    功能：验证登录信息，支持用户名/手机号/邮箱登录
    """
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        """验证登录信息"""
        username = data.get('username')
        password = data.get('password')

        # 尝试查找用户
        user = None

        # 如果是邮箱格式
        if '@' in username:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        # 如果是11位数字（手机号）
        elif username.isdigit() and len(username) == 11:
            try:
                user_obj = User.objects.get(phone=username)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        # 否则当作用户名
        else:
            user = authenticate(username=username, password=password)

        # 验证用户是否存在
        if not user:
            raise serializers.ValidationError("用户名或密码错误")

        # 验证用户是否被禁用
        if not user.is_active:
            raise serializers.ValidationError("用户已被禁用")

        # 将用户对象添加到validated_data中
        data['user'] = user
        return data


class UserInfoSerializer(serializers.ModelSerializer):
    """
    用户信息序列化器
    功能：返回用户信息给前端
    """
    # 是否是商家（只读属性）
    is_seller = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'avatar',
            'nickname', 'gender', 'birthday', 'bio',
            'role', 'is_seller', 'shop_name',
            'date_joined'
        ]
        # 只读字段（前端不能修改）
        read_only_fields = ['id', 'username', 'role', 'date_joined']


class ChangePasswordSerializer(serializers.Serializer):
    """
    修改密码序列化器
    功能：验证旧密码，设置新密码
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)

    def validate_old_password(self, value):
        """验证旧密码是否正确"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("旧密码错误")
        return value

    def validate(self, data):
        """验证两次新密码是否一致"""
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "两次密码不一致"})
        return data


class AddressSerializer(serializers.ModelSerializer):
    """
    收货地址序列化器
    功能：创建/更新/返回地址信息
    """
    class Meta:
        model = Address
        fields = [
            'id', 'receiver_name', 'receiver_phone',
            'province', 'city', 'district', 'detail_address', 'is_default'
        ]
        read_only_fields = ['id']


class UserPreferencesSerializer(serializers.ModelSerializer):
    """
    用户偏好设置序列化器
    """
    class Meta:
        model = UserPreferences
        fields = ['order_notify', 'promotion_notify', 'public_purchase', 'public_review']
