import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import PwaUpdatePrompt from './components/PwaUpdatePrompt.vue'
import './styles.css'
import './roleStyles.css'

createApp(App).use(router).component('PwaUpdatePrompt', PwaUpdatePrompt).mount('#app')
