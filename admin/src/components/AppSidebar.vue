<script setup>
import { RouterLink } from 'vue-router'
import { AppSidebarNav } from '@/components/AppSidebarNav.js'
import { useSidebarStore } from '@/stores/sidebar.js'

const sidebar = useSidebarStore()
</script>

<template>
  <CSidebar class="border-end" colorScheme="dark" position="fixed" :unfoldable="sidebar.unfoldable" :visible="sidebar.visible" @visible-change="(value) => sidebar.toggleVisible(value)">
    <CSidebarHeader class="border-bottom">
      <RouterLink custom to="/" v-slot="{ href, navigate }">
        <CSidebarBrand v-bind="$attrs" as="a" :href="href" @click="navigate">
          <div class="sidebar-brand-full d-flex align-items-center">
            <span class="text-primary fw-bold fs-4">HavoSec</span>
            <span class="text-white ms-2 small">Admin</span>
          </div>
          <div class="sidebar-brand-narrow"><span class="text-primary fw-bold fs-5">HS</span></div>
        </CSidebarBrand>
      </RouterLink>
      <CCloseButton class="d-lg-none" dark @click="sidebar.toggleVisible()" />
    </CSidebarHeader>
    <AppSidebarNav />
    <CSidebarFooter class="border-top d-none d-lg-flex"><CSidebarToggler @click="sidebar.toggleUnfoldable()" /></CSidebarFooter>
  </CSidebar>
</template>
