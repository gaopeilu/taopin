import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { createPinia } from 'pinia'
import VueLazyload from 'vue-lazyload'
import router from './router'
import App from './App.vue'
import './assets/styles/global.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.use(VueLazyload, {
  preLoad: 1.3,
  error: 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect fill="#f5f5f5" width="200" height="200"/><text fill="#ccc" font-family="Arial" font-size="14" x="50%" y="50%" text-anchor="middle" dy=".3em">图片加载失败</text></svg>'),
  loading: 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect fill="#f5f5f5" width="200" height="200"/><text fill="#ccc" font-family="Arial" font-size="14" x="50%" y="50%" text-anchor="middle" dy=".3em">加载中...</text></svg>'),
  attempt: 1
})
app.mount('#app')
