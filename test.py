import numpy as np
from trafficSimulator import *


sim = Simulation()

# Add one road
# Add multiple roads
sim.create_roads([
    ((0, 0), (70, 0)),
    ((200, 0), (130, 0)),
    ((100, 20), (100, 50)),
    *turn_road((70, 0),(100, 20),1,2),
    *turn_road((130, 0),(100, 20),0,2),
    
    
])

sim.create_gen({
    'vehicle_rate': 60,
    'vehicles': [
        [1, {"path": [0,*range(3,5),2]}],
        [1, {"path": [1,*range(5,7),2]}],
    ]
})

sim.create_signal([[0,2], [1,]])



#sim.roads[0].vehicles.append(Vehicle())
# Start simulation
win = Window(sim)
win.zoom = 3
win.run(steps_per_update=8)