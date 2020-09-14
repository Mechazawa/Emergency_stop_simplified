# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import re
from octoprint.events import Events
from time import sleep
import RPi.GPIO as GPIO


class Emergency_stop_simplifiedPlugin(octoprint.plugin.StartupPlugin,
                                       octoprint.plugin.EventHandlerPlugin,
                                       octoprint.plugin.TemplatePlugin,
                                       octoprint.plugin.SettingsPlugin,
                                       octoprint.plugin.AssetPlugin):

    def initialize(self):
        GPIO.setwarnings(False)  # Disable GPIO warnings
        self.send_gcode = False
        self.pin_initialized = False

    @property
    def pin(self):
        return int(self._settings.get(["pin"]))

    @property
    def switch(self):
        return int(self._settings.get(["switch"]))

    @property
    def action(self):
        return int(self._settings.get(["action"]))

    # AssetPlugin hook
    def get_assets(self):
        return dict(js=["js/emergencystopsimplified.js"], css=["css/emergencystopsimplified.css"])

    # Template hooks
    def get_template_configs(self):
        return [dict(type="settings", custom_bindings=False)]

    # Settings hook
    def get_settings_defaults(self):
        return dict(
            pin=-1,  # Default is -1
            switch=0,
            action=0
        )

    def on_after_startup(self):
        self._logger.info("Emergency Stop Simplified started")
        self._setup_button()

    def on_settings_save(self, data):
        if self.sensor_enabled() and self.pin_initialized:
            GPIO.remove_event_detect(self.pin)
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self._setup_button()

    def _setup_button(self):
        if self.sensor_enabled():
            self._logger.info("Setting up button.")
            self._logger.info("Using BCM Mode")
            GPIO.setmode(GPIO.BCM)
            self._logger.info("Emergency Stop button active on GPIO Pin [%s]" % self.pin)
            if self.switch is 0:
                GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            else:
                GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

            GPIO.remove_event_detect(self.pin)
            GPIO.add_event_detect(
                self.pin, GPIO.BOTH,
                callback=self.button_callback,
                bouncetime=100
            )
            self.pin_initialized = True
        else:
            self._logger.info("Pin not configured, won't work unless configured!")

    def sending_gcode(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
        if self.send_gcode:
            self.send_M112()

    def sensor_enabled(self):
        return self.pin != -1

    def on_event(self, event, payload):
        if event is Events.DISCONNECTED:
            self.send_gcode = False

        if not self.sensor_enabled():
            if event is Events.USER_LOGGED_IN:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="info", autoClose=True, msg="Don't forget to configure this plugin."))
            elif event is Events.PRINT_STARTED:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="info", autoClose=True, msg="You may have forgotten to configure this plugin."))

    def button_callback(self, _):
        self._logger.info("Emergency stop button was triggered")

        state = self._printer.get_state_id()

        if self.pin_initialized and self.sensor_enabled() and \
           GPIO.input(self.pin) != self.switch and state in ['PRINTING', 'PAUSED']:
            if self.action == 0:
                self.send_gcode = True
                self.send_M112()
            elif self.action == 1:
                self._logger.info("Cancelling print")
                self._printer.cancel_print()

    def send_M112(self):
        self._logger.info("Sending emergency stop GCODE M112")
        self._printer.commands("M112")


    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return dict(
            filamentsensorsimplified=dict(
                displayName="Emergency stop simplified",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="Mechazawa",
                repo="Emergency_stop_simplified",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/Mechazawa/Emergency_stop_simplified/archive/{target_version}.zip"
            )
        )

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
# __plugin_pythoncompat__ = ">=2.7,<3" # only python 2
# __plugin_pythoncompat__ = ">=3,<4" # only python 3
__plugin_pythoncompat__ = ">=2.7,<4"  # python 2 and 3

__plugin_name__ = "Emergency Stop Simplified"
__plugin_version__ = "0.1.1"

def __plugin_check__():
    try:
        import RPi.GPIO as GPIO
        if GPIO.VERSION < "0.6":  # Need at least 0.6 for edge detection
            return False
    except ImportError:
        return False
    return True

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = Emergency_stop_simplifiedPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.sending": __plugin_implementation__.sending_gcode
    }
