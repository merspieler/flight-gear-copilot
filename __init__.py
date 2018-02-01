import sys
import re
import json
from telnetlib import Telnet

from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler
from mycroft.skills.core import MycroftSkill
from mycroft.util.log import getLogger

LOGGER = getLogger(__name__)

class FlightGearCopilotSkill(MycroftSkill):
	def __init__(self):
		super(FlightGearCopilotSkill, self).__init__()

# DEFINITION of the settings['profiles'] structure
# [
#	{
#		"name": "<profile-name>",
#		"acid":
#		[
#			"<Aircraft-id> can be found in /???",
#			...
#		],
#		flaps:
#		[
#			{
#				"id": "<flaps-name> can be up|down|full|number",
#				"min-spd": "<minimum speed for save retraction>",
#				"max-spd": "<maximum speed for save extention>",
#				"value": "<value in the prop tree>"
#			},
#			...
#		]
#		"flaps-path": "<path to current flaps-position>"
#		"gear-retractable": "<true|false>"
#	},
#	...
# ]

# might be useful
# make_active()

#########################
#			#
#	Flaps		#
#			#
#########################

	@intent_handler(IntentBuilder('FlapsIntent').require('flaps'))
	def handle_flaps_intent(self, message):
		flaps_request = message.data['utterance']
		if flaps_request == "flaps":
			self.speak_dialog("no.setting")
			sys.exit(0)

		# extracting the flaps setting from the utterance
		match = re.match(r'.*flaps.* (up|full|down|\d{1,2}).*', flaps_request, re.I)
		if match == None:
			self.speak_dialog("no.valid.flaps")
			sys.exit(0)

		flaps_request = match.group(1)

		try:
			tn = Telnet(self.settings['host'], self.settings['port'])
		except:
			self.speak_dialog("no.telnet.con")
			sys.exit(0)

		tn.write("data\r\n")

		# DEMO DATA
		flaps = 2
		# END DEMO DATA

		# get acid
		tn.write("get /sim/aircraft")
		acid = tn.read_until("\n")

		profile = None
		for i_profiles in self.settings['profiles']:
			for i_acid in i_profiles['acid']:
				if i_acid == acid:
					profile = i_profiles
					break
			if profile != None:
				break

		if profile == None:
			# TODO when creation of profiles via voice is possible, add dialog how to
			self.speak("Profile not found")
			sys.exit(0)

		tn.write("get /velocities/airspeed-kt\r\n")
		kias = float(tn.read_until("\n"))

		# TODO read flaps

		o_flaps = None

		# find the flaps value for the flaps id
		for i_flaps in profile['flaps']:
			if str(i_flaps['id']) == str(flaps_request):
				o_flaps = i_flaps
				break

		if o_flaps == None:
			self.speak_dialog("flaps.setting.unknown")
			sys.exit(0)

		# check if extend or retract flaps
		# TODO add handling up|down|full is already set
		if str(flaps_request) == "down" or str(flaps_request) == "full":
			flaps_mov = "extend"
		elif str(flaps_request) == "up":
			flaps_mov = "retract"
		else:
			if int(flaps_request) > o_flaps:
				flaps_mov = "extend"
			elif int(flaps_request) < o_flaps:
				flaps_mov = "retract"
			else:
				self.speak_dialog("keep.flaps")
				sys.exit(0)

		# check if speed is high/low enough for retraction/extention
		if flaps_mov == "extend":
			if o_flaps['max-spd'] < kias:
				self.speak_dialog("spd.high")
				sys.exit(0)
		else:
			if o_flaps['min-spd'] > kias:
				self.speak_dialog("spd.low")
				sys.exit(0)

		# TODO set flaps in fg

		self.speak("Speed checked. Flaps " + str(flaps_request))


#########################
#			#
#	Gear		#
#			#
#########################

	@intent_handler(IntentBuilder('GearIntent').require('gear'))
	def handle_gear_intent(self, message):
		gear_request = message.data['utterance']
		if gear_request == "gear":
			self.speak_dialog("no.gear.action")
			sys.exit(0)

		match = re.match(r'.*gear.* (up|down|) +.*|.*(retract|extend) .*gear.*', gear_request, re.i)

		self.speak("Gear " + str(gear_request))

	def stop(self):
		pass

def create_skill():
	return FlightGearCopilotSkill()
