from diagrams import Cluster,Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB
from diagrams.onprem.database import Postgresql
from diagrams.programming.language import Python, Javascript
from diagrams.onprem.compute import Server
from diagrams.onprem.monitoring import Grafana
from diagrams.aws.iot import IotMqtt

with Diagram("IOT Stack", show=False): 
    with Cluster("Sensors"):
        sensors = [
            Python("Sensor 1"),
            Python("Sensor 2"),
            Python("Sensor 3"),
            Python("Sensor ...")
        ]
    sensors >> IotMqtt("mosquitto") >> Javascript("Insert script") >> Postgresql("Database") << Grafana("Visialisaton")