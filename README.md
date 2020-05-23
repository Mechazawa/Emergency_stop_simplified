# Emergency stop simplified

This plugin reacts to a switch or button, if triggered (switch open or closed, based on configuration) it issues **M112** command to printer.

Let's check some features:
* info pop-up when plugin hasn't been configured
* user-friendly and easy to configure
* runs on OctoPrint 1.3.0 and higher

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/Mechazawa/Emergency_stop_simplified

## Configuration

Configuration couldn't be simpler, all you need is to configure listening board pin (board mode) and if the second switch terminal is connected to ground or 3.3V.

Default pin is -1 (not configured) and ground (as it is safer, read below).

**WARNING! Never connect the switch input to 5V as it could fry the GPIO section of your Raspberry!**

#### Advice

You might experience the same problem as I experienced - the button was randomly triggered. Turns out that if running button wires along motor wires, it was enough to interfere with button reading.

To solve this connect a shielded wire to your button and ground the shielding, ideally on both ends.

If you are unsure about your button being triggered, check [OctoPrint logs](https://community.octoprint.org/t/where-can-i-find-octoprints-and-octopis-log-files/299)
