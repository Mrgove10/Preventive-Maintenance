const mqtt = require('mqtt')
const client  = mqtt.connect('mqtt://iamosquitto:10083')

client.on('connect', function () {
  client.subscribe('sensor/#', function (err) {
    if (!err) {
      client.publish('presence', 'Hello mqtt')
    }
  })
})

client.on('message', function (topic, message) {
  // message is Buffer
  console.log(message.toString())
  client.end()
})