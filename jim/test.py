from . import common_classes, config
import time

# тесты модуля common_classes
my_test_message = {
    "action": "presence",
    "time": time.time(),
    "type": "status",
    "user":
    {
        "account_name": "chud0",
        "status": "online",
    },
}

my_test_message2 = {"action": "presence", "time": time.time(), "type": "status", "account_name": "chud0", "status": "online", }
my_test_message3 = {"response": "200", "time": time.time(), "alert": "no message", }


def test_message_action():
    assert common_classes.Message(my_test_message).prop_dict["action"] == "presence"


def test_message_msg():
    assert common_classes.Message(common_classes.Message(my_test_message).message).prop_dict["user"]["status"] == "online"


def test_message_type():
    assert common_classes.Message("test string").prop_dict["ERROR"] == config.SERVER_ERROR


def test_message_encoding():
    assert common_classes.Message(bytes("test", "latin1")).prop_dict["ERROR"] == config.WRONG_REQUEST
