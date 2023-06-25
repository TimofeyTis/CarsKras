from scipy.spatial import distance
from numpy import sqrt
from .Lane import Lane
from collections import deque
from .Traffic_signal import TrafficSignal



class Road:
    def __init__(self, start, end, config={}):
        # Set by default configuration
        self.set_default_config(start, end)



        # Update configuration
        for attr, val in config.items():
            setattr(self, attr, val)
        
        self.init_properties()

        

    def set_default_config(self, start, end):
        self.start = start
        self.end = end

        #Set configurations from OSMNX data
        self.oneway = True
        self.lanes = None
        self.name = ""
        self.oneway = True
        self.reversed = False
        self.length = 0
        self.osmid = 0
        
        self.lanes_forward = []
        self.lanes_backward = []

        self.lane_width = 3.75 # В России это так
        self.has_traffic_signal = False

    def init_properties(self):
        if not(self.length): self.length = distance.euclidean(self.start, self.end)

        # if self.reversed: 
        #     self.start,self.end = self.end, self.start
        #     self.reversed = False

        #Count angles for drawing
        self.angle_sin = (self.end[1]-self.start[1]) / self.length
        self.angle_cos = (self.end[0]-self.start[0]) / self.length

        #Init lanes

        if not(self.lanes): self.lanes = 1
        else: self.lanes = int(self.lanes)

        # Is it oneway road?
        number_lanes_forward = self.lanes
        number_lanes_backward = 0
        if not(self.oneway):
            number_lanes_backward = self.lanes//2
            number_lanes_forward = self.lanes - number_lanes_backward
        

        # Step for lane coords
        dy = self.lane_width*self.angle_cos
        dx = self.lane_width*self.angle_sin

        # Forward direction
        delta = -0.3
        for lf in range(number_lanes_forward,0,-1):
            start = self.start[0]-dx*(lf + delta), self.start[1]+dy*(lf + delta)
            end = self.end[0]-dx*(lf + delta), self.end[1]  +dy*(lf + delta)
            self.lanes_forward.append(Lane(start, end, self.length))

        # Forward direction
        # for lf in range(number_lanes_forward,0,-1):
        #     start = self.start[0]+dx*(lf+0.5), self.start[1]-dy*(lf+0.5) 
        #     end = self.end[0]+dx*(lf+0.5), self.end[1]-dy*(lf+0.5) 
        #     self.lanes_forward.append(Lane(start, end, self.length))
        #     self.width+=self.lane_width

        # Backward direction
        # for lb in range(number_lanes_backward,0,-1):
        #     end = self.start[0]-dx*(lb + 0.5), self.start[1]+dy*(lb + 0.5)
        #     start = self.end[0]-dx*(lb + 0.5), self.end[1]+dy*(lb + 0.5)
        #     self.lanes_backward.append(Lane(start, end, self.length))


    def get_vehicles(self):
        vehicles = []
        for lane in self.lanes_forward + self.lanes_backward:
            vehicles.append(lane.vehicles)
        return vehicles

    def update(self, dt):
        for lane in self.lanes_forward + self.lanes_backward:
            lane.update()


