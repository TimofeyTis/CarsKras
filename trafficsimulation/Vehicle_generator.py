from .Vehicle import Vehicle
from numpy.random import randint
from pandas import ExcelFile


class VehicleGenerator:
    def __init__(self, sim, config={}):
        self.sim = sim

        # Set default configurations
        self.set_default_config()

        # Update configurations
        for attr, val in config.items():
            setattr(self, attr, val)

        # Calculate properties
        self.init_properties()

    def set_default_config(self):
        """Set default configuration"""
        self.vehicle_rate = 20
        self.vehicles = [
            (1, {})
        ]
        self.last_added_time = 0

    def init_properties(self):
        self.upcoming_vehicle = self.generate_vehicle()
        self.cur_time_span = 3600.0 / self.vehicle_rate

    def generate_vehicle(self):
        """Returns a random vehicle from self.vehicles with random proportions"""
        total = sum(pair[0] for pair in self.vehicles)
        r = randint(1, total+1)
        for (weight, config) in self.vehicles:
            r -= weight
            if r <= 0:
                return Vehicle(config)

    def update(self):
        """Add vehicles"""
        if self.sim.t - self.last_added_time >= self.cur_time_span:
            # If time elasped after last added vehicle is
            # greater than vehicle_period; generate a vehicle
            if not(self.sim.roads): return
            road = self.sim.roads[self.upcoming_vehicle.path[0]]
            lane_id = randint(0,len(road.lanes_forward)) 
            lane = road.lanes_forward[lane_id]

            if len(lane.vehicles) == 0\
               or lane.vehicles[-1].x > self.upcoming_vehicle.s0 + self.upcoming_vehicle.l:
                # If there is space for the generated vehicle; add it
                self.upcoming_vehicle.time_added = self.sim.t
                
                lane.vehicles.append(self.upcoming_vehicle)
                # Reset last_added_time and upcoming_vehicle
                self.last_added_time = self.sim.t
            self.upcoming_vehicle = self.generate_vehicle()

class VehicleGeneratorUSDC(VehicleGenerator):   

      

    def update_param(self):
        self.gap = self.gap[1], next(self.gaps_it)
        self.vehicle_rate = next(self.rates_it)
        self.cur_time_span =  (self.gap[1] - self.gap[0]) / self.vehicle_rate if self.vehicle_rate else  self.gap[1] - self.gap[0]#sss
            
            
    def __init__(self, sim, file, config={}):
        super().__init__(sim, config)

        xl = ExcelFile(file)
        sheet_name = xl.sheet_names[0]
        df = xl.parse(sheet_name)

        self.gaps_it = iter(df["time"].tolist())
        self.rates_it = iter(df["data"].tolist())
        
        self.gap =  -1, next(self.gaps_it)
        self.update_param()



    def update(self):
        """Add vehicles"""
        while self.sim.t > self.gap[1]:
            self.update_param()
        super().update()
        
    