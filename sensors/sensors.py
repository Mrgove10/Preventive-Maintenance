import csv
import json
from pathlib import Path
import time
import paho.mqtt.client as MQTTLib
from typer import Typer

cli = Typer()

def on_connect(client, userdata, flags, rc):
    print(userdata)
    print(flags)
    print("Connection returned result: " + MQTTLib.connack_string(rc))

def etablish_mqtt_connexion():
    client = MQTTLib.Client()
    client.on_connect = on_connect
    client.connect("iamosquitto", 10083, 60)

    return client

def publish(*, topic: str, payload: str):
    client = etablish_mqtt_connexion()
    client.publish(topic, payload)

def create_csv_file(header: str, d: list, index: int):
    if not d:
        return

    data = []
    for row in d:
        data.append(",".join(row))

    with open(f"/data/{index}.csv", "w") as f:
        f.writelines(",".join(header))
        f.write("\n")
        f.writelines("\n".join(data))

@cli.command()
def split_file():
    # NOTE: to change
    chunk_size = 1000
    line_numbers = 0
    header = []

    with open("/data/dataset_MP.csv") as f:

        list_data = list(csv.reader(f, delimiter=","))
        line_numbers = len(list_data)

        header = list_data.pop(0)

        index = 0
        for i in range(0, line_numbers, chunk_size):
            create_csv_file(header, list_data[i : i + chunk_size], index)
            index += 1


@cli.command()
def file_to_mqtt():
    path = Path("/data")

    for file in path.iterdir():
        if file.name != "dataset_MP.csv":
            content = file.read_text()
            print(f"sensor/{file.stem}")
            publish(topic=f"sensor/{file.stem}", payload=json.dumps(content.split("\n").pop(0)))
            time.sleep(60)

if __name__ == "__main__":
    cli()