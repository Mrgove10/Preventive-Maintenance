const mqtt = require('mqtt')
const client = mqtt.connect('mqtt://iamosquitto:10083')
const { Pool } = require('pg');
require('dotenv').config()


const PSQLPool = new Pool({
    user: process.env.DB_USER,
    host: process.env.DB_HOST,
    database: process.env.DB_DATABASE,
    password: process.env.DB_PASSWORD,
    port: 5432,
})

let is_database_connected = false;


client.on('connect', function () {
    client.subscribe('sensor/#', function (err) {
        if (!err) {
            console.log("Connection initiated")
        }
    })
})

client.on('message', function (topic, message) {
    persistData(JSON.parse(message))
})

async function persistData({ _, product_id, type, air_temperature_k, process_temperature_k, rotational_speed_rpm, torque_nm, tool_wear_min, machine_failure, TWF, HDF, PWF, OSF, RNF }) {

    await PSQLPool.query(`
        INSERT INTO sensor_data (
            product_id,
            type,
            air_temperature_k,
            process_temperature_k,
            rotational_speed_rpm,
            torque_nm,
            tool_wear_min,
            machine_failure,
            TWF,
            HDF,
            PWF,
            OSF,
            RNF
        ) VALUES('${product_id}','${type}',${air_temperature_k},${process_temperature_k},${rotational_speed_rpm},${torque_nm},${tool_wear_min},${machine_failure},${TWF},${HDF},${PWF},${OSF}, ${RNF});
    `);

}
