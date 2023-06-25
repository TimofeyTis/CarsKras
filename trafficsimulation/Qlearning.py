import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as fctr


def Qlearning_init(TL):
    tsize = len(TL)

    Q = []
    Q2 = []
    MAXQ = []
    M = []
    NB = []
    for i in range(tsize):
        ti = TL[i]
        Si = ti.phases

        Q.append([])
        Q2.append([])
        MAXQ.append([])
        M.append([])
        NB.append(list(range(i+1,tsize)) + list(range(i)))
        if not(len(NB[i])):
            Q[i] = np.zeros(shape=(Si,Si))
            Q2[i] = np.zeros(shape=(Si,Si))
            MAXQ[i] = np.zeros(shape=(Si))
            M[i] = None
        for j in NB[i]:
            tj = TL[j]
            Aj = Sj = tj.phases

            Sij = Si*Sj

            Q[i].append(np.zeros(shape=(Sij,Sij)))
            Q2[i].append(np.zeros(shape=(Sij,Sij)))
            MAXQ[i].append(np.zeros(shape=(Sij)))
            M[i].append(np.ones(shape=(Sij,Aj+1)))
    return Q, Q2, MAXQ, M, NB

def CountPhaseTime(t,TL):
    """
    t - time()
    TL - TrafficLight class
    """

    if isinstance(TL, list):
        return [CountTimeonTL(t,tl) for tl in TL]


    A = S = TL.phases
    rew_act = np.zeros(shape=(S))
    for phase in range(S):
        for  timeq  in TL.collect_lines[phase]:#collect_line = [(car,time)]
            for car,time in timeq.items():
                rew_act[phase] += (t - time)

    return rew_act
def CountTimeonTL(t, TL):
    """
    t - time()
    TL - TrafficLight class
    """

    if isinstance(TL, list):
        return [CountTimeonTL(t,tl) for tl in TL]


    rew_act = CountPhaseTime(t,TL)
    A = S = TL.phases
    r = np.zeros(shape=(S,A))
    for s in range(S):
        for a in range(S):
            r[s][a] = rew_act[(s + a) % S] 
    return r
def CountVehonTL(t, TL):
    """
    t - time()
    TL - TrafficLight class
    """
    if isinstance(TL, list):
        return [CountTimeonTL(t,tl) for tl in TL]

    S = TL.phases
    v = 0
    for phase in range(S):
        for  timeq  in TL.collect_lines[phase]:#collect_line = [(car,time)]
            for _ in timeq.items():
                v += 1
    return v
def GetTLparams(TL):
    ti = TL
    si = ti.current_cycle_index
    Ai = Si = ti.phases
    return si,Ai,Si

def Qfunction(Q, r, MAXQ, alfa = 0.1,gamma = 0.1):
    S,A = Q.shape
    Q2 = np.zeros_like(Q)
    for s in range(S):
        for a in range(A):
            s_ = (s + a) % S
            Q2[s][a] = Q[s][a] * (1 - alfa) + alfa * (r[s][a] + gamma * MAXQ[s_])
    return Q2
def CumReward(ri,rj):
    Si,Ai = ri.shape
    Sj,Aj = rj.shape

    Aij = Sij = Si*Sj

    r = np.zeros(shape=(Sij,Aij))
    for s in range(Sij):
        for a in range(Aij):
            si = s//Sj
            sj = s%Sj
            ai = a//Aj
            aj = a%Aj
            r[s][a] = ri[si][ai]+rj[sj][aj]
    return r

