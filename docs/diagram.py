from diagrams import Cluster,Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB
from diagrams.onprem.database import Postgresql
from diagrams.programming.language import Python, Javascript
from diagrams.onprem.compute import Server
from diagrams.onprem.monitoring import Grafana
from diagrams.aws.iot import IotMqtt
from diagrams.custom import Custom

with Diagram("IOT Stack", show=False, direction="TB"): 
    with Cluster("Sensors"):
        sensors = [
            Python("Sensor 1"),
            Python("Sensor 2"),
            Python("Sensor 3"),
            Python("Sensor ...")
        ]
    
    with Cluster("Online Hosted"):
        bdd = Postgresql("Database")

    mqttbroker = Custom("", "")
    dataiku = Custom("", "./dataiku.jpg")
    bdd << dataiku
    
    sensors >> mqttbroker >> Javascript("Insert script") >> bdd << Grafana("Visualisation")
    
    with Cluster("Model Update"):
        model = Python("Model")
        predict = Python("prediction")
        dataiku >> model >> predict >> mqttbroker


    with Cluster("Real Time rediction"):
        predict >> model
