import importlib
import inspect
import os
import glob

def import_plugins(database, plugins_package_directory_path):
    """ импорт плагинов из plugins_package_directory_path и инициирование их """
    plugins_package_name = os.path.basename(plugins_package_directory_path)

    # -----------------------------
    # Iterate all python files within that directory
    plugin_file_paths = glob.glob(os.path.join(plugins_package_directory_path, "*.py"))
    for plugin_file_path in plugin_file_paths:
        plugin_file_name = os.path.basename(plugin_file_path)

        module_name = os.path.splitext(plugin_file_name)[0]

        if module_name.startswith("__"):
            continue

        # -----------------------------
        # Import python file
        module = importlib.import_module("." + module_name, package=plugins_package_name)

        for item in dir(module):
            if item.lower()==module_name.lower(): #нас только наш класс интересует
                value = getattr(module, item)
                yield value(database)

