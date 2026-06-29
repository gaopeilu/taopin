"""
用户模块的数据模型

包含：
1. User - 用户主表
2. Address - 收货地址
3. UserPreferences - 用户偏好设置
4. VerificationCode - 验证码
"""
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    用户模型
    继承Django自带的AbstractUser，添加自定义字段

    AbstractUser自带字段：
    - username: 用户名
    - password: 密码（自动加密）
    - first_name: 名
    - last_name: 姓
    - is_active: 是否激活
    - is_staff: 是否员工
    - is_superuser: 是否超级管理员
    - date_joined: 注册时间
    - last_login: 最后登录时间
    """
    # 角色选择
    ROLE_CHOICES = (
        ('user', '普通用户'),
        ('seller', '商家'),
    )

    # 角色字段
    role = models.CharField(
        '用户角色',
        max_length=10,
        choices=ROLE_CHOICES,
        default='user'
    )

    # 重写email字段，允许为空
    email = models.EmailField(
        '邮箱',
        blank=True,
        null=True,
        unique=True
    )
    # 手机号，唯一，可以为空
    phone = models.CharField(
        '手机号',
        max_length=11,
        unique=True,
        null=True,
        blank=True
    )

    # 头像，上传到avatars/目录下
    avatar = models.ImageField(
        '头像',
        upload_to='avatars/%Y/%m/',
        null=True,
        blank=True
    )

    # 昵称
    nickname = models.CharField(
        '昵称',
        max_length=50,
        blank=True,
        default=''
    )

    # 性别：0未知 1男 2女
    gender = models.SmallIntegerField(
        '性别',
        choices=(
            (0, '未知'),
            (1, '男'),
            (2, '女')
        ),
        default=0
    )

    # 生日
    birthday = models.DateField(
        '生日',
        null=True,
        blank=True
    )

    # 个人简介
    bio = models.CharField(
        '个人简介',
        max_length=500,
        blank=True,
        default=''
    )

    # 实名认证状态
    is_verified = models.BooleanField(
        '实名认证',
        default=False
    )

    # 商家相关字段
    shop_name = models.CharField(
        '店铺名称',
        max_length=100,
        blank=True,
        default=''
    )

    shop_logo = models.ImageField(
        '店铺Logo',
        upload_to='shops/',
        null=True,
        blank=True
    )

    shop_description = models.TextField(
        '店铺简介',
        blank=True,
        default=''
    )

    # 软删除标记
    is_deleted = models.BooleanField(
        '软删除',
        default=False
    )

    class Meta:
        db_table = 'users'  # 数据库表名
        verbose_name = '用户'  # 后台显示名称
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

    @property
    def is_seller(self):
        """是否是商家"""
        return self.role == 'seller'

    @property
    def is_user(self):
        """是否是普通用户"""
        return self.role == 'user'


class Address(models.Model):
    """
    收货地址模型
    一个用户可以有多个收货地址（一对多关系）
    """
    # 关联用户，CASCADE表示删除用户时同时删除地址
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name='用户'
    )

    # 收货人姓名
    receiver_name = models.CharField(
        '收货人',
        max_length=50
    )

    # 收货人电话
    receiver_phone = models.CharField(
        '电话',
        max_length=11
    )

    # 省
    province = models.CharField(
        '省',
        max_length=50
    )

    # 市
    city = models.CharField(
        '市',
        max_length=50
    )

    # 区
    district = models.CharField(
        '区',
        max_length=50
    )

    # 详细地址
    detail_address = models.CharField(
        '详细地址',
        max_length=200
    )

    # 是否默认地址
    is_default = models.BooleanField(
        '默认地址',
        default=False
    )

    # 创建时间（自动添加）
    created_at = models.DateTimeField(
        '创建时间',
        auto_now_add=True
    )

    # 更新时间（自动更新）
    updated_at = models.DateTimeField(
        '更新时间',
        auto_now=True
    )

    class Meta:
        db_table = 'addresses'
        verbose_name = '收货地址'
        verbose_name_plural = verbose_name
        # 排序规则：默认地址在前，按创建时间倒序
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.receiver_name} - {self.province}{self.city}{self.district}"


class UserPreferences(models.Model):
    """
    用户偏好设置模型
    一个用户只有一个偏好设置（一对一关系）
    """
    # 一对一关联用户
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='preferences',
        verbose_name='用户'
    )

    # 订单通知开关
    order_notify = models.BooleanField(
        '订单通知',
        default=True
    )

    # 促销通知开关
    promotion_notify = models.BooleanField(
        '促销通知',
        default=True
    )

    # 是否公开购买记录
    public_purchase = models.BooleanField(
        '公开购买记录',
        default=False
    )

    # 是否公开评价
    public_review = models.BooleanField(
        '公开评价',
        default=True
    )

    # 创建时间
    created_at = models.DateTimeField(
        '创建时间',
        auto_now_add=True
    )

    # 更新时间
    updated_at = models.DateTimeField(
        '更新时间',
        auto_now=True
    )

    class Meta:
        db_table = 'user_preferences'
        verbose_name = '用户偏好'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username}的偏好设置"


class VerificationCode(models.Model):
    """
    验证码模型
    用于存储手机/邮箱验证码
    """
    # 目标（手机号或邮箱）
    target = models.CharField(
        '目标',
        max_length=100,
        db_index=True
    )

    # 验证码
    code = models.CharField(
        '验证码',
        max_length=10
    )

    # 类型：register=注册, login=登录, bind_phone=绑定手机, bind_email=绑定邮箱
    code_type = models.CharField(
        '类型',
        max_length=20,
        choices=(
            ('register', '注册'),
            ('login', '登录'),
            ('bind_phone', '绑定手机'),
            ('bind_email', '绑定邮箱'),
        )
    )

    # 是否已使用
    is_used = models.BooleanField(
        '已使用',
        default=False
    )

    # 过期时间
    expires_at = models.DateTimeField(
        '过期时间'
    )

    # 创建时间
    created_at = models.DateTimeField(
        '创建时间',
        auto_now_add=True
    )

    class Meta:
        db_table = 'verification_codes'
        verbose_name = '验证码'
        verbose_name_plural = verbose_name
        # 联合索引：查询验证码时更快
        indexes = [
            models.Index(fields=['target', 'code_type']),
        ]

    def __str__(self):
        return f"{self.target} - {self.code}"
