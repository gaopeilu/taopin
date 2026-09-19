"""
API 响应 Schema 校验层

用 Pydantic 定义每个接口的响应结构，测试时自动校验字段类型/必填项。
如果后端接口改字段名、改类型、删字段，测试立刻失败 —— 不等上线才发现。

使用方式:
    from schemas import UserInfoResponse, LoginResponse, ...
    resp = requests.get(...)
    LoginResponse.model_validate(resp.json())

设计原则:
  - 只校验「业务字段」，不校验 code/message（因为它们在所有接口格式统一）
  - 可选字段用 Optional[...] = None，不会因为后端没返回而误报
"""

from pydantic import BaseModel

# ====================================================================
# 通用基类
# ====================================================================


class TokenPair(BaseModel):
    access: str
    refresh: str


class UserProfile(BaseModel):
    id: int
    username: str
    phone: str | None = None
    email: str | None = None
    avatar: str | None = None
    role: str = "buyer"


class DRFPaginatedResponse(BaseModel):
    """DRF 标准分页响应: {count, results}"""

    count: int
    results: list


# ====================================================================
# 用户模块
# ====================================================================


class LoginData(BaseModel):
    tokens: TokenPair
    user: UserProfile


class WrappedLoginResponse(BaseModel):
    code: int = 200
    data: LoginData


class WrappedUserInfoResponse(BaseModel):
    code: int = 200
    data: UserProfile


class WrappedRegisterResponse(BaseModel):
    code: int = 200
    data: LoginData


class AddressItem(BaseModel):
    id: int
    receiver_name: str
    receiver_phone: str
    province: str | None = None
    city: str | None = None
    district: str | None = None
    detail_address: str
    is_default: bool = False


class WrappedAddressListResponse(BaseModel):
    code: int = 200
    data: list[AddressItem]


class WrappedAddressResponse(BaseModel):
    code: int = 200
    data: AddressItem


# ====================================================================
# 商品模块
# ====================================================================


class CategoryItem(BaseModel):
    id: int
    name: str
    parent: int | None = None
    level: int | None = None
    sort: int | None = None
    icon: str | None = None
    children: list["CategoryItem"] = []


class BrandItem(BaseModel):
    id: int
    name: str
    first_letter: str
    logo: str | None = None


class SPUItem(BaseModel):
    id: int
    name: str
    subtitle: str | None = ""
    main_image: str | None = None
    brand: int | None = None
    brand_name: str | None = None
    category: int | None = None
    category_name: str | None = None
    is_on_sale: bool = False
    sales: int | None = 0


class SKUItem(BaseModel):
    id: int
    name: str
    spu: int
    price: str | None = None
    stock: int | None = None
    is_active: bool = True


class CategoryTree(BaseModel):
    id: int
    name: str
    parent: int | None = None
    level: int | None = None
    children: list["CategoryTree"] = []


class ReviewItem(BaseModel):
    id: int
    sku: int
    order: int | None = None
    rating: int
    content: str | None = None
    user: int | None = None
    is_anonymous: bool = False
    created_at: str | None = None


# ====================================================================
# 商品模块 DRF 分页响应
# ====================================================================


class CategoryListResponse(BaseModel):
    count: int
    results: list[CategoryItem]


class BrandListResponse(BaseModel):
    count: int
    results: list[BrandItem]


class SPUListResponse(BaseModel):
    count: int
    results: list[SPUItem]


class SKUListResponse(BaseModel):
    count: int
    results: list[SKUItem]


class ReviewListResponse(BaseModel):
    count: int
    results: list[ReviewItem]


# ====================================================================
# 订单模块
# ====================================================================


class OrderItemSchema(BaseModel):
    sku_id: int
    sku_name: str | None = None
    price: str | None = None
    quantity: int
    subtotal: str | None = None


class OrderData(BaseModel):
    order_no: str
    status: str
    total_amount: str | None = None
    items: list[OrderItemSchema]
    receiver_name: str | None = None
    receiver_phone: str | None = None
    receiver_address: str | None = None


class WrappedOrderResponse(BaseModel):
    code: int = 200
    data: OrderData


class WrappedOrderListData(BaseModel):
    count: int
    results: list[OrderData]


class WrappedOrderListResponse(BaseModel):
    code: int = 200
    data: WrappedOrderListData


# ====================================================================
# 购物车模块
# ====================================================================


class CartItemData(BaseModel):
    sku_id: int
    quantity: int
    selected: bool = True
    sku_name: str | None = None
    price: str | None = None


class CartListData(BaseModel):
    items: list[CartItemData]
    total_amount: str | None = None
    total_count: int = 0


class WrappedCartListResponse(BaseModel):
    code: int = 200
    data: list[CartItemData]


# ====================================================================
# 支付模块
# ====================================================================


class PaymentData(BaseModel):
    pay_no: str
    order_no: str
    amount: str
    status: str
    pay_method: str | None = None


class WrappedPaymentResponse(BaseModel):
    code: int = 200
    data: PaymentData


# ====================================================================
# 营销模块
# ====================================================================


class CouponItem(BaseModel):
    id: int
    title: str
    amount: str
    min_spend: str | None = None
    remain: int | None = None
    is_claimed: bool = False


# ====================================================================
# 错误响应
# ====================================================================


class ErrorResponse(BaseModel):
    code: int
    message: str
    errors: dict | None = None


# ====================================================================
# 校验辅助
# ====================================================================


def assert_valid(schema_cls, data, context: str = ""):
    """
    一行调用完成 Schema 校验 + 错误定位。

    用法:
        from schemas import assert_valid, WrappedLoginResponse
        resp = requests.post(...)
        data = assert_valid(WrappedLoginResponse, resp.json(), context="登录")
    """
    try:
        return schema_cls.model_validate(data)
    except Exception as e:
        prefix = f"[{context}] " if context else ""
        raise AssertionError(f"{prefix}响应 Schema 校验失败:\n{e}") from e
