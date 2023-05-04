import random
import math
import statistics
import sys

random.seed(10)
MAX_RANDOM_PREFERENCE = 20

class Person:
    crisis_effect = 0.4
    crisis_base_chance = 0.01
    crisis_chance_coef = 0.1
    active_questing_val = 0.65
    
    def __init__(self, religion, context, relationships, needs, name):
        self.religion = religion
        self.religion.members.append(self)
        self.context = context
        self.relationships = relationships
        self.needs = needs        
        '''
         The relative degree of satisfaction of each need.
         This determines the degree to which a person is actively or passively
         questing.
         [pleasure, relationships, self-esteem, conceptual system, transcendence] (Rambo, 63)
        '''
        
        self.name = name
        self.decisions = []
        self.impressions = {}
        self.encounter_count = {}
        self.update_coef = 0.7

        self.priorities = [random.randint(1,10) for _ in range(len(self.needs))]
        self.priorities = [self.priorities[i] / sum(self.priorities) for i in range(len(self.priorities))]
        
        self.bias = 1 # [1,2], perceived compataibility with the current religion. Affected by adaptations.
        self.random_preference = random.randint(1,MAX_RANDOM_PREFERENCE) # [1,20]
        '''
        Person.random_preference is introduced to account for the many small factors that affect a person's positive
        or negative view of a religion. This includes things such as being easily convinced, persuaded, or even
        manipulated by a particular religion for whatever reason (e.g. UFO cults, NRMs incorporating 'brainwashing'
        techniques), living in a context or growing up with a family which had positive/negative personal history
        with such a religion, and so on. For now, this will also include interpersonal relationships, e.g. having a
        positive/negative relationship with someone in the group. The closer Person.random_preference matches with
        Religion.random_preference, the more likely the Person has a predilection towards the religion for random reasons.
        '''
        

    def __str__(self):
        return "<Person: {}>".format(self.name)

    def __repr__(self):
        return self.__str__()
    
    @property
    def quest_val(self):
        mult = [self.priorities[i] * (1-self.needs[i]) for i in range(len(self.priorities))]
        return sum(mult) / self.bias

    def is_actively_questing(self):
        return self.quest_val >= Person.active_questing_val 
    
    def update_needs(self):
        for i in range(len(self.needs)):
            self.needs[i] += self.priorities[i]*self.update_coef*(self.religion.provisions[i] - self.needs[i])

    def update_impression(self, r, e):
        if r not in self.impressions:
            self.impressions[r] = 0
            self.encounter_count[r] = 1
        else:
            self.impressions[r] += e.intensity * ((e.typeof == Encounter.ACTIVE) + 1)
            self.encounter_count[r] += 1
        
    
    def check_for_crisis(self):
        # Crisis, p.48
        # Random chance (illness, mystical vision) + dissatisfaction with current life
        crisis_chance = Person.crisis_base_chance
        for i in range(len(self.needs)):
            crisis_chance += Person.crisis_chance_coef*self.priorities[i]*(1 - self.needs[i])
        chk = random.random()
        if chk < crisis_chance:
            self.simulate_crisis()

    def simulate_crisis(self):
        for i in range(len(self.needs)):
            self.needs[i] *= Person.crisis_effect
        
    def check_for_conversion(self, time):
        for r2 in self.encounter_count:
            if r2 not in self.encounter_count or self.encounter_count[r2] % 50 != 0 or self.encounter_count[r2] == 0:
                continue
            provision_diffs = [r2.provisions[i] - self.religion.provisions[i] for i in range(len(self.needs))]
            weighted_advantage = sum([self.priorities[i] * provision_diffs[i] for i in range(len(self.needs))]) * 50
            
            impressions_list = []
            for member in self.religion.members:
                if r2 not in member.impressions:
                    impressions_list.append(0)
                else:
                    impressions_list.append(member.impressions[r2])
            avg_impression = statistics.mean(impressions_list)
            if len(impressions_list) == 1:
                z = 2
            else:
                stdev_impressions = statistics.stdev(impressions_list)
                z = (self.impressions[r2] - avg_impression) / stdev_impressions # conversion depended not on belief but on whether they had stronger relationships with people in the group than out (p. 127)
            
            resilience = self.context.resilience
            adaptability = self.religion.member_adaptability
            
            if z < 0:
                if weighted_advantage + adaptability < 2:
                    self.decide_reject(r2, 0.01, time)
                else:
                    self.decide_adapt(r2, 0.05, time)                  
                return
            
            else:
                
                if (weighted_advantage + (2*z*resilience)) / adaptability < 4:
                    self.decide_adapt(r2, 0.1, time)
                else:
                    self.decide_convert(r2, time)

    def decide_reject(self, other_r, bias_increase, time):
        self.decisions.append(Decision(Decision.REJECT, self.religion, other_r, time))
        self.impressions[other_r] = 0
        self.encounter_count[other_r] += 1
        self.bias += bias_increase

    def decide_adapt(self, other_r, bias_increase, time):
        self.decisions.append(Decision(Decision.ADAPT, self.religion, other_r, time))
        self.impressions[other_r] /= 2
        self.encounter_count[other_r] += 1
        self.bias += bias_increase        
                 
    def decide_convert(self, other_r, time):
        self.decisions.append(Decision(Decision.CONVERT, self.religion, other_r, time))
        self.impressions = {}
        self.encounter_count = {}
        self.bias = 1
        
        self.religion.members.remove(self)
        other_r.members.append(self)
        self.religion = other_r
   
