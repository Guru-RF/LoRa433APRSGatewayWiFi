# Base config for both iGates and Gateways

# I use papertrail but other services are available
syslogHost = "logs4.papertrailapp.com"
syslogPort = 24262
# APRS
call = "ON6URE-5"
aprs_host = "belgium.aprs2.net"
aprs_port = 14580
passcode = "23996"  # https://apps.magicbug.co.uk/passcode/index.php/passcode
latitude = 51.1517227
longitude = 2.7649157
altitude = 46  # in meters
comment = "https://rf.guru"
# Gateway symbol
symbol = "L&"
# iGate symbol
# symbol = "R&"
# Features
biast = False


# Gateway only
msgDistance = 300  # distance in km's from source of messages
# ignore messages from these callsigns
filtersrc = ["F4IED-12", "LX1CU-13", "F8KSM-3"]
# if enabled only allow filterdst prefixes
allowdst = True
# only broadcast messages with calls starting with these callsign prefixes
filterdst = ["ON"]
