import os
import json
import importlib
import pip
import sys

from flask import send_from_directory, abort, render_template

from . import app, config, save_config, site, merge_dicts, root_logger


logger = root_logger.getChild("plugins")


IS_VIRTUAL_ENV = hasattr(sys, "real_prefix")
if not IS_VIRTUAL_ENV:
    logger.info("Running outside virtualenv... Creating own modules folder")
    IMPORT_PATH = os.path.abspath("./imports")
    os.makedirs(IMPORT_PATH, exist_ok=True)
    sys.path.append(IMPORT_PATH)
else:
    IMPORT_PATH = None


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
        logger.info("Loading plugin '%s'" % p)
        if os.path.exists(os.path.join("plugins", p, "default_config.json")):
            default_config = json.load(open(os.path.join("plugins", p, "default_config.json")))
        else:
            default_config = {}
        default_config["enabled"] = False

        if p not in config["plugins"]:
            config["plugins"][p] = default_config
        else:
            config["plugins"][p] = merge_dicts(default_config, config["plugins"][p])



        plugin_info = json.load(open(os.path.join("plugins", p, "plugin.json")))
        plugin_info["config"] = config["plugins"][p]
        plugin_info["default_config"] = default_config
        plugin_info["name"] = p

        plugins[p] = plugin_info

    # check the dependencies on all plugins
    # mark as broken if they're missing something
    for plugin in plugins.values():
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
            raise ValueError("Plugin '%s' does not exist but was specified in the config.")

    plugin = plugins[plugin_name]
    if os.path.exists(os.path.join("plugins", plugin_name, "__init__.py")):
        if "module_requirements" in plugin:
            logger.info("Installing modules for %s." % plugin_name)
            for req, link in plugin["module_requirements"].items():
                # check if req is already installed
                if importlib.util.find_spec(req) is None:
                    logger.warn("Could not find '%s'. Installing via pip..." % req)

                    args = ["install", link]
                    if not IS_VIRTUAL_ENV:
                        args.append("--target=%s" % "./imports")

                    result = pip.main(args)
                    if result != 0:
                        logger.error("Could not install '%s'. Disabling plugin." % req)
                        config["plugins"][plugin_name]["enabled"] = False
                        save_config()
                        return

        plugin["import"] = getattr(__import__("plugins.%s" % plugin_name), plugin_name)
        plugin["import"].main(plugin["config"])

    if "pages" in plugin:
        for path, page in plugin["pages"].items():
            if isinstance(page, str):
                page = {"file_path": page}

            if "file_path" in page:
                site.pages[path] = {
                    "file_path": "/".join(("", "plugins", plugin_name, page["file_path"]))
                }
            elif "element" in page:
                site.pages[path] = {
                    "element": page["element"]
                }


def load_plugins():
    for plugin_name, plugin_config in config["plugins"].items():
        if not plugin_config["enabled"]:
            continue
        load_plugin(plugin_name)


load_plugins()

@app.route("/plugins/<string:plugin>/<path:path>")
def plugin_file_resolver(plugin, path):
    plugin = plugin.lower()
    try:
        if config["plugins"][plugin]["enabled"]:
            # serve from root dir, not flasks root
            f_dir = os.path.join(os.path.abspath("."), "plugins", plugin)

            # this appears to be secure. might need more testing.
            return send_from_directory(f_dir, path)
    except KeyError:
        abort(404)

@app.route("/plugin-components.html")
def plugin_components():
    return render_template("plugin-components.html", plugins=plugins)
