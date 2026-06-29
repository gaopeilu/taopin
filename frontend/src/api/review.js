/**
 * 评价相关接口
 * 对应后端: /api/v1/reviews/
 */
import request from './request'

/**
 * 商品评价列表（公开）
 * GET /api/v1/reviews/?spu_id=<id>
 * @param {Object} params - { spu_id }
 */
export function getReviews(params) {
  return request.get('/api/v1/reviews/', { params })
}

/**
 * 提交评价
 * POST /api/v1/reviews/create/
 * @param {Object} data - { sku_id, spu_id, order_no, rating, content, images, is_anonymous }
 */
export function createReview(data) {
  return request.post('/api/v1/reviews/create/', data)
}

/**
 * 我的评价
 * GET /api/v1/reviews/mine/
 */
export function getMyReviews() {
  return request.get('/api/v1/reviews/mine/')
}

/**
 * 评价点赞
 * POST /api/v1/reviews/<id>/like/
 * @param {Number} id - 评价ID
 * @returns {Object} { code: 200, message: '点赞成功' }
 */
export function likeReview(id) {
  return request.post(`/api/v1/reviews/${id}/like/`)
}
