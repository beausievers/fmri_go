from psychopy import core, data, visual, event, sound, gui
import random
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

if(events.has_overlapping_events):
    print("WARNING: Overlapping events detected in input")

events.create_null_events()

if(events.has_overlapping_events):
    print("WARNING: Overlapping events detected after creating null events")

# http://www.psychopy.org/general/timing/nonSlipTiming.html
end_time = 0            
for event in events.events:
    print event.stim
    end_time += event.dur
    print end_time
    while clock.getTime() < end_time:
        display_text(event.stim, win)
