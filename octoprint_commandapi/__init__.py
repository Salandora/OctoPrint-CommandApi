# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
try:
	from octoprint_automaticonoff import State
	from octoprint_automaticonoff.api import SwitchOnOffApiPlugin
	_disable = False
except ImportError:
	_disable = True
	class SwitchOnOffApiPlugin(object):
		pass


class CommandApiPlugin(SwitchOnOffApiPlugin,
                       octoprint.plugin.SettingsPlugin,
                       octoprint.plugin.TemplatePlugin):
	def __init__(self):
		self._initialized = False

	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(
			init_command = "",
			on_command = "",
			off_command = "",
			read_command = "",
			invert_reading = False
		)
		
	def get_template_configs(self):
		return [
			dict(type="settings", custom_bindings=False),
		]

	##~~ Softwareupdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		return dict(
			commandapi=dict(
				displayName="Commandapi Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="Salandora",
				repo="OctoPrint-CommandApi",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/Salandora/OctoPrint-CommandApi/archive/{target_version}.zip"
			)
		)
		
	def setup_gpio(self):
		command = self._settings.get(["init_command"])
		if command is "":
			return

		try:
			import sarge
			sarge.run(command)
			self._initialized = True
		except:
			self._logger.exception("{} failed".format(" ".join(command)))
	
	def set_power(self, enable):
		if not self._initialized:
			self.setup_gpio()
			if not self._initialized:
				return
		
		command = ""
		if enable:
			self._logger.info("Enabling power supply")
			command = self._settings.get(["on_command"])
		else:
			self._logger.info("Disabling power supply")
			command = self._settings.get(["off_command"])

		if command is "":
			return

		try:
			import sarge
			sarge.run(command)
		except:
			self._logger.exception("{} failed".format(" ".join(command)))
			
	def get_power(self):
		if not self._initialized:
			self.setup_gpio()
			if not self._initialized:
				return
			
		command = self._settings.get(["read_command"])
		if command is "":
			return State.Unknown

		try:
			import sarge
			output = sarge.get_stdout(command)
		except:
			self._logger.exception("{} failed".format(" ".join(command)))
		else:
			if output.strip() == "0":
				return State.OFF if not self._settings.get_boolean(["invert_reading"]) else State.ON
			elif output.strip() == "1":
				return State.ON if not self._settings.get_boolean(["invert_reading"]) else State.OFF 

		return State.UNKNOWN


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.

__plugin_name__ = "CommandApi"

def __plugin_load__():
	if _disable:
		return
	
	global __plugin_implementation__
	__plugin_implementation__ = CommandApiPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}

