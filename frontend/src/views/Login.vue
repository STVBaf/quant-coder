<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";

import { login, register } from "../api";
import { useAuth } from "../stores/auth";

const router = useRouter();
const auth = useAuth();

const mode = ref("login");
const username = ref("");
const password = ref("");
const error = ref("");
const busy = ref(false);

async function submit() {
  if (busy.value) return;
  error.value = "";
  busy.value = true;
  try {
    const fn = mode.value === "login" ? login : register;
    const data = await fn({ username: username.value.trim(), password: password.value });
    auth.setAuth(data.token, data.username);
    router.push("/");
  } catch (e) {
    error.value = e.response?.data?.error || "操作失败";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div class="relative flex h-full items-center justify-center overflow-hidden">
    <!-- grid glow backdrop -->
    <div
      class="pointer-events-none absolute inset-0 opacity-40"
      style="background-image:linear-gradient(rgba(255,255,255,0.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.04) 1px,transparent 1px);background-size:40px 40px"
    ></div>
    <div class="pointer-events-none absolute left-1/2 top-1/3 h-72 w-72 -translate-x-1/2 rounded-full bg-[#007AFF]/20 blur-[100px]"></div>

    <div class="card relative w-80 p-6 backdrop-blur-md">
      <div class="mb-5 flex rounded-lg bg-[#0B0E11] p-1">
        <button
          v-for="m in ['login', 'register']"
          :key="m"
          class="flex-1 rounded-md py-1.5 text-sm transition"
          :class="mode === m ? 'bg-[#2B3139] text-[#FAFAFA]' : 'text-[#848E9C]'"
          @click="mode = m"
        >
          {{ m === "login" ? "登录" : "注册" }}
        </button>
      </div>

      <input
        v-model="username"
        placeholder="用户名"
        class="mb-3 w-full rounded-lg border border-[#2B3139] bg-[#0B0E11] px-3 py-2.5 text-sm outline-none focus:border-[#007AFF]"
        @keyup.enter="submit"
      />
      <input
        v-model="password"
        type="password"
        placeholder="密码"
        class="w-full rounded-lg border border-[#2B3139] bg-[#0B0E11] px-3 py-2.5 text-sm outline-none focus:border-[#007AFF]"
        @keyup.enter="submit"
      />

      <p v-if="error" class="mt-3 text-xs text-[#F6465D]">{{ error }}</p>

      <button
        class="mt-5 w-full rounded-lg bg-[#007AFF] py-2.5 text-sm font-medium text-white transition hover:brightness-110 hover:shadow-[0_0_16px_rgba(0,122,255,0.5)] disabled:opacity-50"
        :disabled="busy"
        @click="submit"
      >
        {{ mode === "login" ? "登录" : "注册并登录" }}
      </button>
    </div>
  </div>
</template>
