def CountTimeonCL(t, TL):
    """
    t - time()
    TL - TrafficLight class
    """

    if isinstance(TL, list):
        return [CountTimeonCL(t,tl) for tl in TL]


    A = S = TL.phases
    rew_act = np.zeros(shape=(S))
    for phase in range(S):
        for  timeq  in TL.collect_lines[phase]:#collect_line = [(car,time)]
            for car,time in timeq.items():
                rew_act[phase] += (t - time)

    r = np.zeros(shape=(S,A))
    for s in range(S):
        for a in range(S):
            r[s][a] = rew_act[(s + a) % S] 
    return r
    
class FLController:
    def __init__(self, TL) -> None:
        pass