class Religion:
    def __init__(self, publicity, provisions, name, advocate_adaptability):
        self.publicity = publicity # [0,1], the likelihood of an encounter
        self.provisions = provisions # the objective compatibiliy
        self.name = name
        self.members = []
        self.advocate_adaptability = advocate_adaptability #[1, 5], once in an encounter how likely to cater to the individual (p. 97)
        self.member_adaptability = random.randint(5,20)/10 #[0.5, 2], how adaptable the religion is from a member's perspective - determines whether individuals ADAPT or CONVERT (p.23, p. 93)
        self.encapsulation_val = 1 # [0, 1]
        self.random_preference = random.randint(1,MAX_RANDOM_PREFERENCE)

    def __str__(self):
        return "<Religion: {}>".format(self.name)
    
    def __repr__(self):
        return self.__str__()
    
    def __hash__(self):
        return hash((self.random_preference, self.advocate_adaptability, self.member_adaptability))
    
class Context:
    def __init__(self, name, fluidity, stability, resilience):
        self.name = name # human readable string
        self.fluidity = fluidity # [0,1], likelihood of encounter (p. 26, transportation and communication)
        self.stability = stability # [0,2], higher means more resilient to positive impressions (China, Japan example)
        self.resilience = resilience # [0, 1?], lower means more resilient to conversion

    def __str__(self):
        return '<Context: {}>'.format(self.name)
    def __repr__(self):
        return self.__str__()

class Relationship:
    def __init__(self, other, importance):
        self.other = other # instance of Person or Context
        self.importance = importance # [0,10], also a measure of 'marginality'

class Decision:
    REJECT = 0
    ADAPT = 1 # (p. 23)
    CONVERT = 2
    def __init__(self, decision, cur_religion, new_religion, time):
        self.decision = decision
        self.cur = cur_religion
        self.new = new_religion
        self.time = time
        
    def __str__(self):
        return "<Decision: {}; cur: {}, new: {}, time: {}>".format(['REJECT', 'ADAPT', 'CONVERT'][self.decision], self.cur, self.new, self.time)

    def __repr__(self):
        return self.__str__()

class Encounter:
    PASSIVE = 0
    ACTIVE = 1
    def __init__(self, typeof=0, intensity=0):
        self.typeof = typeof
        self.intensity = intensity

    def __str__(self):
        typeof_str = ['PASSIVE', 'ACTIVE'][self.typeof]
        return '<Encounter: {} encounter with intensity {}>'.format(typeof_str, self.intensity)

    def __repr__(self):
        return self.__str__()

    def is_passive(self):
        return self.typeof == Encounter.PASSIVE
    
    def is_active(self):
        return self.typeof == Encounter.ACTIVE
    
    
