<template>
  <footer class="footer">
    <div class="footer-inner">
      <div class="footer-top">
        <div class="footer-col">
          <div class="footer-title">购物指南</div>
          <div>购物流程</div>
          <div>订单查询</div>
          <div>常见问题</div>
        </div>
        <div class="footer-col">
          <div class="footer-title">配送方式</div>
          <div>上门自提</div>
          <div>快递运输</div>
          <div>配送范围</div>
        </div>
        <div class="footer-col">
          <div class="footer-title">售后服务</div>
          <div>退换货政策</div>
          <div>退款说明</div>
          <div>投诉建议</div>
        </div>
        <div class="footer-col">
          <div class="footer-title">商家服务</div>
          <div>商家入驻</div>
          <div>商家培训</div>
          <div>商家后台</div>
        </div>
      </div>
      <div class="footer-bottom">
        <p>© 2026 淘拼商城 版权所有 | 智能电商导购平台</p>
      </div>
    </div>
  </footer>
</template>

<script setup></script>

<style scoped>
.footer { background: #333; color: #ccc; margin-top: 40px; }
.footer-inner { max-width: 1200px; margin: 0 auto; padding: 40px 16px 20px; }
.footer-top { display: flex; justify-content: space-between; gap: 40px; margin-bottom: 24px; }
.footer-col { }
.footer-col div { font-size: 13px; padding: 4px 0; color: #999; }
.footer-title { font-size: 14px; font-weight: bold; color: #fff; margin-bottom: 8px; }
.footer-bottom { text-align: center; padding-top: 20px; border-top: 1px solid #444; font-size: 12px; color: #666; }
</style>
