<script setup>
import { useRouter } from "vue-router";
import { ref } from "vue";

import { useAuth } from "./stores/auth";
import { useToast } from "./stores/toast";

const router = useRouter();
const auth = useAuth();
const toast = useToast();
const code = ref("");

const links = [
  { to: "/", label: "大盘看板" },
  { to: "/workspace", label: "量化工作台" },
  { to: "/history", label: "回测历史" },
];

function search() {
  if (code.value.trim()) {
    router.push(`/stock/${code.value.trim()}`);
    code.value = "";
  }
}

function logout() {
  auth.logout();
  router.push("/");
}
</script>

<template>
  <div class="flex h-screen w-screen flex-col overflow-hidden bg-[#0B0E11] text-[#FAFAFA]">
    <!-- Top nav -->
    <header
      class="z-10 flex h-14 shrink-0 items-center justify-between border-b border-[#2B3139] bg-[#0B0E11] px-6"
    >
      <div class="flex items-center gap-8">
        <div class="flex cursor-pointer items-center gap-2" @click="router.push('/')">
          <div
            class="flex h-6 w-6 items-center justify-center rounded bg-gradient-to-br from-[#007AFF] to-[#8A2BE2] text-sm font-bold text-white"
          >
            Q
          </div>
          <span class="text-lg font-bold tracking-wider">QuantDesk</span>
        </div>
        <nav class="flex gap-1">
          <router-link
            v-for="l in links"
            :key="l.to"
            :to="l.to"
            class="rounded px-4 py-2 text-sm text-[#848E9C] transition hover:bg-[#2B3139] hover:text-[#FAFAFA]"
            active-class="!bg-[#2B3139]/50 !text-[#007AFF] font-medium"
          >
            {{ l.label }}
          </router-link>
        </nav>
      </div>

      <div class="flex items-center gap-4">
        <input
          v-model="code"
          placeholder="搜索代码 600519"
          class="nums w-44 rounded border border-[#2B3139] bg-[#181A20] px-3 py-1.5 text-sm outline-none transition placeholder:text-[#848E9C] focus:border-[#007AFF]"
          @keyup.enter="search"
        />
        <div class="flex items-center font-mono text-xs text-[#848E9C]">
          <span class="mr-2 h-2 w-2 animate-pulse rounded-full bg-[#0ECB81]"></span>
          行情 API: Connected
        </div>
        <div v-if="auth.token" class="flex items-center gap-2">
          <span class="text-sm text-[#EAECEF]">{{ auth.username }}</span>
          <button class="text-xs text-[#848E9C] transition hover:text-[#F6465D]" @click="logout">
            退出
          </button>
        </div>
        <router-link
          v-else
          to="/login"
          class="flex h-8 w-8 items-center justify-center rounded-full border border-[#2B3139] bg-[#2B3139] text-[#848E9C] transition hover:border-[#848E9C]"
          title="登录 / 注册"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </router-link>
      </div>
    </header>

    <!-- Body -->
    <main class="flex-1 overflow-hidden">
      <router-view />
    </main>

    <!-- Toast -->
    <div class="fixed right-4 top-16 z-50 flex flex-col gap-2">
      <div
        v-for="t in toast.items"
        :key="t.id"
        class="card glass flex items-center gap-2 px-4 py-3 text-sm shadow-lg"
        :class="t.type === 'error' ? 'border-[#F6465D]/40 text-[#F6465D]' : 'text-[#EAECEF]'"
      >
        {{ t.text }}
      </div>
    </div>
  </div>
</template>
