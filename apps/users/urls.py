from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'users'

urlpatterns = [
    # ==================== 认证相关 ====================

    # 用户注册
    # POST /api/v1/users/register/
    path('register/', views.RegisterView.as_view(), name='register'),

    # 用户登录
    # POST /api/v1/users/login/
    path('login/', views.LoginView.as_view(), name='login'),

    # 刷新Token
    # POST /api/v1/users/token/refresh/
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ==================== 用户信息 ====================

    # 获取/更新用户信息
    # GET /api/v1/users/me/
    # PUT /api/v1/users/me/
    path('me/', views.UserInfoView.as_view(), name='user_info'),

    # 修改密码
    # PUT /api/v1/users/me/password/
    path('me/password/', views.ChangePasswordView.as_view(), name='change_password'),

    # 上传头像
    # POST /api/v1/users/me/avatar/
    path('me/avatar/', views.UploadAvatarView.as_view(), name='upload_avatar'),

    # ==================== 收货地址 ====================

    # 收货地址列表/创建
    # GET /api/v1/users/address/
    # POST /api/v1/users/address/
    path('address/', views.AddressListCreateView.as_view(), name='address_list'),

    # 收货地址详情/修改/删除
    # GET /api/v1/users/address/{id}/
    # PUT /api/v1/users/address/{id}/
    # DELETE /api/v1/users/address/{id}/
    path('address/<int:pk>/', views.AddressDetailView.as_view(), name='address_detail'),

    # 设置默认地址
    # PUT /api/v1/users/address/{id}/default/
    path('address/<int:pk>/default/', views.SetDefaultAddressView.as_view(), name='set_default'),

    # ==================== 偏好设置 ====================

    # 用户偏好设置
    # GET /api/v1/users/preferences/
    # PUT /api/v1/users/preferences/
    path('preferences/', views.UserPreferencesView.as_view(), name='preferences'),

    # ==================== 商家相关 ====================

    # 升级为商家
    # POST /api/v1/users/upgrade/
    path('upgrade/', views.UpgradeToSellerView.as_view(), name='upgrade'),

    # 店铺设置
    # GET /api/v1/users/shop-settings/
    # PUT /api/v1/users/shop-settings/
    path('shop-settings/', views.ShopSettingsView.as_view(), name='shop_settings'),

    # 发送验证码
    # POST /api/v1/users/send_code/
    path('send_code/', views.SendCodeView.as_view(), name='send_code'),

    # 绑定手机号
    # POST /api/v1/users/me/phone/bind/
    path('me/phone/bind/', views.BindPhoneView.as_view(), name='bind_phone'),
]