def Qlearning(Q, Q2, MAXQ, M, NB, TL, time, a, alfa = 0.4,gamma = 0.1):
    #print("Ql")
    tsize = len(TL)

    
    a2 = [0]*tsize
    r = CountTimeonTL(time, TL)

    for i in range(tsize):
        si,Ai,Si = GetTLparams(TL[i])

        if not(len(NB[i])):
            Q2[i] = Qfunction(Q[i],r[i],MAXQ[i],alfa,gamma)

        for j in range(len(NB[i])):
            sj,Aj,Sj = GetTLparams(TL[NB[i][j]])
            aj = int(a[NB[i][j]])

            sij = si*Sj +sj

            rij = CumReward(r[i],r[NB[i][j]])

            #print(M[i][j])
            M[i][j][sij][aj] +=1
            M[i][j][sij][Aj] +=1

            MAXQ[i][j] = np.max(Q[i][j] ,axis = 1)


            Q2[i][j] = Qfunction(Q[i][j],rij,MAXQ[i][j],alfa,gamma)


    for i in range(tsize):
        a2sum = []
        si,Ai,Si = GetTLparams(TL[i])
        if not(len(NB[i])):
            a2[i] = np.argmax(Q2[i][si])
            TL[i].SwitchNphases(a2[i])
            continue
        for ai in range(Ai):
            a2sumi = []
            for j in range(len(NB[i])):
                sj,Aj,Sj = GetTLparams(TL[NB[i][j]])
                for aj in range(Aj):
                    sij = si*Sj + sj
                    aij = ai*Aj + aj
                    a2sumi.append(Q2[i][j][sij][aij]*M[i][j][sij][aj]/ M[i][j][sij][Aj])
            a2sum.append(sum(a2sumi))
        a2[i] = np.argmax(a2sum)
        TL[i].SwitchNphases(a2[i])
    
    return a2,Q2

class Controller:
    def set_default_config(self):
        self.data = []
        self.t = 0


    def __init__(self,TL):
        """
        TL - list of TrafficLight class = [i]
        a - last actions ai
        """
        self.TL = TL
        self.set_default_config()
        

class MARLINController(Controller):
    def __init__(self,TL):
        """
        TL - list of TrafficLight class = [i]
        NB - list of i neighbours NB[i] = [j]
        a - last actions ai
        Q - table of Q[i][j][sij][aij] function values
        M - memorized M[i][j][sij][aj] actions
        """
        super().__init__(TL)
        self.a = [0] * len(self.TL)

        self.step = 8
        self.Q, self.Q2, self.MAXQ, self.M, self.NB = Qlearning_init(TL)

        self.data = []
        for i in range(len(TL)):
            self.data.append([])
            for _ in self.NB[i]:
                self.data[i].append([])

    def __call__(self, time, alfa = 0.1, gamma = 0.1):

        self.t = time
        self.a,self.Q = Qlearning(self.Q, self.Q2, self.MAXQ, self.M, self.NB, self.TL, time, self.a, alfa, gamma)
        
        for i in range(len(self.TL)):
            ti = self.TL[i]
            si = ti.current_cycle_index
            ai = self.a[i]
            if not(len(self.NB[i])):
                self.data[i].append(self.Q[i][si][ai])

            for j in range(len(self.NB[i])):
                
                tj = self.TL[self.NB[i][j]]
                sj,Sj,Aj = GetTLparams(tj)
                sij = si*Sj +sj

                aj = self.a[self.NB[i][j]]
                aij = ai*Aj +aj
                self.data[i][j].append(self.Q[i][j][sij][aij])

        return self.a


def set_default_fv_time():
    x_time_of_day = np.arange(0, 24*3600, 3600)  # время 24ч в секундах c дискретностью Час
    # нечеткие множества
    first_day_part       =  fuzz.trapmf(x_time_of_day, [4*3600, 7*3600,  11*3600, 12*3600])
    second_day_part      =  fuzz.trapmf(x_time_of_day, [10*3600,12*3600, 16*3600, 18*3600])
    second_half_day_part =  fuzz.trapmf(x_time_of_day, [16*3600,18*3600, 20*3600, 21*3600])
    third_day_part       =  fuzz.trapmf(x_time_of_day, [0,      0,       4*3600,  7*3600 ]) + fuzz.trapmf(x_time_of_day, [20*3600, 21*3600, 24*3600, 24*3600])

    fv_time = fctr.Antecedent(x_time_of_day, 'day time')
    fv_time["morning"] = first_day_part
    fv_time["day"]     = second_day_part
    fv_time["evening"] = second_half_day_part
    fv_time["night"]   = third_day_part
    return    fv_time
def make_default_fuzz_partition( MAX):
    x_set = np.arange(0, MAX, 1)
    # нечеткие множества
    big    = fuzz.trapmf(x_set, [0.6*MAX,  0.75*MAX, MAX,      MAX     ])
    medium = fuzz.trapmf(x_set, [0.25*MAX, 0.33*MAX, 0.66*MAX, 0.75*MAX])
    small  = fuzz.trapmf(x_set, [0,        0,        0.25*MAX, 0.4*MAX ])
    return small, medium, big, x_set

