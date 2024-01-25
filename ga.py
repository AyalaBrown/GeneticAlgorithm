import numpy as np
from ypstruct import structure
import convertions
import initializations
import random
import initialPopulation
import min_max_price

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

    init_pop = convertions.initial_population()

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
            c1, c2 = crossover(p1, p2)

            # Perform Mutation
            c1 = mutate(c1)
            c2 = mutate(c2)

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
    values = initializations.getFunctionInputsDB()["values"]
    while True:
        random_gene_idx = np.random.choice(range(len(offspring.position)))
        param_inx = random_gene_idx % 7
        param_values = values[param_inx]
        if param_values == 'start':
            break
        if param_values == 'end':
            break
        if param_values is not None:
            offspring.position[random_gene_idx] = int(random.choice(param_values))
            break
        
    offspring.position = add_or_remove_schedule(offspring.position)
    return offspring

def roulette_wheel_selection(p):
    c = np.cumsum(p)
    r = sum(p)*np.random.rand()
    ind = np.argwhere(r <= c)
    return ind[0][0]

def add_or_remove_schedule(offspring):
    data = initializations.getFunctionInputsDB()
    busses_charge = {bus: {'charge': data["busses"][bus]['socStart'], 'entryTime': data["busses"][bus]['entryTime'], 'exitTime': data["busses"][bus]['exitTime'],
                                        'soc_start': data["busses"][bus]['socStart'], 'soc_end': data["busses"][bus]['socEnd']}
                     for bus in data["busses"].keys()}
    chargers = data["chargers"]
    amperLevels = data["amperLevels"]
    capacity = data["capacity"]
    chargers_busy = {}
    bus_busy = {}

    # if there is an overflow charger, it will be removed / shorted
    for i in range(0, len(offspring), 7):
        chargerCode, connectorId, bus_code, start_time, end_time, ampere, price = offspring[i:i+7]

        chargers_busy.setdefault((chargerCode, connectorId), []).append({"from": start_time, "to": end_time})
        bus_busy.setdefault(bus_code, []).append({"charger":(chargerCode, connectorId) ,"from": start_time, "to": end_time, "ampere": ampere})

        if bus_code not in busses_charge:
            raise Exception("Bus code not found")

        charging_time = end_time - start_time

        if(end_time < start_time):
            print("before Shorted time - end time < start time")
            print(start_time, end_time, busses_charge[bus_code]['charge'], charging_time)

        # if busses_charge[bus_code]['charge'] >= busses_charge[bus_code]['soc_end']:
        #     print(f"soc start: {busses_charge[bus_code]['soc_start']}, soc end: {busses_charge[bus_code]['soc_end']}, charge: {busses_charge[bus_code]['charge']}")
        #     # print("remove offspring")
        #     offspring = offspring[:i] + offspring[i+7:]
        #     return offspring
        
        e = end_time
        if bus_code in capacity:
            curr_charge = charging_time / 1000 / 60 * ampere * chargers[(chargerCode, connectorId)]["voltage"] / 1000 / capacity[int(bus_code)]
            if (busses_charge[bus_code]['charge'] + curr_charge)> 95:
                if busses_charge[bus_code]['charge'] >= busses_charge[bus_code]['soc_end']:
                    # print(f"soc start: {busses_charge[bus_code]['soc_start']}, soc end: {busses_charge[bus_code]['soc_end']}, charge: {busses_charge[bus_code]['charge']}, curr charge: {curr_charge}")
                    # print("remove offspring")
                    offspring = offspring[:i] + offspring[i+7:]
                    return offspring

                # print("Shorted...")
                end_time = start_time + int(charging_time*(busses_charge[bus_code]['soc_end'] - busses_charge[bus_code]['charge'])/curr_charge)
                if end_time == None:
                    print("Shorted time - end time none")
                    print(start_time, end_time, busses_charge[bus_code]['charge'], curr_charge, charging_time)
                price = initialPopulation.calculate_schedule_price(ampere, int(start_time), int(end_time), data["prices"], chargers[(chargerCode, connectorId)]["voltage"])  
                if(e>start_time and end_time < start_time):
                    print("Shorted time - end time < start time")
                    print(start_time, end_time, busses_charge[bus_code]['charge'], curr_charge, charging_time)
                offspring[i+4] = int(end_time)
                offspring[i+6] = price
                return offspring
            busses_charge[bus_code]['charge']+= curr_charge
    for charger in chargers_busy:
        chargers_busy[charger] = sorted(chargers_busy[charger], key=lambda x: x['from'])
    # if there is an underflow charging to a bus we add a charging to it
    for bus in busses_charge:
        if busses_charge[bus]['charge'] < busses_charge[bus]['soc_end']:
            e = end_time
            chargerCode 
            connectorId
            start_time
            end_time

            # checking if I can extend the current charging time
            # busses_charge[bus]: {'charge': 45.00935488806509, 'entryTime': 1704643140000.0, 'exitTime': 1704685800000.0, 'soc_start': 40.085845947265625, 'soc_end': 62.22853469848633}
            curr_bus_busy = [] # all the chergings of this bus
            if bus in bus_busy:
                curr_bus_busy = bus_busy[bus]
            if len(curr_bus_busy) > 0: # if this bus alredy has at list one charging
                curr_bus_busy = sorted(curr_bus_busy, key=lambda x: x["from"])
                prev_slot_start_bus = busses_charge[bus]['entryTime']
                big_slot_time = structure()
                big_slot_time.time = 0
                big_slot_time.start = 0
                big_slot_time.end = 0
                big_slot_time.bus_schedule_index = 0
                big_slot_time.type = None
                for i in range(0, len(curr_bus_busy)): # checking if there is a slot of time that the charger is empty
                    prev_slot_end_bus = curr_bus_busy[i]["from"]
                    prev_slot_bus = prev_slot_end_bus-prev_slot_start_bus
                    next_slot_start_bus = curr_bus_busy[i]['to']
                    next_slot_end_bus = curr_bus_busy[i+1]['from'] if len(curr_bus_busy)>(i+1) else busses_charge[bus]['exitTime']
                    next_slot_bus = next_slot_end_bus-next_slot_start_bus
                    if prev_slot_bus > big_slot_time.time: # if i have a contigouse time to add to the bus
                        # 'from' and 'to' in chargers and busses
                        curr_charger_schedules = chargers_busy[curr_bus_busy[i]['charger']]
                        slot_start_charger = 0
                        for j in range(0, len(curr_charger_schedules)):
                            slot_end_charger = curr_charger_schedules[j]["from"]
                            if prev_slot_end_bus <= slot_end_charger: # if I can extend the charging to start early
                                start = prev_slot_start_bus if prev_slot_start_bus >= slot_start_charger else slot_start_charger
                                if (prev_slot_end_bus - start) > big_slot_time.time:
                                    # print("biggest slot time")
                                    big_slot_time.start = start
                                    big_slot_time.end = prev_slot_end_bus
                                    big_slot_time.time = big_slot_time.end - big_slot_time.start
                                    big_slot_time.bus_schedule_index = i
                                    big_slot_time.type = 'before'
                                
                            slot_end_charger = curr_charger_schedules[j]["to"] 
                    prev_slot_start_bus = curr_bus_busy[i]["to"]
                    if next_slot_bus > big_slot_time.time:
                        curr_charger_schedules = chargers_busy[curr_bus_busy[i]['charger']]
                        slot_start_charger = 0
                        for j in range(0, len(curr_charger_schedules)):
                            slot_end_charger = curr_charger_schedules[j]["from"]
                            if next_slot_start_bus >= slot_start_charger: # if I can extend the charging to end later
                                end = next_slot_end_bus if next_slot_end_bus <= slot_start_charger else slot_end_charger
                                if (end - next_slot_start_bus) > big_slot_time.time:
                                    # print("biggest slot time")
                                    big_slot_time.start = next_slot_start_bus
                                    big_slot_time.end = end
                                    big_slot_time.time = big_slot_time.end - big_slot_time.start
                                    big_slot_time.bus_schedule_index = i
                                    big_slot_time.type = 'after'
                            slot_end_charger = curr_charger_schedules[j]["to"]

                needed_soc = busses_charge[bus]['soc_end'] - busses_charge[bus]['charge']
                chargerAmpere = chargers[curr_bus_busy[big_slot_time.bus_schedule_index]['charger']]["ampere"]
                max_ampere_level = 1
                for k in range(0, 5):
                    if amperLevels[k]["low"] <= chargerAmpere and chargerAmpere <= amperLevels[k]["high"]:
                        max_ampere_level = k+1
                        break
                for a in range(0,5-max_ampere_level):
                    # print(max_ampere_level, a)
                    ampereLevel = amperLevels[4-a]
                    ampere = ampereLevel["low"]+(ampereLevel["high"]-ampereLevel["low"])/2
                    curr_soc = big_slot_time.time/1000/60*ampere*chargers[curr_bus_busy[big_slot_time.bus_schedule_index]['charger']]["voltage"] / 1000 / capacity[int(bus)]
                    # print(f"curr_soc: {curr_soc}, needed_soc: {needed_soc}")
                    if curr_soc >= needed_soc:
                        ampereLevel = amperLevels[4-a]
                        ampere = ampereLevel["low"]+(ampereLevel["high"]-ampereLevel["low"])/2
                        if ampere == curr_bus_busy[big_slot_time.bus_schedule_index]['ampere']:
                            price = 0
                            if big_slot_time.type=='after':
                                price = initialPopulation.calculate_schedule_price(ampere, int(curr_bus_busy[big_slot_time.bus_schedule_index]["from"]), int(big_slot_time.end), data["prices"], chargers[curr_bus_busy[i]['charger']]["voltage"])  
                            else:
                                price = initialPopulation.calculate_schedule_price(ampere, int(big_slot_time.start), int(curr_bus_busy[big_slot_time.bus_schedule_index]["to"]), data["prices"], chargers[curr_bus_busy[i]['charger']]["voltage"])  
                            for n in range(0, len(offspring), 7):
                                chargerCode, connectorId, bus_code, start_time, end_time, ampere, price = offspring[n:n+7]
                                if chargerCode == curr_bus_busy[big_slot_time.bus_schedule_index]['charger'][0] and connectorId == curr_bus_busy[big_slot_time.bus_schedule_index]['charger'][1] and start_time == curr_bus_busy[big_slot_time.bus_schedule_index]['from'] and end_time == curr_bus_busy[big_slot_time.bus_schedule_index]['to']:
                                    if big_slot_time.type=='after':
                                        offspring[n+4] = int(big_slot_time.end)
                                    else:
                                        offspring[n+3] = int(big_slot_time.start)
                                    offspring[n+6] = price
                                    # print("consecutive")
                                    return offspring
                        else:
                            price = initialPopulation.calculate_schedule_price(ampere, int(big_slot_time.start), int(big_slot_time.end), data["prices"],chargers[curr_bus_busy[i]['charger']]["voltage"])
                            offspring.extend([chargerCode, connectorId, bus, int(big_slot_time.start), int(big_slot_time.end), ampere, price])
                            # print("consecutive")
                            return offspring
            # founding the biggest slot of time
            # print("not consecutive")
            prev_empty_time = structure()
            prev_empty_time.start = busses_charge[bus]["entryTime"]
            prev_empty_time.end = busses_charge[bus]["entryTime"]

            big_empty_time = 0
            if bus in bus_busy:
                bus_busy[bus].sort(key=lambda x: x["from"])
                for busy in bus_busy[bus]:
                    prev_empty_time.end = busy["from"]
                    time = prev_empty_time.end - prev_empty_time.start
                    if time > big_empty_time:
                        big_empty_time = time
                        start_time = prev_empty_time.start
                        end_time = prev_empty_time.end
                    prev_empty_time.start = busy["to"]
                time = busses_charge[bus]["exitTime"] - prev_empty_time.start
                prev_empty_time.end = busses_charge[bus]["exitTime"]
                if time > big_empty_time:
                    big_empty_time = time
                    start_time = prev_empty_time.start
                    end_time = prev_empty_time.end
                if end_time == None:
                    print("No end time", busses_charge[bus]["entryTime"])
                    print(bus_code, start_time, e, ampere)

            else:
                start_time = busses_charge[bus]["entryTime"]
                end_time = busses_charge[bus]["exitTime"]
                if end_time == None:
                    print("No bus exitTime")
                    print(bus_code, start_time, e, ampere)
            # founding a free charger at the free time
            for charger in chargers_busy:
                chargers_busy[charger].sort(key=lambda x: x["from"])
                prev = chargers_busy[charger][0]
                for time in chargers_busy[charger]:
                    if time["from"]>prev["to"]and time["to"]<prev["from"]:
                        chargerCode, connectorId = charger
                        break

            # random ampere
            chargerAmpere = chargers[(chargerCode, connectorId)]["ampere"]
            max_ampere_level = 1
            for i in range(0, 5):
                if amperLevels[i]["low"] <= chargerAmpere and chargerAmpere <= amperLevels[i]["high"]:
                    max_ampere_level = i+1
                    break
            ampereLevel = amperLevels[random.randint(max_ampere_level, 5)-1]
            ampere = ampereLevel["low"]+(ampereLevel["high"]-ampereLevel["low"])/2
            if int(end_time) < int(start_time):
                print("adding charging end_time < start_time")
                print(start_time, end_time, busses_charge[bus_code]['charge'], busses_charge[bus_code]['soc_end'])
            price = initialPopulation.calculate_schedule_price(ampere, int(start_time), int(end_time), data["prices"], chargers[(chargerCode, connectorId)]["voltage"])  
            
            offspring.extend([chargerCode, connectorId, bus, int(start_time), int(end_time), ampere, price])
            break
    return offspring

