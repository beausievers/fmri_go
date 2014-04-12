#TODO: Email Thalia about this: When can we test it, am I thinking this through correctly

from psychopy import core, data, visual, event, sound, gui

def create_event_for_stim(event_start, event_dur, stim):
    stim_ext = stim[-4:]
    
    # If the stimulus field begins and ends with double quotes
    if((stim[0] == '"') and (stim[-1] == '"')):
        new_event = TextEvent(
            event_start, event_dur, 
            stim[1:-1] # Strip the quotes 
        )   
    elif(stim_ext in ['.mp4', '.mov']):
        new_event = MovieEvent(
            event_start, event_dur, stim
        ) 
    elif(stim_ext in ['.jpg']):
        new_event = ImageEvent(
            event_start, event_dur, stim
        )
    return(new_event)

class Event:
    def __init__(self, start, dur, stim):
        self.start = start
        self.dur = dur
        self.stim = stim
        
class TextEvent(Event):
    def display(self, win):
        stimulus = visual.TextStim(win, pos=[0,0], text=self.stim)
        stimulus.draw()
        win.flip()

class ImageEvent(Event):
    def display(self, win):
        stimulus = visual.ImageStim(win, pos=[0,0], image=self.stim)
        stimulus.draw()
        win.flip()

class MovieEvent(Event):
    def display(self, win, clock, end_time):
        mov = visual.MovieStim(win, self.stim, 
                               flipVert=False, flipHoriz=False, loop=False)
        
        # Terminate and hand control back to fmri_go.py if either the movie ends
        # or we run out of time on the global clock.
        while((mov.status != visual.FINISHED) and (clock.getTime() < end_time)):
            mov.draw()
            win.flip()

class EventList:
    def __init__(self):
        self.events = []
        self.null_event = None
        
    def read_from_file(self, path):
        # Parse the script file and populate the global event array
        lines = [line.strip() for line in open(path)]
        for line in lines:
            splitline = line.split(',')
            if(splitline[0] == "NULL"):
                self.null_event = splitline[1]
            else:
                event_start = float(splitline[0])
                event_dur = float(splitline[1])
                new_event = create_event_for_stim(event_start, event_dur, splitline[2])
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
            
            #new_null_event = Event(null_start, null_dur, "NULL")
            new_null_event = create_event_for_stim(null_start, null_dur, self.null_event)
            
            if(new_null_event.dur < 0):
                print "WARNING: Overlapping events detected while creating null events"
            
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