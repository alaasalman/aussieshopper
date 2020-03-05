import Vue from 'vue'
import StatisticsComponent from './components/Statistics.vue'

Vue.config.productionTip = false

new Vue({
  el: '#statscontainer',
  render: h => h(StatisticsComponent)
})
