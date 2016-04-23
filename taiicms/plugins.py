import os
import json

from . import app, config, save_config

plugins = {}

def refresh_plugins():
    global plugins
    plugins = {}

    # get a list of all the folders in `/plugins`
    plugin_names = []
    for root, dirs, files in os.walk("plugins"):
        plugin_names = dirs
        break

    # read each plugins `plugin.json` and
    # add the default config to the config file
    for p in plugin_names:
        if os.path.exists(os.path.join("plugins", p, "default_config.json")):
            default_config = json.load(open(os.path.join("plugins", p, "default_config.json")))
        else:
            default_config = {}
        default_config["enabled"] = False

        if p not in config["plugins"]:
            config["plugins"][p] = default_config



        plugin_info = json.load(open(os.path.join("plugins", p, "plugin.json")))
        plugin_info["config"] = config["plugins"][p]
        plugin_info["default_config"] = default_config
        plugin_info["name"] = p

        plugins[p] = plugin_info

    # check the dependencies on all plugins
    # mark as broken if they're missing something
    for plugin in plugins.values():
        print(plugin)
        for dep in plugin["depends"]:
            if dep not in plugin:
                plugin["status"] = {
                    "status": "broken",
                    "reason": "missing_dependencies",
                }
            else:
                plugin["status"] = {
                    "status": "functional",
                    "reason": None
                }

    save_config()

refresh_plugins()


def load_plugin(plugin_name):
    if plugin_name not in plugins:
        refresh_plugins()
        if plugin_name not in plugins:
            raise ValueError("%s does not exist.")

    plugin = plugins[plugin_name]
    if os.path.exists(os.path.join("plugins", plugin_name, "__init__.py")):
        plugin["import"] = getattr(__import__("plugins.%s" % plugin_name), plugin_name)
        plugin["import"].main(plugin["config"])


def load_plugins():
    for plugin_name, plugin_config in config["plugins"].items():
        if not plugin_config["enabled"]:
            continue
        load_plugin(plugin_name)


load_plugins()

@app.route("/plugins/<path:path>")
def plugins(path):
    path_parts = path.split("/")[0]
    plugin, f_path = path_parts[0], path_parts[1:]

    try:
        if config["plugins"][plugin]["enabled"]:
            pass
    except:
        pass
