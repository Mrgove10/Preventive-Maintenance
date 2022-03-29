const mqtt = require('mqtt')
const client = mqtt.connect('mqtt://iamosquitto:10083')
const { InfluxDB, Point } = require("@influxdata/influxdb-client");


client.on('connect', function () {
  client.subscribe('sensor/#', function (err) {
    if (!err) {
      // client.publish('presence', 'Hello mqtt')
      console.log("Connection initiated")
    }
  })
})

client.on('message', function (topic, message) {
  // message is Buffer
  console.log(topic.charAt(topic.length - 1))
  console.log(message.toString())
  message = message.toJSON()

  const writeApi = new InfluxDB({ url: "http://iainflux:8086/", token: "my-super-secret-auth-token" }).getWriteApi("my-org", "my-bucket", 's')
  const point = new Point("temperature")
    .tag("sensor", 1)
    .floatField("temp_process", message['Process temperature [K]'])
    .floatField("temp_air", message['Air temperature [K]'])
    .intField("udi",message["UDI"])
    .stringField("product_id", message['Product ID'])
    .floatField("speed_rot", message['Rotational speed [rpm]'])
    .timestamp(new Date());

  writeApi.writePoint(point);

  writeApi
    .close()
    .then((f) => {
      console.log(f)
      console.log("FINISHED");
    })
    .catch((e) => {
      console.error(e);
      console.log("Finished ERROR");
    });
})
