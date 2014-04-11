class Event:
    def __init__(self, start, dur, stim):
        self.start = start
        self.dur = dur
        self.stim = stim
        
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
                self.events.append(Event(
                    float(splitline[0]), 
                    float(splitline[1]), 
                    splitline[2]))
                # Should guarantee that event list is sorted by start time
                self.sort_by_start()
        
    def append(self, item):
        self.events.append(item)    
        
    def sort_by_start(self):
        self.events.sort(key=lambda event: event.start)
                
    def create_null_events(self):
        new_nulls = []
        for i in range(1, len(self.events)):
            first_event = self.events[i - 1]
            second_event = self.events[i]
            null_start = first_event.start + first_event.dur
            null_dur = second_event.start - null_start
            new_null_event = Event(null_start, null_dur, "NULL")
            
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