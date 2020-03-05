<template>
  <div id="stats">
    <bar-chart :chart-data="chartObject"/>
  </div>
</template>

<script>
  import axios from 'axios'
  import BarChart from './BarChart.js'

  export default {
    name: 'StatsComponent',
    components: {
      BarChart,
    },
    props: {},
    data () {
      return {
        chartObject: null,
      }
    },
    mounted () {
      this.updateChartData()
    },
    methods: {

      updateChartData: function () {
        axios.get('/api/stats/deal-data-monthly/').then((response) => {
          this.chartObject = {
            labels: response.data.labels,
            datasets: [
              {
                label: response.data.label,
                backgroundColor: '#f87979',
                data: response.data.data,
              },
            ],
          }

        }).catch(function (error) {
          console.log(error)
        })
      },
    },
  }
</script>

<!-- Scoped component css -->
<style scoped>
  #stats {
    text-align: center;
  }
</style>
