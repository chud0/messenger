import log_config
import traceback
from functools import wraps


class Log():
    """Создает декоратор для логирования функции, применять с осторожностью"""
    deco_log = logging.getLogger("msg.deco")

    def __init__(self):
        pass

    def __call__(self, func):
        @wraps(func)
        def decorated(*args, **kwargs):
            LVL = -2  # уровень вложенности
            NAME_FUNC_POS = -2  # название функции в выводе traceback
            temp = [f[NAME_FUNC_POS] for f in traceback.extract_stack()][LVL]
            Log.deco_log.info("Функция %s была вызвана из функции %s с аргуметами %s",
                              str(func.__name__), temp, str(args))  # получать аргументом, переделать
            return func(*args, **kwargs)
        return decorated
