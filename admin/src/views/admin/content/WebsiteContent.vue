<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAdminDataStore } from '@/stores/adminData'

const dataStore = useAdminDataStore()
const isLoading = ref(true)
const activeSection = ref('hero')
const isSaving = ref(false)
const saveMessage = ref('')

const sections = [
  { key: 'hero', name: 'Hero Section', icon: 'cil-home' },
  { key: 'achievements', name: 'Achievements', icon: 'cil-chart' },
  { key: 'features', name: 'Features', icon: 'cil-puzzle' },
  { key: 'services', name: 'Services', icon: 'cil-briefcase' },
  { key: 'offensive_model', name: 'Offensive Model', icon: 'cil-shield-alt' },
  { key: 'defensive_model', name: 'Defensive Model', icon: 'cil-lock-locked' },
  { key: 'demo_cta', name: 'Demo CTA', icon: 'cil-bullhorn' },
  { key: 'about_hero', name: 'About Hero', icon: 'cil-info' },
  { key: 'about_mission', name: 'Mission', icon: 'cil-target' },
  { key: 'about_vision', name: 'Vision', icon: 'cil-lightbulb' },
  { key: 'about_values', name: 'Values', icon: 'cil-heart' },
  { key: 'footer', name: 'Footer', icon: 'cil-layers' },
]

const content = computed(() => dataStore.content)
const currentContent = computed(() => content.value[activeSection.value]?.content || {})

onMounted(async () => {
  await dataStore.fetchContent()
  isLoading.value = false
})

async function saveContent() {
  isSaving.value = true
  saveMessage.value = ''
  const result = await dataStore.updateContent(activeSection.value, currentContent.value)
  if (result.success) {
    saveMessage.value = 'Content saved successfully!'
    setTimeout(() => saveMessage.value = '', 3000)
  } else {
    saveMessage.value = `Error: ${result.error}`
  }
  isSaving.value = false
}

function addItem(arrayKey) {
  if (!currentContent.value[arrayKey]) currentContent.value[arrayKey] = []
  currentContent.value[arrayKey].push({ id: Date.now(), title: '', description: '' })
}

function removeItem(arrayKey, index) {
  currentContent.value[arrayKey].splice(index, 1)
}
</script>

