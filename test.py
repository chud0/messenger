import pytest
import common_classes
import time


def test_message_action():
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
    assert common_classes.Message(my_test_message).prop_dict["action"] == "presence"


def test_message_msg():
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
    assert common_classes.Message(common_classes.Message(my_test_message).message).prop_dict["user"]["status"] == "online"