def init_religions():
    r1 = Religion(2, [0.7,0.8,0.6,0.7,0.77], 'Religion 1', 5)
    r2 = Religion(0.8, [0.6, 0.7, 0.8, 0.8, 0.6], 'Religion 2', 5)
    r3 = Religion(0.5, [0.8, 0.8, 0.77, 0.77, 0.77], 'Religion 3', 1)
    r4 = Religion(0.7, [0.5, 0.6,0.6, 0.8, 0.9], 'Religion 4', 8)
    return [r1, r2, r3, r4]
    
def init_people(religions):
    
    names = list('ABCDEFGHIJKLMNOPQRSTUV')
    return [Person(random.choice(religions), context, [], [random.randrange(50,90)/100 for _ in range(5)], names[i]) for i in range(len(names))]

def gen_encounter(p, r, c):
    '''
    1. probability check if there is an encounter
        p.quest_val
        r.publicity
        c.fluidity
    2. type of encounter determines magnitude
        p.quest_val
    3. intensity of encounter
        c.stability
        r.provisions
        interpersonal relationship?
        Positive encounters
            Preexisting positive bias
            Fits with what you are seeking
        Negative encounters
            Conflicts with your beliefs
        Eventually: build over time
    '''
    encounter_probability = p.quest_val * r.publicity * c.fluidity # add impression score to probability
    
    if p.is_actively_questing():
        encounter_probability *= 2
        encounter_probability = min(encounter_probability, 1)
        
    
    if random.random() > encounter_probability:
        return None

    e = Encounter(typeof=Encounter.PASSIVE)
    if p.quest_val > random.random():
        e.typeof = Encounter.ACTIVE

    random_bias = math.log(MAX_RANDOM_PREFERENCE / (abs(p.random_preference - r.random_preference + 0.1)) + 1)
    positive_diffs = [p.priorities[i] * max(r.provisions[i] - p.needs[i], 0) for i in range(len(p.needs))]
    mag = random_bias * c.stability * r.advocate_adaptability * (10*sum(positive_diffs))
    e.intensity = mag
    return e


def simulate(MAX_TIME=1000, file_name=None):
    t = 0
    orig_stdout = sys.stdout
    if file_name:
        f = open(file_name, 'w')
        sys.stdout = f
            
    while t < MAX_TIME:
        t += 1
        for p in people:
            p.update_needs()
            p.check_for_crisis()
            for r in religions:
                if p.religion == r:
                    continue
                e = gen_encounter(p, r, context)
                if e is not None:
                    p.update_impression(r, e)
            p.check_for_conversion(t) 
            
    sys.stdout = orig_stdout

def display_variables(file_name=None):
    orig_stdout = sys.stdout
    if file_name:
        f = open(file_name, 'w')
        sys.stdout = f

    print("="*8 + ' PEOPLE ' + "=" * 8)
    print("Number of people: {}".format(len(people)))
    for p in people:
        print("Person {}".format(p))
        print("\tContext {}".format(p.context))
        print("\tReligion {}".format(p.religion))
        print("\tPriorities {}".format(p.priorities))
        print("\tRandom_preference {}".format(p.random_preference))
        print("\tBias {}".format(p.bias))
        print("\tDecisions:", end='\n\t\t')
        print("\n\t\t".join(list(map(str, p.decisions))))
        print()

    print()
    print("{} {} {}".format('='*8, 'RELIGIONS', '='*8))
    print("Number of religions: {}".format(len(religions)))
    for r in religions:
        print("Religion {}".format(r))
        print("\tProvisions {}".format(r.provisions))
        print("\tMembers {}".format(r.members))
        print("\tAdvocate Adaptability: {}, Member Adaptability: {}".format(r.advocate_adaptability, r.member_adaptability))
        print("\tPublicity {}".format(r.publicity))
        print("\tRandom Preference {}".format(r.random_preference))
        print()

    print()
    print("{} {} {}".format('='*8, 'CONTEXTS', '='*8))
    print("Number of contexts: 1")
    print("Context {}".format(context))
    print("\tResilience = {} Fluidity = {} Stability = {}".format(context.resilience, context.fluidity, context.stability))
    print()
    sys.stdout = orig_stdout

    
context = Context('Society', 1.5, 1, 1)

religions = init_religions()
people = init_people(religions)

simulate(10000)
display_variables(file_name='out.txt')

# TODO 
# other members having an effect on likelihood of conversion - interpersonal relationships
