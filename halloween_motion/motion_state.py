from enum import Enum
from gpiozero import LED, MotionSensor
import time
from pydub import AudioSegment
from pydub.playback import play
import random

class States(Enum):
    WaitForMotion = 1
    PlaySong = 2
    Pause = 3

class State:
    def handleMotionDetection(self):
        pass

    def handleSongPlayback(self):
        pass

    def handlePause(self): 
        pass

class WaitForMotionState(State):
    def __init__(self, context):
        self.context = context
        self.pir = MotionSensor(4, queue_len=10, threshold=0.7)
        self.led = LED(16)

    def handleMotionDetection(self):
        print('Waiting for motion')
        self.led.on()
        self.pir.wait_for_motion()
        self.led.off()
        self.context.setState(States.PlaySong)

    def handleSongPlayback(self):
        print('This state dones not song playback')

    def handlePause(self): 
        print('This state dones not pausing')

class PlaySongState(State):
    def __init__(self, context):
        self.context = context
        self.led = LED(17)
        self.halloween = AudioSegment.from_mp3('./audio/halloween_theme.mp3')
        self.letmeout = AudioSegment.from_mp3('./audio/LetMeOut.mp3')
        self.help = AudioSegment.from_mp3('./audio/help.mp3')
        self.candy = AudioSegment.from_mp3('./audio/candy.mp3')

        self.audio_options = [self.halloween, self.letmeout, self.candy, self.help]
        
    def handleMotionDetection(self):
        print('This state dones not handle motion')

    def handleSongPlayback(self):
        print('Playing audio')
        self.led.on()
        play(random.choice(self.audio_options))
        self.led.off()
        #Play until song completes
        self.context.setState(States.Pause)

    def handlePause(self): 
        print('This state dones not pausing')

class PauseState(State):
    def __init__(self, context):
        self.context = context

    def handleMotionDetection(self):
        print('This state dones not handle motion') 

    def handleSongPlayback(self):
        print('This state dones not song playback')

    def handlePause(self): 
        print('Waiting to transition back to the start')
        time.sleep(10)
        self.context.setState(States.WaitForMotion)


class Context:
    def __init__(self):
        self.wait_for_motion = WaitForMotionState(self)
        self.play_song = PlaySongState(self)
        self.pause = PauseState(self)
        self.state = self.wait_for_motion

    def setState(self,state):
        if not isinstance(state, States):
            raise TypeError('state must be an instance of States Enum')

        self.state = {
            States.WaitForMotion: self.wait_for_motion,
            States.PlaySong: self.play_song,
            States.Pause: self.pause
        }.get(state)

    def getState(self):
        return self.state

    def handleMotionDetection(self):
        self.state.handleMotionDetection()

    def handleSongPlayback(self):
        self.state.handleSongPlayback()

    def handlePause(self): 
        self.state.handlePause()


if __name__ == '__main__':
    print("Initializing state machine...")
    context = Context()
    while True:
        context.handleMotionDetection()
        context.handleSongPlayback()
        context.handlePause()
