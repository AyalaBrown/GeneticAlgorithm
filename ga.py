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
            # c1, c2 = crossover(p1, p2)

            # Perform Mutation
            c1 = mutate(p1)
            c2 = mutate(p2)

            curr_price = initialPopulation.calculate_solution_price(c1.position)
            if curr_price > max_cost:
                max_cost = curr_price
            if curr_price < min_cost:
                min_cost = curr_price
            
            curr_price = initialPopulation.calculate_solution_price(c2.position)
            if curr_price > max_cost:
                max_cost = curr_price
            if curr_price < min_cost:
                min_cost = curr_price

            # Add Offspring to popc
            popc.append(c1)
            popc.append(c2)   

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

    data = initializations.getFunctionInputsDB()
    chargers  =  data['chargers']
    buses = data['busses']

    # Randomly select a charger index
    charger_index = random.randrange(0, len(p1), 7)

    chargers_busy = {}
    buses_busy = []

    offspring = p1[:charger_index+7]

    # Running on the offspring and keeping the buses in it and the schedules
    for i in range(0 + len(offspring), 7):
        schedule = offspring[i:i+7]
        buses_busy.append(schedule[2])
        if (schedule[0], schedule[1]) in chargers_busy.keys():
            chargers_busy[(schedule[0], schedule[1])].append({'from':schedule[3], 'to':schedule[4]})
        else:
            chargers_busy[(schedule[0], schedule[1])] = [{'from':schedule[3], 'to':schedule[4]}]

    # Running on P2
    for i in range(0 + len(p2), 7):
        schedule = p1[i:i+7]

        # If the bus alredy exists in the buses_busy, continue to the next 
        if schedule[2] in buses_busy:
            continue
        
        buses_busy.append(schedule[2])

        # If the schedule's charger not exists in the chargers_busy - adding the schedule to the offspring
        if (schedule[0], schedule[1]) not in chargers_busy.keys():
            chargers_busy[(schedule[0], schedule[1])] = [{'from': schedule[3], 'to': schedule[4]}]
            offspring.append(schedule)
            continue

        # The charger is alredy in the list - 
        # cheking if this charging and the existing chargings are overlap in time
        # If not - adding the charging to the charger.
        chargers_busy[(schedule[0], schedule[1])].sort(key = lambda x: x['start'])
        found = False
        start = 0
        for j in chargers_busy[(schedule[0], schedule[1])]:
            end = j['start']
            if schedule[3] >= start and schedule[4] <= end:
                chargers_busy[(schedule[0], schedule[1])].append({'from': schedule[3], 'to': schedule[4]})
                offspring.append(schedule)
                found = True
                break
        if found == True:
            continue

        # else - cheking for another charger
        for charger in chargers.keys():
            
            # if the charger dosen't exists in charers_busy - adding the charging to the charger...
            if charger not in chargers_busy.keys():

                # if the ampere of the schedule possibile in this charger - adding the schedule to this charger
                if schedule[6]<= chargers[charger]['ampere']:
                    chargers_busy[charger] = ({'from': schedule[3], 'to': schedule[4]})
                    schedule[0] = charger[0]
                    schedule[1] = charger[1]
                    offspring.append(schedule)
                    found = True
                    break
                # else - rand another ampere
                else:
                    ampere, ampereLevel = initialPopulation.rand_ampere(chargers[charger]['ampere'])
                    time = initialPopulation.charging_time(ampereLevel, schedule[2])
                    


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