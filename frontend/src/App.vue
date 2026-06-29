<script setup>
import { useRouter } from "vue-router";
import { ref } from "vue";

const router = useRouter();
const code = ref("");

function search() {
  if (code.value.trim()) router.push(`/stock/${code.value.trim()}`);
}
</script>

<template>
  <div class="app">
    <header>
      <h1 @click="router.push('/')">量化研究台</h1>
      <nav>
        <router-link to="/">大盘</router-link>
        <router-link to="/backtest">回测</router-link>
      </nav>
      <div class="search">
        <input v-model="code" placeholder="输入股票代码，如 600519" @keyup.enter="search" />
        <button @click="search">查询</button>
      </div>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  box-sizing: border-box;
}
body {
  background: #0b0e14;
  color: #d6dbe5;
  font-family: -apple-system, "Segoe UI", sans-serif;
}
header {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px 28px;
  background: #11151f;
  border-bottom: 1px solid #1f2633;
}
h1 {
  font-size: 18px;
  color: #4ea1ff;
  cursor: pointer;
}
nav {
  display: flex;
  gap: 16px;
}
nav a {
  color: #9aa4b5;
  text-decoration: none;
  font-size: 14px;
}
nav a.router-link-active {
  color: #4ea1ff;
}
.search {
  display: flex;
  gap: 8px;
}
input {
  background: #0b0e14;
  border: 1px solid #2a3344;
  color: #d6dbe5;
  padding: 6px 12px;
  border-radius: 6px;
  width: 220px;
}
button {
  background: #4ea1ff;
  border: none;
  color: #06101f;
  padding: 6px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}
main {
  padding: 28px;
}
</style>
