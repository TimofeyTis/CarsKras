from numpy import sqrt

class Vehicle:
    def __init__(self, config={}):
        # Set default configuration
        self.set_default_config()

        # Update configuration
        for attr, val in config.items():
            setattr(self, attr, val)

        # Calculate properties
        self.init_properties()

    def set_default_config(self):    
        self.l  = 4
        self.s0 = 4        # space
        self.T  = 1        # reaction time
        self.v_max = 11.11 # 40 km/h
        self.a_max = 1.44  
        self.b_max = 4.61

        self.path = []
        self.current_road_index = 0

        self.x = 0
        self.v = self.v_max
        self.a = 0
        self.stopped = False

        self.target_lane = None

        self.path_len = 0
    def init_properties(self):
        self.sqrt_ab = 2*sqrt(self.a_max*self.b_max)
        self._v_max = self.v_max
        self.path_len = len(self.path)


    def set_target_lane(self, lane):
        self.target_lane = lane


    def update(self, lead, dt):
        # Update position and velocity
        if self.v + self.a*dt < 0:
            self.x -= 1/2*self.v*self.v/self.a
            self.v = 0
        else:
            self.v += self.a*dt
            self.x += self.v*dt + self.a*dt*dt/2
        
        # Update acceleration
        alpha = 0
        if lead:
            delta_x = lead.x - self.x - lead.l
            delta_v = self.v - lead.v

            alpha = (self.s0 + max(0, self.T*self.v + delta_v*self.v/self.sqrt_ab)) / delta_x

        self.a = self.a_max * (1-(self.v/self.v_max)**4 - alpha**2)

        if self.stopped: 
            self.a = -self.b_max*self.v/self.v_max
        
    def stop(self):
        self.stopped = True

    def unstop(self):
        self.stopped = False

    def slow(self, v):
        self.v_max = v

    def unslow(self):
        self.v_max = self._v_max

    def get_path(self):
        return self.path[self.current_road_index]
    
    def get_next_path(self):
        next_road_index = 1 + self.current_road_index
        return self.path[next_road_index] if next_road_index < self.path_len else -1

