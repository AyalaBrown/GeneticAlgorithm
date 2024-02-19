import numpy as np
from ypstruct import structure
import convertions
import initializations
import random
import initialPopulation
import max_price
import test
from collections import defaultdict, deque

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
    
    # min = 0, max = all the chargers are charging all the time. 
    min_cost = 0
    max_cost = max_price.max_price()

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
            if c1 == None:
                print("After crossover")

            # Perform Mutation
            c2 = mutate(p1)
            if c2 == None:
                print("After mutation")

            c3 = mutate(p2)
            if c3 == None:
                print("After mutation")


            # print(len(p1.position)/7, len(p2.position)/7, len(c1.position)/7, len(c2.position)/7, len(c3.position)/7)

            # Add Offspring to popc
            popc.append(c1)
            popc.append(c2)   
            popc.append(c3)

        for Offspring in popc:
            # Evaluate Offspring
            if Offspring == None:
                print(Offspring)
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
    offspring = p1.deepcopy() # Create a copy of the first parent
    offspring.position = None

    data = initializations.getFunctionInputsDB()
    chargers  =  data['chargers']
    busses = data['busses']
    ampereLevels = data['amperLevels']
    prices = data['prices']

    chargers_busy = {}  # Dictionary to track busy chargers and their schedules

    l = len(p1.position) if len(p1.position) < len(p2.position) else len(p2.position)

    # Randomly select a crossover point
    crossover_point = random.randrange(0, l, 7)

    # Slice the offspring position based on the crossover point
    offspring.position = p1.position[:crossover_point] + p2.position[crossover_point:]

    # Initialize a list to store schedules that need fitting
    schedules_for_fitting = []

    i = 0
    # Iterate through the schedules in the offspring's position
    while i < len(offspring.position):
        schedule = offspring.position[i:i+7]  # Extract the schedule
        # Check if the charger is already busy during the schedule
        if (schedule[0], schedule[1]) in chargers_busy:
            busy_slots = chargers_busy[(schedule[0], schedule[1])]
            overlapping = any(sch['from']+random.randint(10,20) <= schedule[3] and sch['to'] >= schedule[4]+random.randint(10,20) for sch in busy_slots)
            if not overlapping:  # If no overlap, add to busy chargers
                chargers_busy[(schedule[0], schedule[1])].append({'from': schedule[3], 'to': schedule[4]})
                i += 7
            else:  # If overlap, add to schedules for fitting
                schedules_for_fitting.append(schedule)
                offspring.position[i:i+7] = []
        else:  # Charger is not busy, add to busy chargers
            chargers_busy[(schedule[0], schedule[1])] = [{'from': schedule[3], 'to': schedule[4]}]
            i += 7
    # print("schedules for fitting: ", len(schedules_for_fitting))
    # Fit schedules that need fitting into available chargers
            
    # Calculate the total price of each price window
    total_prices = [
        (window['from'], window['to'], sum(price['finalPriceInAgorot'] for price in prices if window['from'] <= price['from'] <= window['to']))
        for window in prices
    ]
    
    # Find the minimum price in the total_prices list
    min_price = min(total_prices, key=lambda x: x[2])[2]

    # Find all tuples with the minimum price
    cheapest_prices = [price for price in total_prices if price[2] == min_price]

    print("-------------------------------------")

    # Extract the time ranges associated with the cheapest prices
    cheapest_price_windows = [(price[0], price[1]) for price in cheapest_prices]
    for schedule in schedules_for_fitting:
        found = False
        # Now you can use cheapest_price_windows to check if a bus entryTime and exitTime fall within the cheapest price windows
        entry_time = busses[schedule[2]]['entryTime']
        exit_time = busses[schedule[2]]['exitTime']
        # Check if the bus entryTime and exitTime fall within any of the cheapest price windows
        for window in cheapest_price_windows:
            time = schedule[4]-schedule[3]
            if window[0] <= entry_time:
                offspring, found = find_charger(offspring, schedule, entry_time, entry_time+time, chargers_busy, chargers, ampereLevels, busses)
                if offspring == None:
                    print("in window[0] <= entry_time", found)
                if found == True:
                    break
            if window[0] > entry_time and exit_time <= window[1]:
                offspring, found = find_charger(offspring, schedule, exit_time-time, exit_time, chargers_busy, chargers, ampereLevels, busses)
                if offspring == None:
                    print("in window[0] > entry_time and exit_time <= window[1]", found)
                if found == True:
                    break
        if not found:
            offspring, found = find_charger(offspring, schedule, schedule[3], schedule[4], chargers_busy, chargers, ampereLevels, busses)
    if not found:
        print("No charger found:(")
    if offspring == None:
        print("None", found)
    return offspring
        
