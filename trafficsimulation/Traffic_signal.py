class TrafficSignal:
    def __init__(self, phase_order, config={}):
        # Initialize roads
        self.phase_order = phase_order

        # надо потом убрать
        self.collect_lines = []
        
        # Set default configuration
        self.set_default_config()
        # Update configuration
        for attr, val in config.items():
            setattr(self, attr, val)
        # Calculate properties
        self.init_properties()

    def set_default_config(self):
        self.cycle = [(False, True), (True, False)]

        self.adaptive = False

        self.slow_distance = 50
        self.slow_factor   = 0.1
        self.stop_distance = 15

        self.current_cycle_index = 0
        self.last_t = 0

    def init_properties(self):
        self.phases = len(self.cycle)

        i=0
        for phase_group in self.phase_order:
            for lane in phase_group:
                lane.set_traffic_signal(self, i)
            i+=1

    @property
    def current_cycle(self):
        return self.cycle[self.current_cycle_index]

    def SwitchNphases(self, phase):
        self.current_cycle_index = (self.current_cycle_index + phase)% len(self.cycle )

    def Fixed(self, sim):
        cycle_length = 30
        k = (sim.t // cycle_length) % len(self.cycle)
        self.current_cycle_index = int(k)

    def Adaptive(self, sim):
        pass

    def update(self, sim):
        if not(self.adaptive): self.Fixed(sim)
        #self.Fixed(sim)

