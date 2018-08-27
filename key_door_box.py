import json
import actr
import numpy as np
import random
import itertools

not_dicts = ['FILLED-SLOTS','EMPTY-SLOTS','BLENDED-SLOTS','IGNORED-SLOTS','RESULT-CHUNK','MATCHED-CHUNK-VALUES',
             'MATCHED-VALUES-MAGNITUDES']

similarities_by_time = {}

def choose(items,chances):
    p = chances[0]
    x = random.random()
    i = 0
    while x > p :
        i = i + 1
        p = p + chances[i]
    return items[i]

def access_by_key(key, list):
    '''Assumes key,vallue pairs and returns the value'''
    if not key in list:
        raise KeyError("Key not in list")

    return list[list.index(key)+1]


def y_value(*args):
    print("y_value", args)
    return a*args[0] + b*args[1]# + c*args[2]


def new_blend_request(args):
    '''Add a new time key for similarities'''
    similarities_by_time[actr.get_time()] = []

def similarity(val1, val2):
    '''Linear tranformation, abslute difference'''
    if val1 == None:
        return None
    max_val = 1#max(map(max, zip(*feature_sets)))
    min_val = 0#min(map(min, zip(*feature_sets)))
    print("max,min,val1,val2",max_val,min_val,val1,val2)
    val1_t = (((val1 - min_val) * (0 + 1)) / (max_val - min_val)) + 0
    val2_t = (((val2 - min_val) * (0 + 1)) / (max_val - min_val)) + 0
    #print("val1_t,val2_t", val1_t, val2_t)
    #print("sim returning", abs(val1_t - val2_t) * -1)
    #print("sim returning", ((val1_t - val2_t)**2) * - 1)
    #return float(((val1_t - val2_t)**2) * - 1)
    #return abs(val1_t - val2_t) * - 1
    #return 0
    #print("sim returning", abs(val1_t - val2_t) * - 1)
    #return abs(val1_t - val2_t) * -1
    print("sim returning", (abs(val1 - val2) * - 1)/max_val)
    return (abs(val1 - val2) * - 1)/max_val

    print("sim returning", abs(val1 - val2) / (max_val - min_val) * - 1)
    return abs(val1 - val2) / (max_val - min_val) * - 1


actr.add_command('similarity_function',similarity)
#actr.add_command('new_blend_request', new_blend_request)
actr.load_act_r_model("/Users/paulsomers/blendingtests/key-door-box.lisp")
actr.record_history("blending-trace")



#actions
#not sure if this makes sense. The actions are cetegorical.
#0 = go for key
#1 = go for box
#2 = go for door
#no, this makes no sense because





#some prototype chunks
chks =[]

chks.append(['isa', 'decision', 'key_visible', 1,
          'has_key', 0, 'door_visible', 1, 'goto_door', 0, 'get_key', 1])

chks.append(['isa', 'decision', 'key_visible', 1,
          'has_key', 1, 'door_visible', 1, 'goto_door', 1, 'get_key', 0])


for x in chks:
    actr.add_dm(x)




#a probe
chk = ['isa', 'observation', 'key_visible', 1, 'has_key', 1, 'door_visible', 1]
chunk = actr.define_chunks(chk)
actr.schedule_simple_event_now("set-buffer-chunk",
                               ['imaginal', chunk[0]])
actr.run(10)

d = actr.get_history_data("blending-trace")
d = json.loads(d)

asdf = actr.get_history_data("blending-times")


