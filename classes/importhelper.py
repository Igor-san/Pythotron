import importlib
import inspect
import os
import glob

from PyQt5.QtWidgets import QAction

def import_plugins(database, plugins_package_directory_path, disabled_plugins, available_plugins):
    """ импорт плагинов из plugins_package_directory_path и инициирование их """
    plugins_package_name = os.path.basename(plugins_package_directory_path)
    available_plugins.clear()
    # -----------------------------
    # Iterate all python files within that directory
    plugin_file_paths = glob.glob(os.path.join(plugins_package_directory_path, "*.py"))
    for plugin_file_path in plugin_file_paths:
        plugin_file_name = os.path.basename(plugin_file_path)

        module_name = os.path.splitext(plugin_file_name)[0]

        if module_name.startswith("__"):
            continue

        available_plugins.append(module_name)

        if module_name in disabled_plugins: #этот даже не импортируем
            continue
        # -----------------------------
        # Import python file
        module = importlib.import_module("." + module_name, package=plugins_package_name)

        for item in dir(module):
            if item.lower()==module_name.lower(): #нас только наш класс интересует
                value = getattr(module, item)
                value.plugin_name = module_name # добавим нужное нам поле

                yield value(database)


def import_plugin(database, plugins_package_directory_path, module_name):
    plugins_package_name = os.path.basename(plugins_package_directory_path)
    module = importlib.import_module("." + module_name, package=plugins_package_name)

    for item in dir(module):
        if item.lower()==module_name.lower(): #нас только наш класс интересует
            value = getattr(module, item)
            value.plugin_name = module_name # добавим нужное нам поле
            return value(database)
    pass