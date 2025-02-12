import sys
from prompt_toolkit.key_binding import KeyBindings
from morix.helpers import console_print
from .settings import config

bindings = KeyBindings()

@bindings.add('c-c')
@bindings.add('c-d')
def _(event):
    """
    Exit the application

    Args:
        event: The event object from prompt_toolkit.
    """
    exit()

@bindings.add('c-e')
def _(event):
    """
    Toggle the 'wait for enter' configuration on Ctrl+W.

    Args:
        event: The event object from prompt_toolkit.
    """
    config.console_commands.wait_enter_before_run = not config.console_commands.wait_enter_before_run
    sys.stdout.write("\033[0G")
    console_print(left="[#268bd2]User:[/#268bd2]", right=f"wait enter is '{config.console_commands.wait_enter_before_run}'")
    sys.stdout.write("\r\033[F")
    sys.stdout.write("\033[6C")
    print(event.app.current_buffer.text, end="")

# Добавляем метод для получения зарегистрированных клавиш для тестирования

def get_bindings():
    return bindings._bindings

bindings.get_bindings = get_bindings
