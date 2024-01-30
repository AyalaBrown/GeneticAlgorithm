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
    c1 = p1.deepcopy()
    c2 = p2.deepcopy()
    length = min(len(p1.position), len(p2.position))
    num_of_solutions = length/7
    crossSite1 = np.random.randint(0, num_of_solutions/2)*7
    crossSite2 = np.random.randint(num_of_solutions/2, num_of_solutions)*7

    for i in range(0, length):
        if i >=crossSite1 and i <= crossSite2:
            c1.position[i] = p2.position[i]
            c2.position[i] = p1.position[i]
        else:
            c1.position[i] = p1.position[i]
            c2.position[i] = p2.position[i]
    
    return c1, c2

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