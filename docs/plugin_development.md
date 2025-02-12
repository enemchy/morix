# Руководство по разработке плагинов

Morix поддерживает возможность расширения функциональности через плагины. Этот документ объясняет, как создать свой собственный плагин с использованием интерфейса `PluginInterface`.
**Плагины позволяют использовать подход [tools](https://platform.openai.com/docs/guides/function-calling) от openai.**

## Шаги для создания плагина

1. **Создание нового файла плагина**

   - Плагины находятся в директории `~/.config/morix/plugins`. Создайте новый файл с расширением `.py` в этой директории. Например, `my_plugin.py`.

2. **Реализация интерфейса `PluginInterface`**

   - В файле плагина импортируйте `PluginInterface`:

     ```python
     from morix.plugins.plugin_interface import PluginInterface
     ```

   - Создайте класс, который наследует `PluginInterface` и реализуйте метод `initialize`. Пример:

     ```python
     class MyPlugin(PluginInterface):
         def initialize(self):
             # Инициализация плагина
             pass

         def my_custom_function(self, param):
             # Логика вашей функции
             return f"Hello, {param}"
     ```

3. **Определение функций плагина в YML**

   - Плагин должен быть связан с описанием функций в файле `.yml`. Эти файлы также находятся в папке `~/.config/morix/plugins`.
   - Создайте файл `my_plugin.yml` и добавьте описание:

     ```yaml
     - type: function
       function:
         name: 'my_custom_function'
         description: 'Пример пользовательской функции'
         parameters:
           type: object
           properties:
             param:
               type: string
               description: 'Пример параметра'
           required: ['param']
           additionalProperties: false
     ```

   - название метода в .py файле и в yaml (function.name) должны совпадать и название аргументов функции должно совпадать с yml (function.parameters.properties.{arg}), так же не забудьте поправить function.parameters.required в yml. Результат выполнения функции, в случае его наличия, будет отправлен модели.

4. **Загрузка и использование плагина**

   - После написания кода плагина и описания функций в файле `.yml`, перезапустите Morix. При запуске плагин автоматически загрузится и станет доступным для использования в рамках системы.

## Пример использования плагина

Процесс добавления нового функционала становится простым благодаря этому подходу. Пример использования плагина через promt:

```text
User: вызови функцию "my_custom_function"
```

Так же можно подробно описать для чего используется эта фукнция в description в файле yml и тогда модель сама будет вызывать функцию когда сочтет нужным.