def find_charger(offspring, schedule, start, end, chargers_busy, chargers, ampereLevels, busses):
    found = False
    for charger, busy_slots in chargers_busy.items():
        overlapping = any(sch['from']+random.randint(600000,1200000) <= start and sch['to'] >= end+random.randint(600000,1200000) for sch in busy_slots)
        if not overlapping and schedule[6] <= chargers[charger]['ampere']:
            chargers_busy[charger].append({'from': start, 'to': end})
            schedule[0], schedule[1] = charger
            schedule[3], schedule[4] = start, end
            offspring.position += schedule
            found = True
            break
    
    ampereLevel = 0
    for i in range(0, len(ampereLevels)):
        if ampereLevels[i]['low'] < schedule[5] < ampereLevels[i]['high']:
            ampereLevel = i
            break
    ampereLevel+=1
    while not found and ampereLevel<5:
        time = initialPopulation.charging_time(ampereLevel+1,schedule[2])
        if busses[schedule[2]]['exitTime'] - busses[schedule[2]]['entryTime'] >= time:
            start = busses[schedule[2]]['entryTime']
            end = busses[schedule[2]]['entryTime']+time
            for charger, busy_slots in chargers_busy.items():
                overlapping = any(sch['from']+random.randint(600000,1200000) <= start and sch['to'] >= end+random.randint(600000,1200000) for sch in busy_slots)
                if not overlapping and ampereLevels[ampereLevel]['avgAmpere'] <= chargers[charger]['ampere']:
                    chargers_busy[charger].append({'from': start, 'to': end})
                    schedule[0], schedule[1] = charger
                    schedule[3], schedule[4], schedule[5] = start, end, ampereLevels[ampereLevel]['avgAmpere']
                    offspring.position += schedule
                    found = True
                    break  
        ampereLevel+=1
    if not found:
        for charger in chargers:
            if charger not in chargers_busy:
                chargers_busy[charger] = []
                chargers_busy[charger].append({'from': start, 'to': end})
                schedule[0], schedule[1] = charger
                schedule[3], schedule[4] = start, end
                offspring.position += schedule
                found = True
                break
    return offspring, found


def _crossover2(p1, p2):
    offspring = p1.deepcopy() # Create a copy of the first parent
    offspring.position = None

    data = initializations.getFunctionInputsDB()
    chargers  =  data['chargers']
    busses = data['busses']
    ampereLevels = data['amperLevels']

    chargers_busy = {}  # Dictionary to track busy chargers and their schedules

    l = len(p1.position) if len(p1.position) < len(p2.position) else len(p2.position)

    # Randomly select a crossover point
    crossover_point = random.randrange(0, l, 7)

    # Slice the offspring position based on the crossover point
    offspring.position = p1.position[:crossover_point] + p2.position[crossover_point:]

    # Initialize a list to store schedules that need fitting
    schedules_for_fitting = []

    i = 0
    # Iterate through the schedules in the offspring's position
    while i < len(offspring.position):
        schedule = offspring.position[i:i+7]  # Extract the schedule
        # Check if the charger is already busy during the schedule
        if (schedule[0], schedule[1]) in chargers_busy:
            busy_slots = chargers_busy[(schedule[0], schedule[1])]
            overlapping = any(sch['from']+random.randint(10,20) <= schedule[3] and sch['to'] >= schedule[4]+random.randint(10,20) for sch in busy_slots)
            if not overlapping:  # If no overlap, add to busy chargers
                chargers_busy[(schedule[0], schedule[1])].append({'from': schedule[3], 'to': schedule[4]})
                i += 7
            else:  # If overlap, add to schedules for fitting
                schedules_for_fitting.append(schedule)
                offspring.position[i:i+7] = []
        else:  # Charger is not busy, add to busy chargers
            chargers_busy[(schedule[0], schedule[1])] = [{'from': schedule[3], 'to': schedule[4]}]
            i += 7
    # print("schedules for fitting: ", len(schedules_for_fitting))
    # Fit schedules that need fitting into available chargers
    for schedule in schedules_for_fitting:
        found = False
        for charger, busy_slots in chargers_busy.items():
            overlapping = any(sch['from']+random.randint(600000,1200000) <= schedule[3] and sch['to'] >= schedule[4]+random.randint(600000,1200000) for sch in busy_slots)
            if not overlapping and schedule[6] <= chargers[charger]['ampere']:
                chargers_busy[charger].append({'from': schedule[3], 'to': schedule[4]})
                schedule[0], schedule[1] = charger
                offspring.position += schedule
                found = True
                break
        
        ampereLevel = 0
        for i in range(0, len(ampereLevels)):
            if ampereLevels[i]['low'] < schedule[5] < ampereLevels[i]['high']:
                ampereLevel = i
                break
        ampereLevel+=1
        while not found and ampereLevel<5:
            time = initialPopulation.charging_time(ampereLevel+1,schedule[2])
            if busses[schedule[2]]['exitTime'] - busses[schedule[2]]['entryTime'] >= time:
                start = busses[schedule[2]]['entryTime']
                end = busses[schedule[2]]['entryTime']+time
                for charger, busy_slots in chargers_busy.items():
                    overlapping = any(sch['from']+random.randint(10,20) <= start and sch['to'] >= end+random.randint(10,20) for sch in busy_slots)
                    if not overlapping and ampereLevels[ampereLevel]['avgAmpere'] <= chargers[charger]['ampere']:
                        chargers_busy[charger].append({'from': start, 'to': end})
                        schedule[0], schedule[1] = charger
                        schedule[3], schedule[4], schedule[5] = start, end, ampereLevels[ampereLevel]['avgAmpere']
                        offspring.position += schedule
                        found = True
                        break  
            ampereLevel+=1
        if not found:
            for charger in chargers:
                if charger not in chargers_busy:
                    chargers_busy[charger] = []
                    chargers_busy[charger].append({'from': schedule[3], 'to': schedule[4]})
                    schedule[0], schedule[1] = charger
                    offspring.position += schedule
                    found = True
                    break
        if not found:
            print("didnt found charger :(")
    return offspring