<template>
  <div>
    <CCard class="mb-4">
      <CCardHeader class="d-flex justify-content-between align-items-center">
        <strong>Website Content Management</strong>
        <CButton color="primary" @click="saveContent" :disabled="isSaving" data-testid="save-content-btn">
          <CSpinner v-if="isSaving" size="sm" class="me-2" />{{ isSaving ? 'Saving...' : 'Save Changes' }}
        </CButton>
      </CCardHeader>
      <CCardBody>
        <CAlert v-if="saveMessage" :color="saveMessage.includes('Error') ? 'danger' : 'success'">{{ saveMessage }}</CAlert>
        <div v-if="isLoading" class="text-center py-5"><CSpinner color="primary" /></div>
        <CRow v-else>
          <CCol :md="3">
            <CListGroup>
              <CListGroupItem v-for="section in sections" :key="section.key" component="button" :active="activeSection === section.key" @click="activeSection = section.key" class="d-flex align-items-center">
                <CIcon :icon="section.icon" class="me-2" />{{ section.name }}
              </CListGroupItem>
            </CListGroup>
          </CCol>
          <CCol :md="9">
            <CCard>
              <CCardHeader><strong>{{ sections.find(s => s.key === activeSection)?.name }}</strong></CCardHeader>
              <CCardBody>
                <!-- Hero -->
                <template v-if="activeSection === 'hero'">
                  <div class="mb-3"><CFormLabel>Title</CFormLabel><CFormInput v-model="currentContent.title" /></div>
                  <div class="mb-3"><CFormLabel>Subtitle</CFormLabel><CFormInput v-model="currentContent.subtitle" /></div>
                  <div class="mb-3"><CFormLabel>Description</CFormLabel><CFormTextarea v-model="currentContent.description" rows="4" /></div>
                  <CRow><CCol :md="6"><div class="mb-3"><CFormLabel>Primary Button Text</CFormLabel><CFormInput v-model="currentContent.primaryButtonText" /></div></CCol><CCol :md="6"><div class="mb-3"><CFormLabel>Primary Button Link</CFormLabel><CFormInput v-model="currentContent.primaryButtonLink" /></div></CCol></CRow>
                </template>
                <!-- About Hero -->
                <template v-else-if="activeSection === 'about_hero'">
                  <div class="mb-3"><CFormLabel>Title</CFormLabel><CFormInput v-model="currentContent.title" /></div>
                  <div class="mb-3"><CFormLabel>Description</CFormLabel><CFormTextarea v-model="currentContent.description" rows="3" /></div>
                </template>
                <!-- Mission/Vision -->
                <template v-else-if="activeSection === 'about_mission' || activeSection === 'about_vision'">
                  <div class="mb-3"><CFormLabel>Title</CFormLabel><CFormInput v-model="currentContent.title" /></div>
                  <div class="mb-3"><CFormLabel>Text</CFormLabel><CFormTextarea v-model="currentContent.text" rows="5" /></div>
                </template>
                <!-- Demo CTA -->
                <template v-else-if="activeSection === 'demo_cta'">
                  <div class="mb-3"><CFormLabel>Title</CFormLabel><CFormInput v-model="currentContent.title" /></div>
                  <div class="mb-3"><CFormLabel>Description</CFormLabel><CFormTextarea v-model="currentContent.description" rows="3" /></div>
                  <CRow><CCol :md="6"><div class="mb-3"><CFormLabel>Button Text</CFormLabel><CFormInput v-model="currentContent.buttonText" /></div></CCol><CCol :md="6"><div class="mb-3"><CFormLabel>Button Link</CFormLabel><CFormInput v-model="currentContent.buttonLink" /></div></CCol></CRow>
                </template>
                <!-- Offensive/Defensive Model -->
                <template v-else-if="activeSection === 'offensive_model' || activeSection === 'defensive_model'">
                  <div class="mb-3"><CFormLabel>Title</CFormLabel><CFormInput v-model="currentContent.title" /></div>
                  <div class="mb-3"><CFormLabel>Description</CFormLabel><CFormTextarea v-model="currentContent.description" rows="3" /></div>
                  <div class="mb-3"><CFormLabel>Features (one per line)</CFormLabel><CFormTextarea :value="currentContent.features?.join('\n')" @input="currentContent.features = $event.target.value.split('\n')" rows="5" /></div>
                </template>
                <!-- Footer -->
                <template v-else-if="activeSection === 'footer'">
                  <div class="mb-3"><CFormLabel>Company Name</CFormLabel><CFormInput v-model="currentContent.companyName" /></div>
                  <div class="mb-3"><CFormLabel>Tagline</CFormLabel><CFormInput v-model="currentContent.tagline" /></div>
                  <div class="mb-3"><CFormLabel>Copyright Text</CFormLabel><CFormInput v-model="currentContent.copyrightText" /></div>
                </template>
                <!-- Achievements -->
                <template v-else-if="activeSection === 'achievements'">
                  <div v-for="(item, index) in currentContent.items" :key="index" class="border rounded p-3 mb-3">
                    <div class="d-flex justify-content-between mb-2"><strong>Item {{ index + 1 }}</strong><CButton color="danger" size="sm" @click="removeItem('items', index)"><CIcon icon="cil-trash" /></CButton></div>
                    <CRow><CCol :md="6"><CFormLabel>Number</CFormLabel><CFormInput v-model="item.number" /></CCol><CCol :md="6"><CFormLabel>Label</CFormLabel><CFormInput v-model="item.label" /></CCol></CRow>
                  </div>
                  <CButton color="primary" variant="outline" @click="addItem('items')"><CIcon icon="cil-plus" class="me-2" />Add Item</CButton>
                </template>
                <!-- Features -->
                <template v-else-if="activeSection === 'features'">
                  <div class="mb-3"><CFormLabel>Section Title</CFormLabel><CFormInput v-model="currentContent.title" /></div>
                  <hr />
                  <div v-for="(feature, index) in currentContent.features" :key="index" class="border rounded p-3 mb-3">
                    <div class="d-flex justify-content-between mb-2"><strong>Feature {{ index + 1 }}</strong><CButton color="danger" size="sm" @click="removeItem('features', index)"><CIcon icon="cil-trash" /></CButton></div>
                    <div class="mb-2"><CFormLabel>Title</CFormLabel><CFormInput v-model="feature.title" /></div>
                    <div class="mb-2"><CFormLabel>Description</CFormLabel><CFormTextarea v-model="feature.description" rows="2" /></div>
                    <div class="mb-2"><CFormLabel>Benefit</CFormLabel><CFormInput v-model="feature.benefit" /></div>
                  </div>
                  <CButton color="primary" variant="outline" @click="addItem('features')"><CIcon icon="cil-plus" class="me-2" />Add Feature</CButton>
                </template>
                <!-- Services -->
                <template v-else-if="activeSection === 'services'">
                  <div class="mb-3"><CFormLabel>Section Title</CFormLabel><CFormInput v-model="currentContent.title" /></div>
                  <hr />
                  <div v-for="(service, index) in currentContent.services" :key="index" class="border rounded p-3 mb-3">
                    <div class="d-flex justify-content-between mb-2"><strong>Service {{ index + 1 }}</strong><CButton color="danger" size="sm" @click="removeItem('services', index)"><CIcon icon="cil-trash" /></CButton></div>
                    <div class="mb-2"><CFormLabel>Name</CFormLabel><CFormInput v-model="service.name" /></div>
                    <div class="mb-2"><CFormLabel>Description</CFormLabel><CFormTextarea v-model="service.description" rows="2" /></div>
                  </div>
                  <CButton color="primary" variant="outline" @click="addItem('services')"><CIcon icon="cil-plus" class="me-2" />Add Service</CButton>
                </template>
                <!-- Values -->
                <template v-else-if="activeSection === 'about_values'">
                  <div v-for="(value, index) in currentContent.values" :key="index" class="border rounded p-3 mb-3">
                    <div class="d-flex justify-content-between mb-2"><strong>Value {{ index + 1 }}</strong><CButton color="danger" size="sm" @click="removeItem('values', index)"><CIcon icon="cil-trash" /></CButton></div>
                    <div class="mb-2"><CFormLabel>Title</CFormLabel><CFormInput v-model="value.title" /></div>
                    <div class="mb-2"><CFormLabel>Description</CFormLabel><CFormTextarea v-model="value.description" rows="2" /></div>
                  </div>
                  <CButton color="primary" variant="outline" @click="addItem('values')"><CIcon icon="cil-plus" class="me-2" />Add Value</CButton>
                </template>
                <template v-else><CAlert color="info">Select a section from the left to edit.</CAlert></template>
              </CCardBody>
            </CCard>
          </CCol>
        </CRow>
      </CCardBody>
    </CCard>
  </div>
</template>
