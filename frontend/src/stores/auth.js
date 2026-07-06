import { defineStore } from "pinia";
import { ref } from "vue";

export const useAuth = defineStore("auth", () => {
  const token = ref(localStorage.getItem("token") || "");
  const username = ref(localStorage.getItem("username") || "");

  function setAuth(t, name) {
    token.value = t;
    username.value = name;
    localStorage.setItem("token", t);
    localStorage.setItem("username", name);
  }

  function logout() {
    token.value = "";
    username.value = "";
    localStorage.removeItem("token");
    localStorage.removeItem("username");
  }

  return { token, username, setAuth, logout };
});
