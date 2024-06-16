"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os
import pickle
import shutil
from pathlib import Path

import qtpy.QtCore as qtc

import utilities as utils
from main import MainApp
from plugin_parser import PluginParser


class Cacher:
    """
    Class for managing cache data in SSE-AT/data/cache.
    """

    log = logging.getLogger("Cacher")

    __plugin_states_cache: dict[str, tuple[bool, utils.Plugin.Status]] = {}
    """
    This cache is persistent
    and stores the states of the plugins of a modlist.
    """

    def __init__(self, app: MainApp):
        self.app = app

        self.path = app.cache_path

    def load_caches(self):
        """
        Loads available caches.
        """

        if self.path.is_dir():
            self.log.info("Loading caches...")

            plugin_states_cache_path = self.path / "plugin_states.cache"

            if plugin_states_cache_path.is_file():
                self.load_plugin_states_cache(plugin_states_cache_path)

            self.log.info("Caches loaded.")

    def get_plugin_strings(self, plugin_path: Path):
        """
        Gets strings of `plugin_path` from cache or extracts them if not in cache.
        """

        identifier = utils.get_file_identifier(plugin_path)

        cache_file = self.path / "plugin_strings" / f"{identifier}.cache"

        if not cache_file.is_file():
            plugin_parser = PluginParser(plugin_path)
            strings = [
                string
                for group in plugin_parser.extract_strings().values()
                for string in group
            ]
            os.makedirs(cache_file.parent, exist_ok=True)
            with cache_file.open(mode="wb") as data:
                pickle.dump(strings, data)

            return strings

        with cache_file.open(mode="rb") as data:
            strings = pickle.load(data)

        self.log.debug(f"Loaded strings for plugin {str(plugin_path)!r} from cache.")

        return strings

    def clear_plugin_strings_cache(self):
        """
        Clears Plugin Strings Cache.
        """

        shutil.rmtree(self.path / "plugin_strings", ignore_errors=True)

    def load_plugin_states_cache(self, path: Path):
        self.log.debug(f"Loading Plugin States Cache from {str(path)!r}...")

        with path.open("rb") as file:
            cache: dict[str, utils.Plugin.Status] = pickle.load(file)

        self.__plugin_states_cache = cache

        self.log.debug(
            f"Loaded Plugin States for {len(self.__plugin_states_cache)} Plugin(s)."
        )

    def clear_plugin_states_cache(self):
        """
        Clears Plugin States Cache.
        """

        self.__plugin_states_cache.clear()

    def update_plugin_states_cache(self, modlist: list[utils.Mod]):
        """
        Updates Plugin States Cache from `modlist`.
        """

        plugins = [
            plugin
            for mod in modlist
            for plugin in mod.plugins
            if plugin.status != plugin.Status.NoneStatus
        ]

        cache = {
            utils.get_file_identifier(plugin.path): (
                plugin.tree_item.checkState(0) == qtc.Qt.CheckState.Checked,
                plugin.status,
            )
            for plugin in plugins
        }

        self.__plugin_states_cache = cache

    def get_from_plugin_states_cache(self, plugin_path: Path):
        """
        Returns cached State for `plugin_path` if existing else None.
        """

        return self.__plugin_states_cache.get(utils.get_file_identifier(plugin_path))

    def save_plugin_states_cache(self, path: Path):
        self.log.debug(f"Saving Plugin States Cache to {str(path)!r}...")

        with path.open("wb") as file:
            pickle.dump(self.__plugin_states_cache, file)

        self.log.debug(
            f"Saved Plugin States for {len(self.__plugin_states_cache)} Plugin(s)."
        )

    def save_caches(self):
        """
        Saves non-empty caches.
        """

        self.log.info("Saving caches...")

        os.makedirs(self.path, exist_ok=True)

        if self.__plugin_states_cache:
            plugin_states_cache_path = self.path / "plugin_states.cache"

            self.save_plugin_states_cache(plugin_states_cache_path)

        self.log.info("Caches saved.")
