// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import router from './router'
import BootstrapVue from 'bootstrap-vue'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'
import VueQrcode from '@xkeshi/vue-qrcode'
import datePicker from 'vue-bootstrap-datetimepicker'
import 'pc-bootstrap4-datetimepicker/build/css/bootstrap-datetimepicker.css'
import VCharts from 'v-charts'
import axios from 'axios'
import Vuex from 'vuex'
import VueI18n from 'vue-i18n'
import SimpleLineIcons from 'vue-simple-line'

Vue.component(VueQrcode.name, VueQrcode)
Vue.use(BootstrapVue)
Vue.use(datePicker)
Vue.use(VCharts)
Vue.use(Vuex)
Vue.use(VueI18n)
Vue.config.productionTip = false
Vue.prototype.$http = axios
axios.defaults.withCredentials = true
const store = new Vuex.Store({
  state: {
    status: false,
    user: {
      is_new_customer: null,
      customer_id: '',
      username: '',
      avatar: 'default/customers/avatars/2100_lab.jpg'
    },
    adminStatus: false,
    adminName: '',
    phone: '',
    money: '',
    time: '',
    address: 'http://localhost:8000/media/',
    menu: 0,
    colors: [
      '#204269',
      '#204269',
      '#204269',
      '#204269',
      '#204269',
      '#204269',
      '#204269'
    ]
  },
  mutations: {
    status (state, status = true) {
      state.status = status
      sessionStorage.setItem('status', status ? 'true' : 'false')
    },
    adminStatus (state, adminStatus = true) {
      state.adminStatus = adminStatus
      sessionStorage.setItem('adminStatus', adminStatus ? 'true' : 'false')
    },
    adminName (state, adminName) {
      state.adminName = adminName
      sessionStorage.setItem('adminName', adminName)
    },
    user (state, data) {
      state.user = data
      sessionStorage.setItem('user', JSON.stringify(data))
    },
    phone (state, number) {
      state.phone = number
      sessionStorage.setItem('phone', number)
    },
    money (state, money) {
      state.money = money
      sessionStorage.setItem('money', money)
    },
    time (state, time) {
      state.time = time
      sessionStorage.setItem('time', time)
    },
    avatar (state, avatar) {
      state.user.avatar = avatar
      sessionStorage.setItem('avatar', avatar)
    },
    logout (state) {
      state.status = false
      sessionStorage.setItem('status', 'false')
    },
    menu (state, menu) {
      state.menu = menu
      sessionStorage.setItem('menu', menu)
    },
    colors (state, id) {
      for (let i = 0; i < 7; i++) {
        state.colors[i] = '#204269'
      }
      state.colors[id] = '#5b9bd1'
      sessionStorage.setItem('colors', id)
    }
  }
})

const i18n = new VueI18n({
  locale: 'zh',
  messages: {
    zh: require('./lang/zh/zh'),
    en: require('./lang/en/en')
  }
})

Vue.component('simple-line-icons', SimpleLineIcons)

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  axios,
  store,
  i18n,
  components: { App, SimpleLineIcons },
  created () {
    if (sessionStorage.getItem('status') === 'true') {
      this.$store.commit('status')
      this.$store.commit('user', JSON.parse(sessionStorage.getItem('user')))
      this.$store.commit('phone', sessionStorage.getItem('phone'))
      this.$store.commit('money', sessionStorage.getItem('money'))
      this.$store.commit('time', sessionStorage.getItem('time'))
      this.$store.commit('avatar', sessionStorage.getItem('avatar'))
      this.$store.commit('menu', sessionStorage.getItem('menu'))
    }
    axios
      .post('http://localhost:8000/api/v1/core/auth/is-authenticated/', {
        withCredentials: true
      })
      .then(res => {
        if (res.data.is_authenticated) {
          this.$store.commit('adminStatus')
          this.$store.commit('adminName')
          this.$store.commit('menu', sessionStorage.getItem('menu'))
          this.$store.commit('colors', sessionStorage.getItem('colors'))
        }
      })
  },
  template: '<App/>'
}).$mount('#app')
