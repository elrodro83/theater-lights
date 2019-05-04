# Author: Rodro (theater-lights@rodronet.com.ar)

import xbmc, xbmcaddon, xbmcgui
import socket

settings = xbmcaddon.Addon(id='script.service.theater-light')
udpPort = int(settings.getSetting("udpPort"))

class MyPlayer(xbmc.Player) :

    def __init__ (self):
        xbmc.Player.__init__(self)

        self.broadcastUDP("<b>theater-lighs<li>config</b>{0:.2f};{1:.2f};{2:.2f};{3:.2f};{4:.2f};{5:.2f}".format(float(settings.getSetting("lightsFullOn")) / 100, float(settings.getSetting("lightsFullOff")) / 100, float(settings.getSetting("lightsTheaterIntro")) / 100, float(settings.getSetting("lightsComingAttractions")) / 100, float(settings.getSetting("lightsPaused")) / 100, float(settings.getSetting("lightsFadeTime"))))

    def broadcastUDP( self, data, ipaddress = settings.getSetting("lightsHost") ):
        IPADDR = ipaddress
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        if hasattr(socket,'SO_BROADCAST'):
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.connect((IPADDR, udpPort))
        s.send(data)
        s.close()

    def onAVStarted(self):
        xbmc.log('My Player - onAVStarted',level=xbmc.LOGDEBUG )
        self.onPlayBackStarted()

    def onPlayBackStarted(self):
        if xbmc.Player().isPlayingVideo():
            VIDEO = 1
            xbmc.log('My Player - <b>playeractions<li>playing</b>',level=xbmc.LOGDEBUG )
            self.broadcastUDP( "<b>playeractions<li>playing</b>" )

    def onPlayBackEnded(self):
        if (VIDEO == 1):
            xbmc.log('My Player - <b>playeractions<li>playback_ended</b>',level=xbmc.LOGDEBUG )
            self.broadcastUDP( "<b>playeractions<li>playback_ended</b>" )

    def onPlayBackStopped(self):
        if (VIDEO == 1):
            xbmc.log('My Player - <b>playeractions<li>playback_stopped</b>',level=xbmc.LOGDEBUG )
            self.broadcastUDP( "<b>playeractions<li>playback_stopped</b>" )

    def onPlayBackPaused(self):
        if xbmc.Player().isPlayingVideo():
            VIDEO = 1
            xbmc.log('My Player - <b>playeractions<li>playback_paused</b>',level=xbmc.LOGDEBUG )
            self.broadcastUDP( "<b>playeractions<li>playback_paused</b>" )

    def onPlayBackResumed(self):
        if xbmc.Player().isPlayingVideo():
            xbmc.log('My Player - <b>playeractions<li>playback_resumed</b>',level=xbmc.LOGDEBUG )
            self.broadcastUDP( "<b>playeractions<li>playback_resumed</b>" )

    def onAVChange(self):
        xbmc.log('My Player - onAVChange',level=xbmc.LOGDEBUG )
        self.onPlayBackStarted()

player=MyPlayer()

VIDEO = 0

while not xbmc.abortRequested:
    if xbmc.Player().isPlaying():
        if xbmc.Player().isPlayingVideo():
            VIDEO = 1
        else:
            VIDEO = 0

    xbmc.sleep(1000)
