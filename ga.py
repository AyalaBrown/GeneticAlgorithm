import numpy as np
from ypstruct import structure
import convertions
import initializations
import random
import initialPopulation
import min_max_price
import test

def run(problem, params):
    # Problem Information
    costfunc = problem.costfunc

    # Parameters
    maxit = params.maxit
    npop = params.npop
    beta = params.beta
    pc = params.pc
    nc = int(np.round(pc*npop/2)*2)

    # Empty Individual Template
    empty_individual = structure()
    empty_individual.position = None
    empty_individual.cost = None
    empty_individual.iteration = None

    # BestSolution Ever Found
    bestsol = empty_individual.deepcopy()
    bestsol.cost = np.inf

    init_pop = convertions.initial_population(npop)

    min_cost, max_cost = min_max_price.min_max_price()
    
    # Initialize Population
    pop = empty_individual.repeat(npop)
    for i in range(0, npop):
        pop[i].position = init_pop[i]
        pop[i].cost = costfunc(pop[i].position, min_cost, max_cost)
        if pop[i].cost < bestsol.cost:
            bestsol = pop[i].deepcopy()
            bestsol.iteration = 0

    # Best Cost Of Iteration
    bestcost = np.empty(maxit)    

    # Main Loop
    for it in range(0, maxit):
        costs = np.array([x.cost for x in pop])
        avg_cost = np.mean(costs)
        if avg_cost != 0:
            costs = costs/avg_cost
        probs = np.exp(-beta*costs)    
        popc = []
        for _ in range(nc//2):

            # Perform Roulette Wheel Selection
            p1 = pop[roulette_wheel_selection(probs)]
            p2 = pop[roulette_wheel_selection(probs)]

            # Perform Crossover
            c1 = crossover(p1, p2)

            # Perform Mutation
            c2 = mutate(p1)
            c3 = mutate(p2)

            # Add Offspring to popc
            popc.append(c1)
            popc.append(c2)   
            popc.append(c3)

        for Offspring in popc:
            # Evaluate Offspring
            Offspring.cost = costfunc(Offspring.position, min_cost, max_cost)
            if Offspring.cost < bestsol.cost:
                bestsol = Offspring.deepcopy()
                bestsol.iteration = it

        # Merge, Sort and Select
        pop += popc
        pop = sorted(pop, key=lambda x: x.cost)
        pop = pop[0:npop]

        # Store Best Cost
        bestcost[it] = bestsol.cost

        # Show Iteration Information
        print("Iteration {}: Best Cost = {}".format(it, bestcost[it]))

    # Output
    out = structure()
    out.pop = pop
    out.bestsol = bestsol
    out.bestsolLen = len(bestsol.position)
    out.bestcost = bestcost
    return out

def crossover(p1, p2):
    offspring = p1.deepcopy()
    offspring.position = None

    data = initializations.getFunctionInputsDB()
    chargers  =  data['chargers']
    buses = data['busses']

    # Randomly select a charger index
    charger_index = random.randrange(0, len(p1.position), 7)

    chargers_busy = {}
    buses_busy = []

    # print(charger_index+7)
    # print(len(p1.position))
    offspring.position = p1.position[:(charger_index+7)]

    # Running on the offspring and keeping the buses in it and the schedules
    for i in range(0 , len(offspring.position), 7):
        schedule = offspring.position[i:i+7]
        buses_busy.append(schedule[2])
        if (schedule[0], schedule[1]) in chargers_busy.keys():
            chargers_busy[(schedule[0], schedule[1])].append({'from':schedule[3], 'to':schedule[4]})
        else:
            chargers_busy[(schedule[0], schedule[1])] = [{'from':schedule[3], 'to':schedule[4]}]

    # print("buses:", buses_busy)
    # print("chargers:",chargers_busy)

    for charger in chargers.keys():
        if charger not in chargers_busy.keys():
                chargers_busy[(charger)] = []

    s_chargers_busy = dict(sorted(chargers_busy.items(), key=lambda x: len(x[1]), reverse=True))

    # Running on P2
    for i in range(0, len(p2.position), 7):
        schedule = p1.position[i:i+7]

        # If the bus alredy exists in the buses_busy, continue to the next 
        if schedule[2] in buses_busy:
            # print("exist")
            continue
        
        buses_busy.append(schedule[2])

        # If the schedule's charger not exists in the chargers_busy - adding the schedule to the offspring.position
        if len(s_chargers_busy[(schedule[0], schedule[1])]) == 0:
            # print('adding charger...')
            s_chargers_busy[(schedule[0], schedule[1])].append({'from': schedule[3], 'to': schedule[4]})
            offspring.position+=schedule
            continue

        # The charger alredy has schedules - 
        # cheking if this charging and the existing chargings are overlap in time
        # If not - adding the charging to the charger.
        s_chargers_busy[(schedule[0], schedule[1])].sort(key = lambda x: x['from'])
        found = False
        start_slot = 0
        for j in s_chargers_busy[(schedule[0], schedule[1])]:
            end_slot = j['from']
            if schedule[3] >= start_slot and schedule[4] <= end_slot:
                s_chargers_busy[(schedule[0], schedule[1])].append({'from': schedule[3], 'to': schedule[4]})
                offspring.position+=schedule
                found = True
                break
            start_slot = j['to']
        if found == True:
            continue

        # else - cheking for another charger
        for charger in s_chargers_busy.keys():
            # if the charger have schedules - cheking if I can add the charging to the charger..
            if len(s_chargers_busy[charger]) > 0:
                # if the ampere of the schedule possibile in this charger - cheking if I can add the charging to the charger..
                if schedule[6]<= chargers[charger]['ampere']: # if the charging amper smaller than the ampre of the charger
                    start_slot = 0
                    for sch in s_chargers_busy[charger]:
                        end_slot = sch['from']
                        if schedule[3] >= start_slot and schedule[4] <= end_slot:
                            s_chargers_busy[charger].append({'from': schedule[3], 'to': schedule[4]})
                            schedule[0] = charger[0]
                            schedule[1] = charger[1]
                            offspring.position+=schedule
                            found = True
                            break
                        start_slot = sch['to']
                    if found == True:
                        break
                else:
                    # rand a new ampere that is good for the charger
                    ampere, ampereLevel = initialPopulation.rand_ampere(chargers[charger]['ampere'])
                    time = initialPopulation.charging_time(ampereLevel, schedule[2])
                    bus = schedule[2]
                    while buses[bus]['exitTime'] - buses[bus]['entryTime'] < time: # if the bus have no time for charging in the ampere of the charger - cheking for another charger
                        _ampere, _ampereLevel = initialPopulation.faster(ampereLevel, chargers[charger]['ampere'])
                        if _ampere == False or _ampereLevel == ampereLevel:
                            found = False
                            break
                        time = initialPopulation.charging_time(_ampereLevel, schedule[2])
                        ampere, ampereLevel = _ampere, _ampereLevel
                        found = True
                    if found == False:
                        continue
                    start_slot = 0
                    for sch in s_chargers_busy[charger]:
                        end_slot = sch['from']
                        if schedule[3] >= start_slot and schedule[4] <= end_slot:
                            s_chargers_busy[charger].append({'from': schedule[3], 'to': schedule[4]})
                            schedule[0] = charger[0]
                            schedule[1] = charger[1]
                            if schedule[3]+time > buses[bus]['exitTime']:
                                schedule[3] = buses[bus]['entryTime']
                            schedule[4] = schedule[3]+time
                            schedule[5] = ampere
                            offspring.position+=schedule
                            found = True
                            break
                        start_slot = sch['to']
                    if found == True:
                        break
            
            # if the charger dosen't have schedules - adding the charging to the charger...
            else:
                # if the ampere of the schedule possibile in this charger - adding the schedule to this charger
                if schedule[6]<= chargers[charger]['ampere']:
                    s_chargers_busy[charger].append({'from': schedule[3], 'to': schedule[4]})
                    schedule[0] = charger[0]
                    schedule[1] = charger[1]
                    offspring.position+=schedule
                    found = True
                    break
                # else - rand another ampere
                else:
                    ampere, ampereLevel = initialPopulation.rand_ampere(chargers[charger]['ampere'])
                    time = initialPopulation.charging_time(ampereLevel, schedule[2])
                    bus = schedule[2]
                    while buses[bus]['exitTime'] - buses[bus]['entryTime'] < time: # if the bus have no time for charging in the ampere of the charger - cheking for another charger
                        _ampere, _ampereLevel = initialPopulation.faster(ampereLevel, chargers[charger]['ampere'])
                        if _ampere == False or _ampereLevel == ampereLevel:
                            found = False
                            break
                        time = initialPopulation.charging_time(_ampereLevel, schedule[2])
                        ampere, ampereLevel = _ampere, _ampereLevel
                        found = True
                    if found == False:
                        continue
                    s_chargers_busy[charger].append({'from': schedule[3], 'to': schedule[4]})
                    schedule[0] = charger[0]
                    schedule[1] = charger[1]
                    if schedule[3]+time > buses[bus]['exitTime']:
                        schedule[3] = buses[bus]['entryTime']
                    schedule[4] = schedule[3]+time
                    schedule[5] = ampere
                    offspring.position+=schedule
                    break
    # print(offspring)
    return offspring

def mutate(x):
    offspring = x.deepcopy()
    data = initializations.getFunctionInputsDB()
    chargers = data['chargers']
    prices = data['prices']
    chargers_busy = {key: [] for key in list(chargers.keys())} # schedules for each charger
    while True:
        i = (np.random.choice(int(len(offspring.position)/7)))*7 # random schedule for change
        charger_code, connector_id, track_code, start_time, end_time, ampere, price = offspring.position[i: i+7]
        maxAmpere = chargers[(charger_code, connector_id)]['ampere']
        _ampere, ampere_level = initialPopulation.rand_ampere(maxAmpere) # new ampere
        if _ampere == ampere: # if the random ampere as before - nothing will change
            break
        time = initialPopulation.charging_time(ampere_level, track_code) # else - the new charging time in the new ampere
        if end_time-start_time >= time: # if the time is shorter than befor - the time is good for the charger
            price = initialPopulation.calculate_schedule_price(_ampere, start_time, start_time+time, prices, chargers[(charger_code, connector_id)]["voltage"])
            if start_time+time<offspring.position[i+3]:
                print(f" 000 time: {time} start time: {start_time} offspring[i+3]: {offspring.position[i+3]}")
            offspring.position[i+4] = start_time+time
            offspring.position[i+5] = _ampere
            offspring.position[i+6] = price
            break
        else:
            for j in range(0, len(offspring.position), 7):
                charger_code1, connector_id1, _, start_time1, end_time1, _, _ = offspring.position[j: j+7]
                chargers_busy[(charger_code1, connector_id1)].append({"start": start_time1, "end": end_time1})
            chargers_busy[(charger_code, connector_id)].sort(key=lambda x:x['start']) # sort the current charger list for running in the good order
            for j in range(len(chargers_busy[(charger_code, connector_id)])): # running on all the charger scheduls
                sch = chargers_busy[(charger_code, connector_id)][j]
                if sch['start'] == start_time: # if I found the current schedule
                    if j+1 == len(chargers_busy[(charger_code, connector_id)]): # if there are no more schedules on the achargers after this - i can extend the charging time
                        price = initialPopulation.calculate_schedule_price(_ampere, start_time, start_time+time, prices, chargers[(charger_code, connector_id)]["voltage"])
                        if start_time+time<offspring.position[i+3]:
                            print(f" 111 time: {time} start time: {start_time} offspring[i+3]: {offspring.position[i+3]}")
                        offspring.position[i+4] = start_time+time
                        offspring.position[i+5] = _ampere
                        offspring.position[i+6] = price
                        break
                    else: # if there are more schedulse after this:
                        # print(sch)
                        next_start = chargers_busy[(charger_code, connector_id)][j+1]['start']
                        if next_start - (start_time+time) >=  600000: # if i have enough time before the next schedule - i can extend this charging
                            price = initialPopulation.calculate_schedule_price(_ampere, start_time, start_time+time, prices, chargers[(charger_code, connector_id)]["voltage"])
                            if start_time+time<offspring.position[i+3]:
                                print(f" 222 time: {time} start time: {start_time} offspring[i+3]: {offspring.position[i+3]}")
                            offspring.position[i+4] = start_time+time
                            offspring.position[i+5] = _ampere
                            offspring.position[i+6] = price
                            break
                        else: # else - I'm checking for anothe charger
                            found = False
                            for c in chargers_busy:
                                if chargers[c]['ampere']>=_ampere:
                                    charger = chargers_busy[c]
                                    if len(charger) == 0: # if there arn't schedules for this charger - I can add this charging
                                        price = initialPopulation.calculate_schedule_price(_ampere, start_time, start_time+time, prices, chargers[(charger_code, connector_id)]["voltage"])
                                        if start_time+time<offspring.position[i+3]:
                                            print(f" 333 time: {time} start time: {start_time} offspring[i+3]: {offspring.position[i+3]}")
                                        offspring.position[i] = c[0]
                                        offspring.position[i+1] = c[1]
                                        offspring.position[i+4] = start_time+time
                                        offspring.position[i+5] = _ampere
                                        offspring.position[i+6] = price
                                        found = True
                                        break
                                    charger.sort(key=lambda x: x['start'])
                                    start = 0
                                    for j in range(len(charger)): # else - 
                                        end = charger[j]['end']
                                        if start < start_time and end > start_time+time:
                                            price = initialPopulation.calculate_schedule_price(_ampere, start_time, start_time+time, prices, chargers[(charger_code, connector_id)]["voltage"])
                                            if start_time+time<offspring.position[i+3]:
                                                print(f" 444 time: {time} start time: {start_time} offspring[i+3]: {offspring.position[i+3]}")
                                            offspring.position[i] = c[0]
                                            offspring.position[i+1] = c[1]
                                            offspring.position[i+4] = start_time+time
                                            offspring.position[i+5] = _ampere
                                            offspring.position[i+6] = price
                                            found = True
                                            break
                                    if found:
                                        break
    return offspring

def roulette_wheel_selection(p):
    c = np.cumsum(p)
    r = sum(p)*np.random.rand()
    ind = np.argwhere(r <= c)
    return ind[0][0]