def compute_S(blend_trace, keys_list):
    '''For blend_trace @ time'''
    #probablities
    probs = [x[3] for x in access_by_key('MAGNITUDES',access_by_key('SLOT-DETAILS',blend_trace[0][1])[0][1])]
    #feature values in probe
    FKs = [access_by_key(key.upper(),access_by_key('RESULT-CHUNK',blend_trace[0][1])) for key in keys_list]
    chunk_names = [x[0] for x in access_by_key('CHUNKS', blend_trace[0][1])]

    #Fs is all the F values (may or may not be needed for tss)
    #They are organized by chunk, same order as probs
    vjks = []
    for name in chunk_names:
        chunk_fs = []
        for key in keys_list:
            chunk_fs.append(actr.chunk_slot_value(name,key))
        vjks.append(chunk_fs)

    #tss is a list of all the to_sum
    #each to_sum is Pj x dSim(Fs,vjk)/dFk
    #therefore, will depend on your similarity equation
    #in this case, we need max/min of the features because we use them to normalize
    max_val = 1#max(map(max, zip(*feature_sets)))
    min_val = 0#min(map(min, zip(*feature_sets)))
    n = max_val - min_val
    n = max_val
    #n = 1
    #this case the derivative is:
    #           Fk > vjk -> -1/n
    #           Fk = vjk -> 0
    #           Fk < vjk -> 1/n
    #compute Tss
    #there should be one for each feature
    #you subtract the sum of each according to (7)
    tss = {}
    ts2 = []
    for i in range(len(FKs)):
        if not i in tss:
            tss[i] = []
        for j in range(len(probs)):
            if FKs[i] > vjks[j][i]:
                dSim = -1/n
            elif FKs[i] == vjks[j][i]:
                dSim = 0
            else:
                dSim = 1/n
            tss[i].append(probs[j] * dSim)
        ts2.append(sum(tss[i]))

    #vios
    viosList = []
    viosList.append([actr.chunk_slot_value(x,'get_key') for x in chunk_names])
    viosList.append([actr.chunk_slot_value(x, 'goto_door') for x in chunk_names])

    #compute (7)
    rturn = []
    for vios in viosList:
        results = []
        for i in range(len(FKs)):
            tmp = 0
            sub = []
            for j in range(len(probs)):
                if FKs[i] > vjks[j][i]:
                    dSim = -1/n
                elif FKs[i] == vjks[j][i]:
                    dSim = 0
                else:
                    dSim = 1/n
                tmp = probs[j] * (dSim - ts2[i]) * vios[j]#sum(tss[i])) * vios[j]
                sub.append(tmp)
            results.append(sub)

        print("compute S complete")
        rturn.append(results)
    return rturn


   #print("compute_S complete")





#compute S(Vo,Fk)
#Sum(P * der/wrt-k)

#get the probabilities from the trace
#Assumes the right structure from the list (may need to find another way)
#list of chunks with probabilities ['CHUNK', chunk_name, 'probability', p_value, 'value', value, 'increment', increment']

#for chunk_trace in access_by_key('MAGNITUDES',access_by_key('SLOT-DETAILS',d[0][1])[0][1]):
    #need the derivative of the similarity equation
    #similarity is (roughly) |x - y|
    # x - y
    #-------
    #|y - x|    #wolframalpha
#    pass
# #ordered probablities
# probs = [x[3] for x in access_by_key('MAGNITUDES',access_by_key('SLOT-DETAILS',d[0][1])[0][1])]
# #can get the feature values from the result-chunk as it will be the same as the probe chunk
# F1K = access_by_key('F1',access_by_key('RESULT-CHUNK',d[0][1]))
# #have to get the f-values for each chunk manually, by name
# #chunk_names has the same order as probs. zip them if needed.
# chunk_names = [x[0] for x in access_by_key('CHUNKS',d[0][1])]
# #now get the f1 values for each chunks
# f1s = [actr.chunk_slot_value(x,'f1') for x in chunk_names]
# #Pj * dSim(Fk,vjk) 'Pj'
# to_sum = [p*((F1K - y)/abs(F1K - y)) for p,y in zip(probs,f1s)]
# sumPj = sum(to_sum)
# #get MP
MP = actr.get_parameter_value(':mp')
# #get t
t = access_by_key('TEMPERATURE',d[0][1])
# #the values
# vs = [actr.chunk_slot_value(x,'value') for x in chunk_names]
#
factors = ['key_visible', 'has_key', 'door_visible']
#factors = ['needsFood', 'needsWater']
result_factors = ['get_key', 'goto_door']
#result_factors = ['food','water']
results = compute_S(d, factors)#,'f3'])
for sums,result_factor in zip(results,result_factors):
    print("For", result_factor)
    for s,factor in zip(sums,factors):
        print(factor, MP/t * sum(s))

print("actual value is", actr.chunk_slot_value('OBSERVATION0','ACTUAL'))

print("done")


