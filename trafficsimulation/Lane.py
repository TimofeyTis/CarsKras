from collections import deque


class Lane:

   def __init__(self, start, end, length):
      self.start = start
      self.end = end
      self.length = length

      self.blocked = False
      self.has_traffic_signal = False


      self.vehicles = deque()
      self.t = {}

      self.IN_transition = self.OUT_transition = False

   def set_traffic_signal(self, signal, group):
      if self.has_traffic_signal == False:
         self.traffic_signal = []
         self.traffic_signal_group = []

      self.has_traffic_signal = True
      self.traffic_signal.append(signal)
      self.traffic_signal_group.append(group)
      

   def set_traffic_block(self, blocked):
      self.blocked = blocked

   @property
   def traffic_signal_state(self):
      if self.has_traffic_signal:
         for traffic_signal, group in zip(self.traffic_signal, self.traffic_signal_group):
            if traffic_signal.current_cycle[group]:  return True
         return self.traffic_signal[0]
      return True



   def make_slowing(self, slow_distance, stop_distance, slow_factor):
      for vehicle in self.vehicles:
         if vehicle.x >= self.length - slow_distance:
            # Slow vehicles in slowing zone
            vehicle.slow(slow_factor*vehicle._v_max)
         if vehicle.x >= self.length - stop_distance:
            # Stop vehicles in the stop zone
            vehicle.stop()
         

   def update_signal(self):
      if not(self.vehicles): return
   
      tss = self.traffic_signal_state
      # If traffic signal is green
      if tss == True:
         self.vehicles[0].unstop()
         for vehicle in self.vehicles:
            vehicle.unslow()
         return

      # If traffic signal is red
      slow_distance = tss.slow_distance
      stop_distance = tss.stop_distance
      slow_factor = tss.slow_factor
      self.make_slowing(slow_distance, stop_distance, slow_factor)
      



   def update_blocked(self):
      if self.blocked:
         slow_distance = 8
         slow_factor = 0.1
         stop_distance = 3
         self.make_slowing(slow_distance, stop_distance, slow_factor)
         return


   def update(self, dt):
      n = len(self.vehicles)
      if not(n): return

      self.update_signal()
      self.update_blocked()


      # Update other vehicles
      self.vehicles[0].update(None, dt)
      for i in range(1, n):
         lead = self.vehicles[i-1]
         self.vehicles[i].update(lead, dt)

      