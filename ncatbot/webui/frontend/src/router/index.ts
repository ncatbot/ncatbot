import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/test',
    },
    {
      path: '/test',
      name: 'test',
      component: () => import('../views/TestPlayground.vue'),
    },
  ],
})

export default router
