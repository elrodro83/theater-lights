#!/usr/bin/env python

# Author: Rodro (theater-lights@rodronet.com.ar)

from threading import Thread
import ConfigParser, sys, signal, select, socket, time, math, logging, logging.handlers
import wiringpi2 as wiringpi

config = ConfigParser.ConfigParser()
config.read('/etc/theater-lights.conf')

rootLogger = logging.getLogger('')
rootLogger.setLevel(config.get('log', 'level'))
rootLogger.addHandler(logging.handlers.RotatingFileHandler(config.get('log', 'file'), maxBytes=20 * 1024, backupCount=5))

targetBrightness = 1.00
def setTargetBrightness(tb):
    global targetBrightness
    rootLogger.info('setTargetBrightness({0})'.format(tb))
    targetBrightness = tb

lastEvent = ""

shutdownFlag=False

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

class TLConfig:
    lightsFullOn = 1.00
    lightsFullOff = 0.00
    lightsTheaterIntro = config.getfloat('lights', 'intensity_theaterIntro')
    lightsComingAttractions = config.getfloat('lights', 'intensity_comingAttractions')
    lightsPaused = config.getfloat('lights', 'intensity_paused')
    
    lightsFadeTime = config.getfloat('lights', 'update_fadeTime')

    def writeConfig(self):
        config.set('lights', 'intensity_theaterIntro', self.lightsTheaterIntro)
        config.set('lights', 'intensity_comingAttractions', self.lightsComingAttractions)
        config.set('lights', 'intensity_paused', self.lightsPaused)
        
        config.set('lights', 'update_fadeTime', self.lightsFadeTime)

        with open('/etc/theater-lights.conf', 'wb') as configfile:
            config.write(configfile)        

tlConfig = TLConfig()
eventPrefix = config.get('xbmc', 'event_prefix')
CONFIG_EVENT = eventPrefix + "<b>theater-lighs<li>config</b>"

class PlayerState:
    global tlConfig

    playing = False
    paused = False
    delayPlay = False
    
    ceha_active = False
    playingLevel = tlConfig.lightsFullOff
    
    def cehaStart(self):
        self.ceha_active = True

    def cehaEnd(self):
        self.setPlayingLevel(tlConfig.lightsFullOff)
        self.ceha_active = False
    
    def play(self):
        self.playing = True
        
        if not self.delayPlay:
            setTargetBrightness(self.playingLevel)
            
    def pause(self):
        self.paused = True
        if not self.playing:
            self.delayPlay = True
        
        if self.playing:
            setTargetBrightness(tlConfig.lightsPaused)
    
    def resume(self):
        self.paused = False
        if self.delayPlay:
            self.delayPlay = False

        setTargetBrightness(self.playingLevel)
    
    def stop(self):
        self.playing = False
        self.paused = False
        self.delayPlay = False
        
        setTargetBrightness(tlConfig.lightsFullOn)
        self.setPlayingLevel(tlConfig.lightsFullOff)
    
    def playbackEnded(self):
        if not self.ceha_active:
            self.stop()
    
    def setPlayingLevel(self, level):
        self.playingLevel = level
        if self.playing and not self.paused and not self.delayPlay:
            setTargetBrightness(self.playingLevel)

playerState = PlayerState()

