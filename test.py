import jim.common_classes as common_classes
import pytest
import server
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


def test_message_action():
    assert common_classes.Message(my_test_message).prop_dict["action"] == "presence"


def test_message_msg():
    assert common_classes.Message(common_classes.Message(my_test_message).message).prop_dict["user"]["status"] == "online"


def test_message_format():
    assert common_classes.Message("test string").prop_dict["ERROR"] == "400"

# тесты модуля common_classes


test_clnt = server.IncomingClient(("A", "B"))


def test_processing_msg():
    # подготовка:
    temp = test_clnt.get_action_msg
    test_clnt.get_action_msg = lambda x: test_list.append(list(x.values())[0])
    test_list = []
    test_clnt.last_msg = [{"action": 1}, {"action": 2}, {"action": 3}]
    # тестируемая ф-ия:
    test_clnt.processing_msg()
    assert test_list == [1, 2, 3]
    assert test_clnt.last_msg == []
    # возвращаю настоящий метод
    test_clnt.get_action_msg = temp


def test_get_response():
    assert test_clnt.get_response(200)["response"] == 200
    assert test_clnt.get_response(205) is None


test2_clnt = server.IncomingClient(("C", "D"))


def test_get_action_msg():
    test_clnt.get_action_msg("1")
    assert common_classes.Message(test_clnt.next_msg[-1]).prop_dict["response"] == 400
    test_clnt.get_action_msg(my_test_message)
    assert common_classes.Message(test_clnt.next_msg[-1]).prop_dict["response"] == 200
    test_clnt.get_action_msg({"action": "msg", "msg": "test"})
    # сообщения приходят клиентам, кроме себя:
    assert common_classes.Message(test_clnt.next_msg[-1]).prop_dict["response"] == 200
    assert common_classes.Message(test2_clnt.next_msg[-1]).prop_dict["msg"] == "test"
