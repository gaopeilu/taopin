/**
 * 响应数据提取工具
 * 统一处理不同API返回格式
 */

/**
 * 从响应中提取数据
 * 支持格式: {code, data}, {count, results}, 纯list, 纯object
 */
export function extractData(res, defaultVal = null) {
  if (!res) return defaultVal
  if (Array.isArray(res)) return res
  if (res.data !== undefined) return res.data
  if (res.results !== undefined) return res.results
  return res
}

/**
 * 从响应中提取列表
 * 支持格式: {code, data: [...]}, {count, results: [...]}, [...]
 */
export function extractList(res) {
  if (!res) return []
  if (Array.isArray(res)) return res
  if (Array.isArray(res.data)) return res.data
  if (Array.isArray(res.results)) return res.results
  return []
}

/**
 * 从响应中提取分页数据
 * 返回: { list: [], total: number }
 */
export function extractPage(res) {
  if (!res) return { list: [], total: 0 }
  if (Array.isArray(res)) return { list: res, total: res.length }
  if (res.results !== undefined) return { list: res.results || [], total: res.count || 0 }
  if (Array.isArray(res.data)) return { list: res.data, total: res.data.length }
  if (res.data?.results !== undefined) return { list: res.data.results || [], total: res.data.count || 0 }
  return { list: [], total: 0 }
}
