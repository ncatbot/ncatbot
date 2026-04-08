<script setup lang="ts">
</script>

<template>
  <div id="ncatbot-app">
    <header class="app-header">
      <h1>NcatBot TestUI</h1>
      <nav>
        <router-link to="/test">Test Playground</router-link>
      </nav>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f5f5;
  color: #333;
}

.app-header {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 0.75rem 1.5rem;
  background: #1a1a2e;
  color: white;
}

.app-header h1 {
  font-size: 1.2rem;
  font-weight: 600;
}

.app-header nav a {
  color: #a0a0c0;
  text-decoration: none;
  font-size: 0.9rem;
}

.app-header nav a.router-link-active {
  color: white;
}

main {
  height: calc(100vh - 3rem);
}
</style>
