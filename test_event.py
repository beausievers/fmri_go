from psychopy import core, data, visual, event, sound, gui
import event
import unittest

class TestEvent(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def test_create_null_events_creates_correct_start_times(self):
        win = visual.Window([800, 600], monitor='testMonitor')
        events = event.EventList(win)
        events.read_from_file('test_scripts/test_script.txt')
        events.create_null_events()
        
        #NULL,"+"
        #0,2,"pecan"
        #6,3,"walnut"
        #13,2,"apricot"
        #15,2,"melon"

        # null at 0 + 2 for 6 - 2
        # null at 6 + 3 for 13 - (6+3) 

        # 0  - 2  pecan
        # 2  - 6  NULL
        # 6  - 9  walnut
        # 9  - 13 NULL
        # 13 - 15 apricot
        # 15 - 17 melon
        
        self.assertEqual(9, events.events[3].start)
    
    def test_create_null_events_creates_correct_durations(self):
        win = visual.Window([800, 600], monitor='testMonitor')
        events = event.EventList(win)
        events.read_from_file('test_scripts/test_script.txt')
        events.create_null_events()
        self.assertEqual(4, events.events[3].dur)
        
    def test_create_null_events_no_null_between_adjacent_non_nulls(self):
        win = visual.Window([800, 600], monitor='testMonitor')
        events = event.EventList(win)
        events.read_from_file('test_scripts/test_script.txt')
        events.create_null_events()
        self.assertEqual('melon', events.events[5].stim_str)
        
    def test_create_null_events_does_not_create_overlapping_events(self):
        win = visual.Window([800, 600], monitor='testMonitor')
        events = event.EventList(win)
        events.read_from_file('test_scripts/test_script_without_overlap.txt')
        events.create_null_events()
        self.assertFalse(events.has_overlapping_events())
        
    def test_has_overlapping_events_finds_overlapping_events_before_null_creation(self):
        win = visual.Window([800, 600], monitor='testMonitor')
        events = event.EventList(win)
        events.read_from_file('test_scripts/test_script_with_overlap.txt')
        self.assertTrue(events.has_overlapping_events())
        
    def test_has_overlapping_events_finds_overlapping_events_after_null_creation(self):
        win = visual.Window([800, 600], monitor='testMonitor')
        events = event.EventList(win)
        events.read_from_file('test_scripts/test_script_with_overlap.txt')
        events.create_null_events()
        self.assertTrue(events.has_overlapping_events())
        
if __name__ == '__main__':
    unittest.main()
