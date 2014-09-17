# Scanner presentation script
# Beau Sievers, 4/2014

#from psychopy import core, data, visual, event, sound, gui

from psychopy.hardware.emulator import launchScan
import psychopy as psy

import serial
import random 
import math
import multiprocessing
import time

from event import *

# This is a configuration object for PsychoPy's LaunchScan
# that determines what the scanner trigger value should be  
fmri_settings = {
    'TR': 1.0,           # duration (sec) per volume
    'volumes': None,     # number of whole-brain 3D volumes / frames
    'sync': '5',         # character to use as the sync timing event;
    'skip': 0,           # number of vols w/o sync pulse at start of scan
    'sound': False       # play sound in test mode
}

# This is how the scanner trigger works in the DBIC:
# Swaroop used: tty.USA19H62P1.1
# I have: tty.USA19H142P1.1. Lumina settings: 115200 baud, ASCII.
# Parag observed a changing mount point in /dev, so if this doesn't work
# just take a look and see what's there.
# It's necessary to install drivers for the KeySpan 19HS or whatever 
# serial-to-USB converter is in use.
serial_settings = {
    'mount': '/dev/tty.USA19H142P1.1',
    'baud': 115200,
    'timeout': .0001
}

# This function is used in a multiprocess-based "thread." 
# Calling PyGame-based functions in the "thread" causes problems, so this is
# a little baroque.
# t0 is the start time. 
def log_serial_input(filename, t0):
    global serial_settings
    print("Running capture_log_input with location {0}".format(location))
    ser = serial.Serial(serial_settings['mount'], serial_settings['baud'], timeout = serial_settings['timeout'])
    ser.flushInput()

    with open(filename, 'a') as logfile:
        logfile.write("time,input\n")
    # This while(True) construction should give any reasonable person pause,
    # because it could create zombie processes. This function is explicitly
    # flagged as a logging daemon. But maybe there's a better way, so we don't
    # need to terminate later? I.e., the "poison pill" method.
    while(True):
        char = ser.read()
        if(char):
            with open(filename, 'a') as logfile:
                t_now = time.time() - t0
                logfile.write("{0},{1}".format(t_now, char))

# This function is designed for testing logging during simulation mode. Actual
# logging should use the log_serial_input function above. During simulations,
# the pressed keys are dumped from psychopy.event.getKeys() between each event
# presentation, so log timings will not be accurate. This includes TR 5s from
# the PsychoPy scanner simulator; they all are logged in clumps between events.
# The only way to avoid this would be to call a function to dump getKeys() 
# between every flip() but this would require extensive restructuring and isn't
# necessary for testing during simulations right now.
def log_keyboard_input(filename, t0, shared_keys):
    with open(filename, 'a') as logfile:
        logfile.write("time,input\n")
    while(True):
        if(len(shared_keys) > 0):
            for index in range(len(shared_keys)):
                key = shared_keys.pop()
                with open(filename, 'a') as logfile:
                    t_now = time.time() - t0
                    logfile.write("{0},{1}\n".format(t_now, key))    

def run_experiment():
    global serial_settings
    global fmri_settings
    win = psy.visual.Window([1280, 720], monitor='testMonitor', screen=0, fullscr=False)
    #, winType="pyglet")

    # At DBIC, with Mac OS X, the scanner projector wants to be 1280x1024 and 60Hz
    # Use the following line to run this experiment fullscreen on a 2nd monitor:
    #win = visual.Window([1280, 1024], monitor='testMonitor', screen=1, fullscr=True)
    clock = psy.core.Clock()

    loading_message = psy.visual.TextStim(win, pos=[0,0], text="Loading...")
    loading_message.draw()
    win.flip()

    # This global will hold all of the events we will display
    # The EventList needs to know about the Window so we can preload the stimuli
    events = EventList(win)
    events.read_from_file('test_scripts/clean_run_1.txt')

    if(events.has_overlapping_events()):
        print("WARNING: Overlapping events detected in input")

    events.create_null_events()

    if(events.has_overlapping_events()):
        print("WARNING: Overlapping events detected after creating null events")
    
    # Specify the TR duration
    tr_dur = fmri_settings['TR']
    
    # Find the duration of the event list in TRs/volumes
    fmri_settings['volumes'] = math.ceil(float(events.dur()) / tr_dur)
    
    # Specify our location
    # (For now this just controls how we handle receipt of the _first_ 
    #  trigger, but in the future it should control how we handle all 
    #  scanner triggers.)
    location = "simulation"
    #location = "dbic"

    if(location == "simulation"):
        # The experiment starts in sync with the first scanner trigger.
        # To test, set mode='Test'
        # To scan, set mode='Scan'
        vol = launchScan(win, fmri_settings, globalClock=clock, mode='Test')
    
    elif(location == "dbic"):
        wait_stim = psy.visual.TextStim(win, pos=[0,0], text="Waiting for scanner")
        # Wait till trigger
        ser = serial.Serial(serial_settings['mount'], serial_settings['baud'], timeout = serial_settings['timeout'])
        ser.flushInput()
        trigger = ''
        while trigger != fmri_settings['sync']:
            wait_stim.draw()
            win.flip()
            trigger = ser.read()
        # We close this serial object now because
        # further serial input will be read by a different process
        ser.close()
        
    t0 = time.time()

    mgr = multiprocessing.Manager()
    shared_keys = mgr.list()

    # Spawn a second process to do TR and input logging
    if(location == "dbic"):
        log_filename = 'multiproc_ser_log.txt'
        log_proc = multiprocessing.Process(target=log_serial_input, args=(log_filename, t0))
    elif(location == "simulation"):
        log_filename = 'multiproc_key_log.txt'
        log_proc = multiprocessing.Process(target=log_keyboard_input, args=(log_filename, t0, shared_keys))
    log_proc.daemon = True
    log_proc.start()

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
            post_movie_null = create_event_for_stim([None, None, events.null_event], win)
            while(clock.getTime() < end_time):
                post_movie_null.display()
                
        elif(event.__class__ == SoundEvent):
            # SoundEvents also need to know the end_time so the sound can be cut off
            # early if the sound file is too long.
        
            # We also need a null event to draw to the screen while we're playing
            # the sound
            sound_null = create_event_for_stim([None, None, events.null_event], win)
        
            event.display(clock, end_time, sound_null)
        else:    
            while(clock.getTime() < end_time):
                event.display()
        
        # Move all the keys pressed during the event to shared_keys only _after_
        # the event is over.
        now_keys = psy.event.getKeys()
        if(len(now_keys) > 0):
            shared_keys += now_keys
        
        # If 'q' was pressed during an event, terminate the experiment after 
        # that event ends.
        if('q' in now_keys):
            log_proc.terminate()
            print("Quit experiment because 'q' was pressed.")
            with open(log_filename, 'a') as logfile:
                logfile.write("--- Quit experiment because 'q' was pressed. ---")
            win.close()
            psy.core.quit()
    
    log_proc.terminate()    # Terminate the log process when we get to the end

if __name__ == '__main__':
    run_experiment()