def _crossover(p1, p2):
    offspring = p1.deepcopy()
    offspring.position = None

    data = initializations.getFunctionInputsDB()
    chargers  =  data['chargers']
    buses = data['busses']

    # Randomly select a charger index
    charger_index = random.randrange(0, len(p1.position), 7)

    chargers_busy = {}
    schedulesForFitting = []
    buses_busy = []

    offspring.position = p1.position[:(charger_index+7)]

    # Running on the offspring and keeping the buses in it and the schedules
    for i in range(0 , len(offspring.position), 7):
        schedule = offspring.position[i:i+7]
        buses_busy.append(schedule[2])
        if (schedule[0], schedule[1]) in chargers_busy.keys():
            chargers_busy[(schedule[0], schedule[1])].append({'from':schedule[3], 'to':schedule[4]})
        else:
            chargers_busy[(schedule[0], schedule[1])] = [{'from':schedule[3], 'to':schedule[4]}]

    for charger in chargers.keys():
        if charger not in chargers_busy.keys():
                chargers_busy[(charger)] = []

    s_chargers_busy = dict(sorted(chargers_busy.items(), key=lambda x: len(x[1]), reverse=True))

    # Running on P2
    for i in range(0, len(p2.position), 7):
        schedule = p2.position[i:i+7]
        # If the bus alredy exists in the buses_busy, continue to the next 
        if schedule[2] in buses_busy:
            continue
        
        buses_busy.append(schedule[2])

        # If the schedule's charger not exists in the chargers_busy - adding the schedule to the offspring.position
        if len(s_chargers_busy[(schedule[0], schedule[1])]) == 0:
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
        if found:
            continue

        schedulesForFitting.append(schedule)

    if len(schedulesForFitting)>0:
        print("len of schedulesForFitting:", len(schedulesForFitting))
        # cheking for another charger for the schedules are overlap on the chargers
        for schedule in schedulesForFitting:
            print("Running on schedulesForFitting", schedule)
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
                        if found:
                            break
                    else:
                        # rand a new ampere that is good for the charger
                        ampere, ampereLevel = initialPopulation.rand_ampere(chargers[charger]['ampere'])
                        time = initialPopulation.charging_time(ampereLevel, schedule[2])
                        bus = schedule[2]
                        # if the bus have no time for charging in the ampere of the charger - cheking for another charger
                        while buses[bus]['exitTime'] - buses[bus]['entryTime'] < time:
                            _ampere, _ampereLevel = initialPopulation.faster(ampereLevel, chargers[charger]['ampere'])
                            if _ampere == False or _ampereLevel == ampereLevel:
                                found = False
                                break
                            time = initialPopulation.charging_time(_ampereLevel, schedule[2])
                            ampere, ampereLevel = _ampere, _ampereLevel
                            found = True
                        if not found:
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
                        if found:
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