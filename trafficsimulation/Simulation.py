from collections import deque
from copy import copy, deepcopy
from .Road import Road
from .Vehicle_generator import VehicleGenerator,VehicleGeneratorUSDC
from .Traffic_signal import TrafficSignal
from .Qlearning import MARLINController, FLController



def collect_control_lines(signal):
    signal.collect_lines = []
    for phases in signal.cycle:
        lines_om_phase_act = []
        for id in range(len(phases)):
            if phases[id]: 
                lanes = signal.phase_order[id]
                for lane in lanes:
                    lane.IN_transition = lane.OUT_transition = True
                    lines_om_phase_act.append(lane.t)
        signal.collect_lines.append(lines_om_phase_act)


def check_road_block(vehicle, roads):
    next_road_index = vehicle.get_next_path()
    if next_road_index == -1: return False

    next_road = roads[next_road_index]
    
    for lane in next_road.lanes_forward:
        if not(lane.vehicles): 
            vehicle.target_lane = lane
            return False

    for lane in next_road.lanes_forward:
        lead = lane.vehicles[-1]
        if lead.x  > vehicle.l + vehicle.s0:
            vehicle.target_lane = lane 
            return False
    return True

def road_transitioning(vehicles, lane,  length, roads, t, lane_transition_out):
    n = len(vehicles)

    

    while (n and vehicles[0].x >= length-vehicles[0].l ):

        if lane.blocked:  
            vehicles[0].x = length - vehicles[0].l
            return
        
        vehicle = vehicles.popleft()
        if lane.OUT_transition: 
            t1 = lane.t.pop(vehicle, None)
            if t1 : lane_transition_out(t-t1)

        n-=1
        road_index = vehicle.get_next_path()
        if road_index == -1: continue
        
        new_vehicle = vehicle
        check_road_block(new_vehicle, roads)

        new_lane = new_vehicle.target_lane 
        new_lane.vehicles.append(new_vehicle)
        
        new_vehicle.x = 0
        new_vehicle.current_road_index += 1
        
        if new_lane.IN_transition: 
            new_lane.t[new_vehicle] = t
            #print(self.t)
class Simulation:
    def lane_transition_out(self, time):
        self.MCOUNT     += 1
        self.TOTAL_TIME += time
        self.MAX_TIME   = max(self.MAX_TIME, time)

    def __init__(self,config={}):

        # Init goal params
        self.MCOUNT     = 0     # Total machine count on controlled intersection transition
        self.TOTAL_TIME = 0     # Total transition time count on controlled intersection
        self.MAX_TIME   = 0     # Max of transition time on controlled intersection

        # Set default configuration
        self.set_default_config()

        # Update configuration
        for attr, val in config.items():
            setattr(self, attr, val)


    
    def set_default_config(self):
        self.t           = 0.0  # Time keeping
        self.frame_count = 0    # Frame count keeping
        self.dt          = 1/5  # 1/60  Simulation time step

        self.roads              = {}    # Dict to store roads by their osmid
        self.generators         = []    # Vehicle generators defined by traffic intensivity
        self.traffic_signals    = []    # Traffic lights
        self.buildings          = []    # Additional info about buildings (will be expanded soon)
        self.tl_control_func    = []    # Control function objects for TLs
        self.all_lanes          = []    # All lines on road
        
    def create_road(self, start, end, road_config = {}):
        road = Road(start, end, road_config)
        self.roads[road.osmid] =  road
        self.all_lanes.extend(road.lanes_forward)
        return road

    def create_roads(self, road_list):
        for road in road_list: self.create_road(*road)

    def create_gen_from_usdc_data_collector(self, file, config={}):
        gen = VehicleGeneratorUSDC(self, file, config)
        self.generators.append(gen)
        return gen

    def create_gen(self, config={}):
        gen = VehicleGenerator(self, config)
        self.generators.append(gen)
        return gen

    def create_buildings(self, buildings):
        self.buildings = buildings
    
    def increment_time(self):
        self.t           += self.dt
        self.frame_count += 1

    def create_signal(self, program, config={}):
        phase_order = []
        for phases in program:
            phase = []
            for roadid,lines in phases.items():
                road = self.roads[roadid]
                for lineid in lines:
                    phase.append(road.lanes_forward[lineid])
            phase_order.append(phase)
         
        sig = TrafficSignal(phase_order, config)
        self.traffic_signals.append(sig)
        return sig



    def create_control(self, signals, type = "Fixed"):

        for signal in signals: collect_control_lines(signal)

        control_func = None
        if type == "MARLINController":
            control_func = MARLINController(signals)
            self.tl_control_func.append(control_func)
            for signal in signals: signal.adaptive = True

        elif type == "FLController":
            control_func = FLController(signal)
            self.tl_control_func.append(control_func)
            for signal in signals: signal.adaptive = False
        elif type == "Fixed":
            for signal in signals: signal.adaptive = False
        
        return control_func


    def update(self):
        active_lanes = [lane for lane in self.all_lanes if lane.vehicles]

        for lane in active_lanes:           # Update vehicles on lanes
            lane.blocked = check_road_block(lane.vehicles[0], self.roads)
            road_transitioning(lane.vehicles,lane, lane.length, self.roads, self.t, self.lane_transition_out)

        for lane in active_lanes:           # Update lanes
            lane.update(self.dt)
        for gen in self.generators:         # Update generators
            gen.update()
        for signal in self.traffic_signals: # Update signal states
            signal.update(self)
        for control in self.tl_control_func:# Update signal control objects
            if self.t - control.t >= control.step: control(self.t)
        self.increment_time()               # Update time
                
    def run(self, steps):
        for _ in range(steps):
            self.update()

