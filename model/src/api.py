from flask import Flask, request

import pickle
import json
import paho.mqtt.client as MQTTLib
import pandas as pd
from sqlalchemy import create_engine, insert, Table, MetaData, Column, CHAR, Float, Boolean
from . import script

app = Flask(__name__)
meta = MetaData()
engine = create_engine(
    "postgresql://uxtidv9o5ybxot1fszs9:YLVmIztDDVLfRQcYy2ji@b3dgnxzuiidmblheqmre-postgresql.services.clever-cloud.com:5432/b3dgnxzuiidmblheqmre")
Predictions = Table(
    'predictions',
    meta,
    Column('type', CHAR(1)),
    Column('air_temperature_k', Float),
    Column('process_temperature_k', Float),
    Column('rotational_speed_rpm', Float),
    Column('torque_nm', Float),
    Column('tool_wear_min', Float),
    Column('twf', Boolean),
    Column('hdf', Boolean),
    Column('pwf', Boolean),
    Column('osf', Boolean),
    Column('rnf', Boolean),
    Column('machine_failure', Boolean),
)


def create_table():
    meta.create_all(engine)


def persist_in_database(raw, machine_failure):
    with engine.connect() as conn:
        stmt = insert(Predictions).values(
            type=raw[0],
            air_temperature_k=raw[1],
            process_temperature_k=raw[2],
            rotational_speed_rpm=raw[3],
            torque_nm=raw[4],
            tool_wear_min=raw[5],
            twf=raw[6],
            hdf=raw[7],
            pwf=raw[8],
            osf=raw[9],
            rnf=raw[10],
            machine_failure=machine_failure[0],
        )
        conn.execute(stmt)


def on_connect(client, userdata, flags, rc):
    print("Connection returned result: " + MQTTLib.connack_string(rc))


def on_message(client, userdata, msg):
    json_payload = json.dumps(msg.payload)
    print(json_payload)
    persist_in_database(json_payload)


def predict(row):
    dataframe = pd.DataFrame({
        "type": [row[0]],
        "air_temperature_k": [row[1]],
        "process_temperature_k": [row[2]],
        "rotational_speed_rpm": [row[3]],
        "torque_nm": [row[4]],
        "tool_wear_min": [row[5]],
        "twf": [row[6]],
        "hdf": [row[7]],
        "pwf": [row[8]],
        "osf": [row[9]],
        "rnf": [row[10]],
    })

    mapping = {
        "type": ["type_value_M", "type_value_H", "type_value_L"],
        "twf": ["twf_value_0", "twf_value_1"],
        "hdf": ["hdf_value_0", "hdf_value_1"],
        "pwf": ["pwf_value_0", "pwf_value_1"],
        "osf": ["osf_value_0", "osf_value_1"],
        "rnf": ["rnf_value_0", "rnf_value_1"],
    }

    def parse_raw_to_features(df: pd.DataFrame) -> None:
        """Alterate base dataframe to fit with expected features from the model"""

        def process_type():
            type = df["type"][0]
            df[f"type_value_{type}"] = 1.0
            del df["type"]

        def process_booleans():
            for k in mapping.keys():
                # Type if already handled on `process_type` function
                if k == "type":
                    continue
                v = df[k][0]
                df[f"{k}_value_{v}"] = v
                del df[k]

        # Create dummies keys with default value (0.0)
        for v in mapping.values():
            for k in v:
                df[k] = 0.0

        process_type()
        process_booleans()

    parse_raw_to_features(dataframe)

    with open("prod_model.pkl", "rb") as m:
        model = pickle.loads(m.read())
        r = model.predict(dataframe)
        return r


@app.route('/', methods=['POST'])
def set_data():
    row = request.json["data"]
    prediction = predict(row)
    persist_in_database(row, prediction)
    return "null"


@app.route('/update_model', methods=['GET'])
def update_model():
    script.update_model()
    return "updated"
