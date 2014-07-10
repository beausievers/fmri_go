from psychopy import core, data, visual, event, sound, gui
import os
import decimal

def create_event_for_stim(event_strings, win):    
    if(event_strings[0] != None):
        event_start = decimal.Decimal(event_strings[0])
    else:
        event_start = None
    
    if(event_strings[1] != None):
        event_dur = decimal.Decimal(event_strings[1])
    else:
        event_dur = None
        
    stim_strings = event_strings[2:]
    
    # Are we dealing with a text stim or a file stim?
    # If the stim begins and ends with double quotes, then it's text.
    if((stim_strings[0][0] == '"') and (stim_strings[0][-1] == '"')):
        # If the following field begins with a hash, then it's colored text
        if(len(stim_strings) == 2 and stim_strings[1][0]=='#'):
            text_color = stim_strings[1]
        else:
            text_color = '#FFFFFF'
        new_event = TextEvent(
            event_start, event_dur, 
            stim_strings[0][1:-1], # Strip the quotes 
            win,
            text_color
        )
    # If we do not begin and end with quotes, then we assume we are dealing
    # with a file stim (this if/elif structure is inelegant).
    elif((stim_strings[0][0] != '"') and (stim_strings[0][-1] != '"')):
        filename, stim_ext = os.path.splitext(stim_strings[0])
        if(stim_ext in ['.mp4', '.mov']):
            new_event = MovieEvent(
                event_start, event_dur, stim_strings[0], win
            )
        elif(stim_ext in ['.jpg', '.jpeg', '.tif']):
            new_event = ImageEvent(
                event_start, event_dur, stim_strings[0], win
            )
        elif(stim_ext in ['.wav', '.aif']):
            new_event = SoundEvent(
                event_start, event_dur, stim_strings[0], win
            )
        else:
            print("stim_ext not found: {0}".format(stim_ext))
            print("stim_strings: {0}".format(stim_strings))
    else:
        print("Confusing stim_strings: {0}".format(stim_strings))
    return(new_event)

class Event(object):
    def __init__(self, start, dur, stim_str, win):
        self.start = start
        self.dur = dur
        self.stim_str = stim_str
        self.win = win
        
class TextEvent(Event):
    def __init__(self, start, dur, stim_str, win, text_color='#FFFFFF'):
        super(TextEvent, self).__init__(start, dur, stim_str, win)
        self.stim = visual.TextStim(win, pos=[0,0], text=self.stim_str, 
                                    color=text_color, wrapWidth=2)
    
    def display(self):
        self.stim.draw()
        self.win.flip()
        
class ImageEvent(Event):
    def __init__(self, start, dur, stim_str, win):
        super(ImageEvent, self).__init__(start, dur, stim_str, win)
        self.stim = visual.ImageStim(self.win, pos=[0,0], image=self.stim_str)
    
    def display(self):
        self.stim.draw()
        self.win.flip()
        
# As with movies, PsychoPy depends on avbin for media decoding, and it likes
# some audio files better than others. Certain AIFF files don't work.

class SoundEvent(Event):
    def __init__(self, start, dur, stim_str, win):
        super(SoundEvent, self).__init__(start, dur, stim_str, win)
        self.stim = sound.Sound(stim_str)
        
    def display(self, clock, end_time, on_screen):
        self.stim.play()
        while(clock.getTime() < end_time):
            on_screen.display()
        self.stim.stop()
        
# Note: If a single movie is loaded multiple times in a script, multiple
# MovieEvent objects will be created, each occupying their own memory location.
# This could possibly get expensive. Consider releasing the objects after use?
# Consider reusing objects for events that are loaded multiple times?

# Note: PsychoPy depends on avbin for media decoding, and avbin likes some
# movies and not others. I experienced crashing when playing movies with empty
# audio tracks. Also experienced crashing when playing movies with certain
# codec/wrapper combinations. It took some trial and error to get things 
# working smoothly.

# TODO: Figure out exactly what's going on with the horizontal flipping.
class MovieEvent(Event):
    def __init__(self, start, dur, stim_str, win):
        super(MovieEvent, self).__init__(start, dur, stim_str, win)
        self.stim = visual.MovieStim(self.win, self.stim_str,
                                    flipVert=False, flipHoriz=True, loop=False)
        
    def display(self, clock, end_time):
        # Terminate and hand control back to fmri_go.py if either the movie ends
        # or we run out of time on the global clock.
        while((self.stim.status != visual.FINISHED) and (clock.getTime() < end_time)):
            self.stim.draw()
            self.win.flip()

class EventList:
    def __init__(self, win):
        self.events = []
        self.null_event = None
        self.win = win
        
    def read_from_file(self, path):
        # Parse the script file and populate the global event array
        lines = [line.strip() for line in open(path)]
        for line in lines:
            splitline = line.split(',')
            if(splitline[0] == "NULL"):
                self.null_event = splitline[1]
            else:
                new_event = create_event_for_stim(splitline, self.win)
                self.events.append(new_event)
                                        
                # Should guarantee that event list is sorted by start time
                self.sort_by_start()
        
    def sort_by_start(self):
        self.events.sort(key=lambda event: event.start)
        
    def dur(self):
        self.sort_by_start()
        return(self.events[-1].start + self.events[-1].dur)
    
    def create_null_events(self):
        new_nulls = []
        for i in range(1, len(self.events)):
            first_event = self.events[i - 1]
            second_event = self.events[i]
            null_start = first_event.start + first_event.dur
            null_dur = second_event.start - null_start
            
            new_null_event = create_event_for_stim([null_start, null_dur, self.null_event], self.win)
            
            if(new_null_event.dur < 0):
                print "WARNING: Overlapping events detected while creating null events"
                print "new_null_event.dur = {0}".format(new_null_event.dur)
            
            # Append the null to a separate list
            if(new_null_event.dur > 0):
                new_nulls.append(new_null_event)        
    
        # Append all the new nulls to the event list
        for new_null_event in new_nulls:
            self.events.append(new_null_event)
            # Sort the event list again
            self.sort_by_start()
    
    def has_overlapping_events(self):
        overlap = False
        for i in range(1, len(self.events)):
            first_event = self.events[i - 1]
            second_event = self.events[i]
            first_event_end = first_event.start + first_event.dur
            if(first_event_end > second_event.start):
                overlap = True
        return(overlap)