def pollForData():

    global lastEvent

    port = config.getint('xbmc', 'udp_port')  # where do you expect to get a msg?
    bufferSize = 256 # whatever you need

    s.bind(('', port))
    s.setblocking(0)
    rootLogger.info("UDP port binded!")

    while not shutdownFlag:
        result = select.select([s],[],[], 2)
        if result[0]:
            lastEvent = result[0][0].recv(bufferSize)
            lastEvent = lastEvent
            rootLogger.info("Event received: " + lastEvent)
            if lastEvent.startswith(CONFIG_EVENT):
                values = lastEvent[len(CONFIG_EVENT):].split(';')
 
                tlConfig.lightsFullOn = float(values[0])
                tlConfig.lightsFullOff = float(values[1])
                tlConfig.lightsTheaterIntro = float(values[2])
                tlConfig.lightsComingAttractions = float(values[3])
                tlConfig.lightsPaused = float(values[4])
                 
                tlConfig.lightsFadeTime = float(values[5])
                
                tlConfig.writeConfig()
            elif lastEvent == eventPrefix + "<b>CE_Automate<li>script_start</b>":
                playerState.cehaStart()
            elif lastEvent == eventPrefix + "<b>playeractions<li>playback_stopped</b>":
                playerState.stop()
                playerState.cehaEnd()
            elif lastEvent == eventPrefix + "<b>playeractions<li>playback_ended</b>":
                playerState.playbackEnded()
            elif lastEvent == eventPrefix + "<b>CE_Automate<li>script_end</b>":
                playerState.stop()
                playerState.cehaEnd()
            elif lastEvent == eventPrefix + "<b>CE_Automate<li>trivia_intro</b>":
                playerState.setPlayingLevel(tlConfig.lightsFullOn)
            elif lastEvent == eventPrefix + "<b>CE_Automate<li>trivia_start</b>":
                pass
            elif lastEvent == eventPrefix + "<b>CE_Automate<li>trivia_outro</b>":
                pass
            elif lastEvent == eventPrefix + "<b>CE_Automate<li>movie_theatre_intro</b>":
                playerState.setPlayingLevel(tlConfig.lightsTheaterIntro)
            elif lastEvent == eventPrefix + "<b>CE_Automate<li>coming_attractions_intro</b>":
                playerState.setPlayingLevel(tlConfig.lightsComingAttractions)
            elif lastEvent == eventPrefix + "<b>CE_Automate<li>trailer</b>":
                playerState.setPlayingLevel(tlConfig.lightsComingAttractions)
            elif lastEvent == eventPrefix + "<b>CE_Automate<li>coming_attractions_outro</b>":
                pass
            elif lastEvent == eventPrefix + "<b>CE_Automate<li>feature_intro</b>":
                pass
            elif lastEvent == eventPrefix + "<b>CE_Automate<li>countdown_video</b>":
                pass
            elif lastEvent == eventPrefix + "<b>CE_Automate<li>audio_video</b>":
                pass
            elif lastEvent == eventPrefix + "<b>CE_Automate<li>mpaa_rating</b>":
                playerState.setPlayingLevel(tlConfig.lightsFullOff)
            elif lastEvent == eventPrefix + "<b>CE_Automate<li>movie_start</b>":
                playerState.setPlayingLevel(tlConfig.lightsFullOff)
            elif lastEvent == eventPrefix + "<b>playeractions<li>playing</b>":
                playerState.play()
            elif lastEvent == eventPrefix + "<b>CE_Automate<li>intermission</b>":
                playerState.setPlayingLevel(tlConfig.lightsTheaterIntro)
            elif lastEvent == eventPrefix + "<b>CE_Automate<li>feature_outro</b>":
                pass
            elif lastEvent == eventPrefix + "<b>CE_Automate<li>movie_theatre_outro</b>":
                playerState.stop()
                playerState.cehaEnd()
#            elif lastEvent == eventPrefix + "<b>CE_Automate<li>paused</b>" or 
            elif lastEvent == eventPrefix + "<b>playeractions<li>playback_paused</b>":
                playerState.pause()
#            elif lastEvent == eventPrefix + "<b>CE_Automate<li>resumed</b>" or 
            elif lastEvent == eventPrefix + "<b>playeractions<li>playback_resumed</b>":
                playerState.resume()
            else:
                rootLogger.warn("Event not recognized: " + lastEvent)

PWM_FREQ = config.getfloat('lights', 'pwm_freq')

TL_PWM = 1 # gpio pin 12 = wiringpi no. 1 (BCM 18)

# Initialize PWM output for theater lights
wiringpi.wiringPiSetup()
wiringpi.pwmSetMode(0) # PWM_MODE_MS
wiringpi.pwmSetClock(math.trunc(18750 / PWM_FREQ))
wiringpi.pinMode(TL_PWM, 2)     # PWM mode
wiringpi.pwmWrite(TL_PWM, 0)    # OFF

def updateLights():
    global tlConfig
    STEP_INTERVAL = 1 / PWM_FREQ # how often
    STEP_BRIGHTNESS = 1 / (tlConfig.lightsFadeTime * PWM_FREQ) # how much
    
    currentBrightness = 1.00

    while not shutdownFlag:
        changed = False
        if abs(currentBrightness - targetBrightness) > STEP_BRIGHTNESS / 2:
            if currentBrightness < targetBrightness:
                currentBrightness += STEP_BRIGHTNESS
                changed = True
            elif currentBrightness > targetBrightness:
                currentBrightness -= STEP_BRIGHTNESS
                changed = True

        if changed:
            wiringpi.pwmWrite(TL_PWM, math.trunc(1024 * (1.00 - currentBrightness)))
            rootLogger.debug("{0:.2f} <- {1} <- {2:.2f}".format(currentBrightness, lastEvent, targetBrightness))
        time.sleep(STEP_INTERVAL)

thUpdateLights = Thread(target=updateLights)
thPollForData = Thread(target=pollForData)

def cleanUp(signal, frame):
    global shutdownFlag
    rootLogger.info("Received signal {0}. Exiting...".format(signal))

    shutdownFlag = True
    thUpdateLights.join()
    thPollForData.join()
    rootLogger.info("Threads joined!")

    s.close()
    rootLogger.info("UDP socket closed!")
    
    sys.exit()

rootLogger.info("Starting threads...")

thUpdateLights.start()
rootLogger.info("updateLights thread started!")

thPollForData.start()
rootLogger.info("pollForData thread started!")

signal.signal(signal.SIGTERM, cleanUp)
signal.signal(signal.SIGINT, cleanUp)

while True:
    time.sleep(1000)
