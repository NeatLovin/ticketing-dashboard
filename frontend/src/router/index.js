// src/router/index.js
import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import OverviewView from "../views/OverviewView.vue";
import TicketsView from "../views/TicketsView.vue";
import DashboardView from "../views/DashboardView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "home",
      component: HomeView,
    },
    {
      path: "/overview",
      name: "overview",
      component: OverviewView,
    },
    {
      path: "/dashboard",
      name: "dashboard",
      component: DashboardView,
    },
    {
      path: "/tickets",
      name: "tickets",
      component: TicketsView,
    },
  ],
});

export default router;