def set_default_fv_vehicles():
    MAX_VEH = 500
    veh_run, veh_wait, veh_jam, x_vehicles =  make_default_fuzz_partition(MAX_VEH)

    fv_vehicles = fctr.Antecedent(x_vehicles, 'vehicles')
    fv_vehicles["jam"]  = veh_jam
    fv_vehicles["wait"] = veh_wait
    fv_vehicles["run"]  = veh_run
    return fv_vehicles
def set_default_fv_reward():
    MAX_REW = 200
    reward_small, reward_medium, reward_large, x_reward =  make_default_fuzz_partition(MAX_REW)

    fv_reward = fctr.Antecedent(x_reward, 'reward')
    fv_reward["small"]  = reward_small
    fv_reward["medium"] = reward_medium
    fv_reward["large"]  = reward_large
    return fv_reward
def set_default_fv_phase_dur():
    MAX_DUR = 300
    phase_short, phase_med, phase_long, x_phase_duration =  make_default_fuzz_partition(MAX_DUR)

    fv_phase_dur = fctr.Consequent(x_phase_duration, 'phase')
    fv_phase_dur["short"]  = phase_short
    fv_phase_dur["medium"] = phase_med
    fv_phase_dur["long"]   = phase_long
    return fv_phase_dur
class FLController(Controller):
    
    
    def set_default_fv(self):
       self.fv_time      = set_default_fv_time()
       self.fv_vehicles  = set_default_fv_vehicles()
       self.fv_reward    = set_default_fv_reward()
       self.fv_phase_dur = set_default_fv_phase_dur()

    def set_default_rules(self):
        self.rules = [
            fctr.Rule(self.fv_time["morning"], self.fv_phase_dur["short"]),
            fctr.Rule(self.fv_time["night"] , self.fv_phase_dur["short"]),
            fctr.Rule(self.fv_reward["small"], self.fv_phase_dur["short"]),
            fctr.Rule(self.fv_vehicles["run"], self.fv_phase_dur["short"]),
            fctr.Rule(self.fv_vehicles["jam"]  & self.fv_reward["medium"], self.fv_phase_dur["short"]),
            fctr.Rule((self.fv_time["day"] | self.fv_time["evening"]) & (self.fv_reward["medium"]), self.fv_phase_dur["medium"]),
            fctr.Rule((self.fv_time["day"] | self.fv_time["evening"]) & (self.fv_reward["large"]), self.fv_phase_dur["long"]),
            fctr.Rule(self.fv_vehicles["wait"]  & self.fv_reward["medium"], self.fv_phase_dur["long"]),
            fctr.Rule(self.fv_vehicles["jam"]  & self.fv_reward["large"], self.fv_phase_dur["long"]),   
        ]

    def set_default_config(self):
        super().set_default_config()

        self.set_default_fv()
        self.set_default_rules()




    def __init__(self, TL):
        super().__init__(TL)
        self.step = 0
        self.set_default_config()

        FL_ctrl = fctr.ControlSystem(self.rules)
        self.FL_sim = fctr.ControlSystemSimulation(FL_ctrl)
        self.data = []


    def __call__(self, time):
        self.t = time
        time = int(time) 
        day_time = time - time % 3600  #ТУТ ЗАПЛАТКА ТК ДАННЫЕ НЕ ОТНОРМИРОВАНЫ ПО ЧАСАМ... И НАЧИНАЮТСЯ С 14
        vehicles = int(CountVehonTL(time,self.TL))
        


        s,A,S = GetTLparams(self.TL)
        for s in range(S):
            reward = CountPhaseTime(time,self.TL)[s]
            self.FL_sim.input['day time'] = day_time
            self.FL_sim.input['vehicles'] = vehicles 
            self.FL_sim.input['reward']   = int(reward)
            
            self.FL_sim.compute()
            self.TL.cycle_length[s] = self.FL_sim.output['phase']
        self.step = sum(self.TL.cycle_length)

        self.data.append([self.TL.cycle_length, time])