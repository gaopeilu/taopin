/**
 * 商品相关接口
 * 对应后端: /api/v1/goods/
 */
import request from './request'

/* ========== 分类 ========== */

/**
 * 获取分类列表（顶级分类或指定父级的子分类）
 * GET /api/v1/goods/categories/
 * @param {Object} params - { parent: <id> } 可选
 */
export function getCategories(params) {
  return request.get('/api/v1/goods/categories/', { params })
}

/**
 * 获取完整分类树（递归嵌套children）
 * GET /api/v1/goods/categories/tree/
 */
export function getCategoryTree() {
  return request.get('/api/v1/goods/categories/tree/')
}

/* ========== 品牌 ========== */

/**
 * 品牌列表
 * GET /api/v1/goods/brands/
 * @param {Object} params - { letter, search, ordering }
 */
export function getBrands(params) {
  return request.get('/api/v1/goods/brands/', { params })
}

/* ========== 商品SPU（买家端） ========== */

/**
 * 商品列表（支持分页、分类筛选、搜索、排序）
 * GET /api/v1/goods/spus/
 * @param {Object} params - { category, search, ordering, page }
 * 返回: { count, next, previous, results: [GoodsSPUListSerializer] }
 */
export function getGoodsList(params) {
  return request.get('/api/v1/goods/spus/', { params })
}

/**
 * 商品详情（含嵌套brand/category/skus/images）
 * GET /api/v1/goods/spus/<id>/
 * @param {Number} id - SPU ID
 * 返回: GoodsSPUDetailSerializer
 */
export function getGoodsDetail(id) {
  return request.get(`/api/v1/goods/spus/${id}/`)
}

/**
 * 热销商品
 * GET /api/v1/goods/spus/hot/
 * @param {Object} params - { limit } 默认10
 */
export function getHotGoods(params) {
  return request.get('/api/v1/goods/spus/hot/', { params })
}

/**
 * 搜索商品
 * GET /api/v1/goods/spus/search/
 * @param {Object} params - { q: keyword }
 */
export function searchGoods(params) {
  return request.get('/api/v1/goods/spus/search/', { params })
}

/**
 * 获取商品SKU列表（仅激活的）
 * GET /api/v1/goods/spus/<id>/skus/
 * @param {Number} spuId - SPU ID
 */
export function getGoodsSkus(spuId) {
  return request.get(`/api/v1/goods/spus/${spuId}/skus/`)
}

/**
 * 获取商品图片列表
 * GET /api/v1/goods/spus/<id>/images/
 * @param {Number} spuId - SPU ID
 */
export function getGoodsImages(spuId) {
  return request.get(`/api/v1/goods/spus/${spuId}/images/`)
}

/* ========== SKU ========== */

/**
 * SKU列表
 * GET /api/v1/goods/skus/
 * @param {Object} params - { spu, is_default, in_stock, ordering }
 */
export function getSkuList(params) {
  return request.get('/api/v1/goods/skus/', { params })
}

/**
 * SKU详情
 * GET /api/v1/goods/skus/<id>/
 * @param {Number} id
 */
export function getSkuDetail(id) {
  return request.get(`/api/v1/goods/skus/${id}/`)
}

/**
 * 扣减库存
 * POST /api/v1/goods/skus/<id>/deduct_stock/
 * @param {Number} id - SKU ID
 * @param {Object} data - { quantity }
 */
export function deductStock(id, data) {
  return request.post(`/api/v1/goods/skus/${id}/deduct_stock/`, data)
}

/**
 * 恢复库存
 * POST /api/v1/goods/skus/<id>/restore_stock/
 * @param {Number} id - SKU ID
 * @param {Object} data - { quantity }
 */
export function restoreStock(id, data) {
  return request.post(`/api/v1/goods/skus/${id}/restore_stock/`, data)
}
