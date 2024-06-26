from configparser import ConfigParser
from core import config
from core import zm_ftp_lib
import json
import logging
from logging.handlers import RotatingFileHandler
import paho.mqtt.client as mqtt

CONFIG = config.load_config("core/config.ini")
LOG_FILE = "cvd.log"
FTP = zm_ftp_lib.ZM_FTP(CONFIG)

MQTT_BROKER = CONFIG["MQTT"]["MQTT_BROKER"]
MQTT_USER = CONFIG["MQTT"]["MQTT_USER"]
MQTT_PASSWD = CONFIG["MQTT"]["MQTT_PASSWD"]
MQTT_TOPIC = CONFIG["MQTT"]["TOPIC"]


def check_recipe_format(recipe):
    return True


def on_connect(client, userdata, flags, reason_code, properties=""):
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    # parse message
    try:
        msg_decoded = msg.payload.decode()
        logging.info(msg.topic+" " + msg_decoded)
        recipe = json.loads(msg_decoded)
        if check_recipe_format(recipe) is False:
            raise ValueError("Recipe check failed")

        FTP.write_recipe(msg_decoded)

    except Exception as e:
        logging.warning(f"Recipe load error {e}")
        return


if __name__ == "__main__":
    # logging init
    from logging.handlers import RotatingFileHandler

    logHandler = RotatingFileHandler(LOG_FILE, mode="a", maxBytes=10*1024*1024,
                                     backupCount=2, encoding=None, delay=0)
    logFormatter = logging.Formatter(
        "%(asctime)s %(levelname)s -> %(message)s")
    logHandler.setFormatter(logFormatter)
    logHandler.setLevel(logging.INFO)
    meshLog = logging.getLogger("root")
    meshLog.setLevel(logging.INFO)
    meshLog.addHandler(logHandler)
    # mqtt init
    mqttc = mqtt.Client()
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.username_pw_set(MQTT_USER, MQTT_PASSWD)
    mqttc.connect(MQTT_BROKER, 1883, 60)

    mqttc.loop_forever()
    FTP.quit()
