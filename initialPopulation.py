import initializations
import random
import readingFromDb
import logging
import time

inputs = initializations.getFunctionInputsDB()
busses = inputs["busses"]
prices = inputs["prices"]
chargers = inputs["chargers"]
maxPower = inputs["maxPower"]
amperLevels = inputs["amperLevels"]

logging.basicConfig(filename='init_pop.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def init_pop(npop):
    init_pop = readingFromDb.read_init_pop('20240107', npop)
    pop = []
    for i in range(npop):
        print(init_pop)
        filtered_init_pop = init_pop[init_pop['solutionCode'] == i+1]
        sol = filtered_init_pop.drop(columns=['solutionCode']).to_dict(orient='records')
        pop.append(sol)
        print(f"Added solution {i+1}")
        logging.info(f"Added solution {i+1}")
    return pop

def _init_pop(npop):
    busses_keys = list(busses.keys())
    chargers_keys = list(chargers.keys())
    pop = []
    for i in range(npop):
        random.shuffle(busses_keys)
        random.shuffle(chargers_keys)
        sol = [] # solution
        chargers_busy = {key: [] for key in chargers_keys} # list of charging for each cherger
        charger_ind = 0
        for bus in busses_keys: # run on each bus for fining free charger
            found_charger = False
            while found_charger==False:
                charger = chargers_keys[charger_ind]
                chargerAmpere = chargers[charger]["ampere"] # random ampere that suitable for the charger
                ampere, ampereLevel = rand_ampere(chargerAmpere)
                t = charging_time(ampereLevel, bus)
                while busses[bus]['exitTime']-busses[bus]['entryTime'] < t:
                    ampere = faster(ampereLevel, chargerAmpere)
                    if ampere == False:
                        break
                    t = charging_time(ampere, bus)
                if ampere == False:
                    break
                interval = random.randint(10, 20)*60000
                if len(chargers_busy[charger]) == 0:
                    start_time = busses[bus]['entryTime']
                    end_time = busses[bus]['entryTime']+t
                    sol.append(append_schedule(chargers_busy, int(start_time), int(end_time), ampere, bus, charger))
                    found_charger = True
                elif len(chargers_busy[charger])>0:
                    chargers_busy[charger] = sorted(chargers_busy[charger], key=lambda x: x['start_time'])
                    start = chargers_busy[charger][0]['start_time']
                    for i in range(1,len(chargers_busy[charger])):
                        end = chargers_busy[charger][i]['end_time']
                        if t <= (end-interval)-(start+interval) and busses[bus]['entryTime'] <= start+interval and start+interval+t <= busses[bus]['exitTime']:
                            start_time = start+interval
                            end_time = start+interval+t
                            sol.append(append_schedule(chargers_busy, int(start_time), int(end_time), ampere, bus, charger))
                            found_charger = True
                            break
                if charger_ind == len(chargers_keys)-1:
                    charger_ind = 0
                else:
                    charger_ind+=1
                logging.info(f"Processed bus {bus} and charger {charger} at {time.time()}")
        pop.append(sol)
        print(sol)
        print(f"Added solution {i}")
        logging.info(f"Added solution {i}")
    print(pop)
    return pop

def calculate_schedule_price(ampere, startTime, endTime, prices, voltage):
    if endTime<startTime:
        print("end smaller then start")
    sorted_prices = sorted(prices, key=lambda x: x['from'])
    price = 0
    for k in range(0, len(prices)):
        if endTime == None:
            print(ampere, startTime, endTime, prices, voltage)
        if (startTime >= sorted_prices[k]['from'] and startTime<prices[k]['to']) or price > 0:
            if endTime <= sorted_prices[k]['to']:
                price += sorted_prices[k]['finalPriceInAgorot'] * ampere * (endTime - startTime)/1000./60./60. * voltage/1000
                return price
            else:
                if price == 0:
                    price = ampere * voltage/1000 * sorted_prices[k]['finalPriceInAgorot'] * (sorted_prices[k]['to'] - startTime)/1000./60./60.
                else:
                    price += sorted_prices[k]['finalPriceInAgorot'] * ampere * (sorted_prices[k]['to'] - sorted_prices[k]['from'])/1000./60./60. * voltage/1000
    return price

def calculate_solution_price(solution):
    final_price = 0
    for i in range(0, len(solution), 7):
        _, _, _, _, _, _, price = solution[i:i+7] 
        final_price += price
    return final_price

def rand_ampere(chargerAmpere):
    max_ampere_level = 1 # the lowest level
    for i in range(0, 5):
        if amperLevels[i]["low"] <= chargerAmpere and chargerAmpere <= amperLevels[i]["high"]:
            max_ampere_level = i+1
            break
    ampereLevel = amperLevels[random.randint(max_ampere_level, 5)-1]
    ampere = ampereLevel["low"]+(ampereLevel["high"]-ampereLevel["low"])/2
    return ampere, ampereLevel['levelCode']

def charging_time(ampereLevel, bus):
    return readingFromDb.getChargingTime(bus, ampereLevel, busses[bus]["socStart"], busses[bus]["socEnd"])

def faster(ampereLevel, chargerAmpere):
    if ampereLevel == 1:
        return False, False 
    new_ampere = amperLevels[ampereLevel-1]["low"]+(amperLevels[ampereLevel-1]["high"]-amperLevels[ampereLevel-1]["low"])/2
    if(new_ampere < chargerAmpere):
        return new_ampere, ampereLevel-1
    return chargerAmpere, ampereLevel

def append_schedule(chargers_busy, start_time, end_time, ampere, bus, charger):
    chargers_busy[charger].append({'start_time':start_time , 'end_time': end_time})
    price = calculate_schedule_price(ampere, start_time, end_time, prices, chargers[charger]["voltage"])
    return {"chargerCode": charger[0], "connectorId": charger[1], "trackCode": bus, "startTime": start_time, "endTime":end_time, "ampere": ampere, "price": price}

# pop = init_pop(10)
# print(pop)
