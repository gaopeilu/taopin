/**
 * 搜索相关接口
 * 对应后端: /api/v1/search/
 */
import request from './request'

/**
 * 获取搜索历史
 * GET /api/v1/search/history/
 * @returns {Array} [ { id, keyword, result_count, created_at } ]
 */
export function getSearchHistory() {
  return request.get('/api/v1/search/history/')
}

/**
 * 清空搜索历史
 * DELETE /api/v1/search/history/clear/
 * @returns {Object} { code: 200, message: '清空成功' }
 */
export function clearSearchHistory() {
  return request.delete('/api/v1/search/history/clear/')
}

/**
 * 搜索建议
 * GET /api/v1/search/suggest/?q=关键词
 * @param {String} keyword - 搜索关键词
 * @returns {Array} [ '建议1', '建议2', ... ]
 */
export function searchSuggest(keyword) {
  return request.get('/api/v1/search/suggest/', { params: { q: keyword } })
}
