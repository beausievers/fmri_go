# Scanner presentation script
# Beau Sievers, 4/2014

from psychopy import core, data, visual, event, sound, gui
from psychopy.hardware.emulator import launchScan

import random
import math

from event import *

win = visual.Window([800, 600], monitor='testMonitor')
clock = core.Clock()

def display_text(t, win):
    stimulus = visual.TextStim(win, pos=[0,0], text=t)
    stimulus.draw()
    win.flip()

# This global will hold all of the events we will display
events = EventList()
events.read_from_file('script.txt')

if(events.has_overlapping_events()):
    print("WARNING: Overlapping events detected in input")

events.create_null_events()

if(events.has_overlapping_events()):
    print("WARNING: Overlapping events detected after creating null events")
    
# Specify the TR duration
tr_dur = 2.0

# Find the duration of the event list in volumes
num_vols = math.ceil(events.dur() / tr_dur)

# This is a configuration object for PsychoPy's launchScan
fmri_settings = {
    'TR': tr_dur,        # duration (sec) per volume
    'volumes': num_vols, # number of whole-brain 3D volumes / frames
    'sync': '5',         # character to use as the sync timing event;
    'skip': 0,           # number of vols w/o sync pulse at start of scan
    'sound': False       # play sound in test mode
}

# This should set it up so the experiment starts in sync with the first 
# scanner trigger
vol = launchScan(win, fmri_settings, globalClock=clock, mode='Test')

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
        event.display(win, clock, end_time)
        
        # If a MovieEvent ends earlier than the duration specified in the script
        # file, we display a null event for the remaining time in order to
        # maintain continuity (no blank screens).
        post_movie_null = create_event_for_stim(None, None, events.null_event)
        while(clock.getTime() < end_time):
            post_movie_null.display(win)
            
    else:    
        while(clock.getTime() < end_time):
            event.display(win)
