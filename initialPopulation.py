import initializations
import random

inputs = initializations.getFunctionInputsDB()
busses = inputs["busses"]
prices = inputs["prices"]
chargers = inputs["chargers"]
maxPower = inputs["maxPower"]
amperLevels = inputs["amperLevels"]

def init_pop(npop):
    pop = []
    for i in range(npop):
        busses_keys = list(busses.keys())
        random.shuffle(busses_keys)
        shuffled_busses = {key: busses[key] for key in busses_keys} # random shuffled busses
        chargers_keys = list(chargers.keys())
        random.shuffle(chargers_keys)
        shuffled_chargers = {key: chargers[key] for key in chargers_keys} # random shuffled chargers
        finish = False
        sol = [] # solution
        chargers_busy = {key: {'busy': False, 'schedules': []} for key in chargers_keys} # list of charging for each cherger
        for bus in shuffled_busses: # run on each bus for fining free charger
            for charger in shuffled_chargers: # run to fining free charger to the bus
                charger_key = chargers_keys[charger]

            sol.append({"chargerCode": charger_code, "connectorId": connector_id, "trackCode": j, "startTime": startTime, "endTime": endTime, "ampere": ampere, "price": price})
        pop.append(sol)
        # for j in busses.keys(): # for each bus
        #     if(busses[j]["entryTime"] >0 and busses[j]["exitTime"]>0):
        #         keys_list = list(chargers.keys())
        #         charger_ = random.choice(keys_list)
        #         charger_code = charger_[0]
        #         connector_id =charger_[1]
        #         bus = busses[j]
        #         mid_time = bus["entryTime"]+(bus["exitTime"]-bus["entryTime"])/2
        #         startTime = random.randint(bus["entryTime"], mid_time)
        #         endTime = random.randint(mid_time+1, bus["exitTime"])
        #         if startTime > endTime:
        #             print("initial population - end time > start time")
        #         chargerAmpere = chargers[charger_]["ampere"]
        #         max_ampere_level = 1
        #         for i in range(0, 5):
        #             if amperLevels[i]["low"] <= chargerAmpere and chargerAmpere <= amperLevels[i]["high"]:
        #                 max_ampere_level = i+1
        #                 break
        #         amperLevel = random.randint(max_ampere_level, 5)
        #         ampere = amperLevels[amperLevel-1]["low"]+(amperLevels[amperLevel-1]["high"]-amperLevels[amperLevel-1]["low"])/2
        #         price = calculate_schedule_price(ampere, startTime, endTime, prices, chargers[charger_]["voltage"])

    return pop

def calculate_schedule_price(ampere, startTime, endTime, prices, voltage):
    sorted_prices = sorted(prices, key=lambda x: x["from"])
    price = 0
    for k in range(0, len(prices)):
        if endTime == None:
            print(ampere, startTime, endTime, prices, voltage)
        if (startTime >= sorted_prices[k]["from"] and startTime<prices[k]["to"]) or price > 0:
            if endTime <= sorted_prices[k]["to"]:
                price += sorted_prices[k]["finalPriceInAgorot"]/100 * ampere * (endTime/1000./60./60. - startTime/1000./60./60.) * voltage/1000
                return price
            else:
                if price == 0:
                    price = sorted_prices[k]["finalPriceInAgorot"]/100 * ampere * (sorted_prices[k]["to"]/1000./60./60. - startTime/1000./60./60.) * voltage/1000
                else:
                    price += sorted_prices[k]["finalPriceInAgorot"]/100 * ampere * (sorted_prices[k]["to"]/1000./60./60. - sorted_prices[k]["from"]/1000./60./60.) *voltage/1000
    return price

def calculate_solution_price(solution):
    final_price = 0
    for i in range(0, len(solution), 7):
        _, _, _, _, _, _, price = solution[i:i+7] 
        final_price += price
    return final_price

init_pop(1)