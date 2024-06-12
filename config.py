# Base config for both iGates and Gateways

# We use papertrail, it logs unrecoverable errors so we can fix them in future updates
syslogHost = "logs4.papertrailapp.com"
syslogPort = 24262
# APRS
call = ""
aprs_host = "belgium.aprs2.net"
aprs_port = 14580
passcode = ""  # https://apps.magicbug.co.uk/passcode/
latitude = 52.1517227
longitude = 3.7649157
altitude = 46  # in meters
comment = "https://rf.guru"
# Gateway symbol
symbol = "L&"
# iGate symbol
# symbol = "R&"
# Features
biast = False
paDelay = 0  # in seconds


# Gateway only
msgDistance = 300  # distance in km's from source of messages
# ignore messages from these callsigns
filtersrc = ["F4IED-12", "LX1CU-13", "F8KSM-3"]
# if enabled only allow filterdst prefixes
allowdst = True
# only broadcast messages with calls starting with these callsign prefixes
filterdst = ["ON"]
