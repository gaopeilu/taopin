<template>
  <!-- 买家端布局：顶部导航 + 主内容 + 底部 -->
  <div class="user-layout">
    <NavBar />
    <main class="main-content"><router-view /></main>
    <Footer />
  </div>
</template>

<script setup>
/* 买家端公共布局 */
import NavBar from './NavBar.vue'
import Footer from './Footer.vue'
</script>

<style scoped>
.user-layout { display: flex; flex-direction: column; min-height: 100vh; }
.main-content { flex: 1; padding-bottom: 40px; }
</style>
