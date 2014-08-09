# Author: Rodro (theater-lights@rodronet.com.ar)

import xbmcvfs

xbmcvfs.rename('special://home/userdata/addon_data/script.cinema.experience/ha_scripts/home_automation.py', 'special://home/userdata/addon_data/script.cinema.experience/ha_scripts/home_automation.py.old')        
xbmcvfs.copy('special://home/addons/script.service.theater-light/resources/home_automation.py', 'special://home/userdata/addon_data/script.cinema.experience/ha_scripts/home_automation.py')
