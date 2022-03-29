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
  console.log(message.toString())
  // client.end()
  const url = "http://iainflux:8086";
  const token = "my-super-secret-auth-token";
  const org = "my-org";
  const bucket = "my-bucket";

  const influxclient = new InfluxDB({ url: url, token: token });
  const writeApi = influxclient.getWriteApi(org, bucket);
  const point = new Point("weatherstation")
    .tag("sensor", 1)
    .floatField("temperature", 23.4)
    .timestamp(new Date());

  writeApi.writePoint(point);

  writeApi
    .close()
    .then(() => {
      console.log("FINISHED");
    })
    .catch((e) => {
      console.error(e);
      console.log("Finished ERROR");
    });
})
