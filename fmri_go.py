# Scanner presentation script
# Beau Sievers, 4/2014

from psychopy import core, data, visual, event, sound, gui
from psychopy.hardware.emulator import launchScan

import serial
import random
import math

from event import *

win = visual.Window([1280, 720], monitor='testMonitor', screen=0, fullscr=False)

# At DBIC, with Mac OS X, the scanner projector wants to be 1280x1024 and 60Hz
# Use the following line to run this experiment fullscreen on a 2nd monitor:
#win = visual.Window([1280, 1024], monitor='testMonitor', screen=1, fullscr=True)
clock = core.Clock()

loading_message = visual.TextStim(win, pos=[0,0], text="Loading...")
loading_message.draw()
win.flip()

# This global will hold all of the events we will display
# The EventList needs to know about the Window so we can preload the stimuli
events = EventList(win)
events.read_from_file('localizer_1.txt')

if(events.has_overlapping_events()):
    print("WARNING: Overlapping events detected in input")

events.create_null_events()

if(events.has_overlapping_events()):
    print("WARNING: Overlapping events detected after creating null events")
    
# Specify the TR duration
tr_dur = 1.0

# Find the duration of the event list in TRs/volumes
num_vols = math.ceil(float(events.dur()) / tr_dur)

# This is a configuration object for PsychoPy's launchScan
fmri_settings = {
    'TR': tr_dur,        # duration (sec) per volume
    'volumes': num_vols, # number of whole-brain 3D volumes / frames
    'sync': '5',         # character to use as the sync timing event;
    'skip': 0,           # number of vols w/o sync pulse at start of scan
    'sound': False       # play sound in test mode
}

# The experiment starts in sync with the first scanner trigger.
# To test, set mode='Test'
# To scan, set mode='Scan'
vol = launchScan(win, fmri_settings, globalClock=clock, mode='Test')

# Some approaches to waiting for the scanner trigger.

# Swaroop used: tty.USA19H62P1.1
# I have: tty.USA19H142P1.1. Lumina settings: 115200 baud, ASCII.
# It's necessary to install drivers for the KeySpan 19HS

# 1. The Swaroop:
#swaroop_tr = True
#wait_stim = visual.TextStim(win, pos=[0,0], text="Waiting for scanner")
#if(swaroop_tr):
#    # Wait till trigger
#    ser = serial.Serial('/dev/tty.USA19H142P1.1', 115200, timeout = .0001)
#    ser.flushInput()
#    trigger = ''
#    while trigger != fmri_settings['sync']:
#        wait_stim.draw()
#        win.flip()
#        trigger = ser.read()
# Continue your presentation.

# Reset the clock after getting the scanner trigger
clock.reset()

# This script uses "non-slip" timing, presenting stimuli relative to the
# clock time when the first scanner trigger was received. This should ensure
# a minimum of drift without locking the stimuli to each TR.
# http://www.psychopy.org/general/timing/nonSlipTiming.html
end_time = 0            
for event in events.events:
    print event.stim
    end_time += event.dur
    print end_time
    
    if(event.__class__ == MovieEvent):
        # We pass the global clock and the end_time to the MovieEvent to 
        # handle timing. The MovieEvent will cut off the movie early if the
        # movie file is longer than the duration specified in the script file.
        event.display(clock, end_time)
        
        # If a MovieEvent ends earlier than the duration specified in the script
        # file, we display a null event for the remaining time in order to
        # maintain continuity (no blank screens).
        post_movie_null = create_event_for_stim(None, None, events.null_event, win)
        while(clock.getTime() < end_time):
            post_movie_null.display()
    elif(event.__class__ == SoundEvent):
        # SoundEvents also need to know the end_time so the sound can be cut off
        # early if the sound file is too long.
        
        # We also need a null event to draw to the screen while we're playing
        # the sound
        sound_null = create_event_for_stim(None, None, events.null_event, win)
        
        event.display(clock, end_time, sound_null)
    else:    
        while(clock.getTime() < end_time):
            event.display()
