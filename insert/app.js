const mqtt = require('mqtt')
const client = mqtt.connect('mqtt://iamosquitto:10083')
const { InfluxDB, Point } = require("@influxdata/influxdb-client");


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
setInterval(() => {
  console.log("COUCOU")
}, 2500);


setTimeout(() => {
  // const url = "https://us-west-2-1.aws.cloud2.influxdata.com";
  const url = "http://iainflux:10086";
  const token = "my-token";
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
}, 30000);
