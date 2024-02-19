import initializations
from collections import defaultdict

def fitness(solution, min_cost, max_cost):
    # try:
    data = initializations.getFunctionInputsDB()
    busses = data["busses"]
    chargers = data["chargers"]
    maxPower = data["maxPower"]
    capacity = data["capacity"]
    ampereLevels = {level["levelCode"]: {"low": level["low"], "high": level["high"], } for level in data["amperLevels"]}

    # Correctness:
    # A bus is scheduled to charge while it is in the parking lot & There are not conflicts between busses and chargers
    # A bus charging enough for it's tasks
    # The ampere in each charger dosent over the max ampere of the charger

    # Constraints:
    # constraint 1 - The total consumption of the ampere in the parking lot not exceeds the max ampere.
    # constraint 2 - Prefer the cheapest plan.
    # constraint 3 - Charging as little as possible at the high level.
    # constraint 4 - The time interval between different loads on the same charger is as large as possible.

    # Weights:
    # constraint 1 
    w1 = 0.50
    # constraint 2
    w2 = 0.35
    # constraint 3
    w3 = 0.15
    # constraint 4
    w4 = 0.10

    # Parameters:
    # constraint 1 
    start_ampere_list = []
    end_ampere_list = []
    cost1 = 0
    # constraint 2
    financial_cost = 0
    cost2 = 0
    # constraint 3
    level1 = 0
    level2 = 0
    cost3 = 0
    # constraint 4
    chargers_busy = defaultdict(list)
    slots = 0

    sum_of_schedules = 0

    for i in range(0, len(solution), 7):
        sum_of_schedules+=1
        chargerCode, connectorId, bus_code, start_time, end_time, ampere, price = solution[i:i+7] 
        chargers_busy[(chargerCode, connectorId)].append({'from': start_time, 'to': end_time})
        voltage = 0
        if (chargerCode, connectorId) in chargers:
            voltage = chargers[(chargerCode, connectorId)]["voltage"]

        # constraint 1
        start_ampere_list.append({'start_time': start_time, 'ampere': ampere, 'voltage': voltage})
        end_ampere_list.append({'end_time': end_time, 'ampere': ampere, 'voltage': voltage})
 
        # constraint 2
        financial_cost += price

        # constraint 3
        if ampereLevels[5]["low"] <= ampere and ampere <= ampereLevels[4]["high"]:
            level1+=1
        if ampereLevels[3]["low"] <= ampere and ampere <= ampereLevels[2]["high"]:
            level2+=1

    # constraint 4
    for i in chargers_busy:
        if len(chargers_busy[i]) > 1:
            start = chargers_busy[i][0]['to']
            for j in range(1, len(chargers_busy[i])):
                end = chargers_busy[i][j]['from']
                slot = end-start
                if slot > 1200000:
                    slot = 1200000
                if slot < 600000:
                    slot = 600000
                slots += (slot-600000)/(1200000-600000)


    cost1 = w1*calculate_cost_3(start_ampere_list, end_ampere_list, maxPower)
    cost2 = w2*(financial_cost-min_cost)/(max_cost-min_cost)
    cost3 = w3*(level1/sum_of_schedules+0.5*level2/sum_of_schedules)
    cost4 = w4*(slots/sum_of_schedules)
    print("cost1, cost2, cost3, cost4", cost1, cost2, cost3, cost4)
    total_cost = cost1 + cost2 + cost3 + cost4

    return total_cost
    # except Exception as e:
    #     print("error!!!!!!!!", e)
    #     return

def calculate_cost_3(start_ampere_list, end_ampere_list, maxPower):
    total_power = 0 
    good = 0
    not_good = 0
    merged_list = start_ampere_list + end_ampere_list

    def custom_key(item):
        if 'start_time' in item:
            return item['start_time']
        elif 'end_time' in item:
            return item['end_time']
        else:
            return float('inf')
        
    sorted_merged_list = sorted(merged_list, key=custom_key)

    for i in range(0, len(sorted_merged_list)):
        if 'start_time' in sorted_merged_list[i]:
            total_power += sorted_merged_list[i]['ampere']*sorted_merged_list[i]['voltage']
            if total_power > maxPower:
                not_good+=1
            else:
                good+=1
        else: 
            total_power -= sorted_merged_list[i]['ampere']*sorted_merged_list[i]['voltage']
    return not_good/(good+not_good)

'''
# constraint 1
cost1 = 0
good1 = 0
not_good1 = 0
# constraint 2
cost2 = 0
good2 = 0
not_good2 = 0
# constraint 4
busses_charge = {}
cost4 = 0
good4 = 0
not_good4 = 0
# constraint 7
chargers_bussy = {charger[0]:{"maxAmpere": chargers[charger]["ampere"], "chargings":[]} for charger in chargers.keys()}
good7 = 0
not_good7 = 0

for bus in busses.keys():
    busses_charge[bus] = {'charge': busses[bus]['socStart'],'soc_start': busses[bus]['socStart'], 'soc_end': busses[bus]['socEnd']}

# constraint 1
if start_time > end_time:
    not_good1+=1
else:
    if bus_code in busses:
        start = busses[bus_code]["entryTime"]
        end = busses[bus_code]["exitTime"]
        if start <= start_time and end_time <= end:
            good1+=1
        else:
            not_good1+=1

# constraint 2 
for j in range(i+7, len(solution), 7):
    chargerCode2, connectorId2, bus_code2, start_time2, end_time2, _, _ = solution[j:j+7] 
    if bus_code == bus_code2 and start_time <= end_time2 and end_time >= start_time2:
        not_good2+=1
    else:
        good2+=1
    if chargerCode == chargerCode2 and connectorId == connectorId2 and start_time <= end_time2 and end_time >= start_time2:
        not_good2+=1
    else:
        good2+=1


# constraint 4
if bus_code not in busses_charge.keys():
    raise Exception("Bus code not found")
charging_time = end_time - start_time
if bus_code in capacity:
    busses_charge[bus_code]['charge']+= charging_time/1000/60*ampere*voltage/1000/capacity[int(bus_code)]
       

# constraint 7
chargers_bussy[chargerCode]["chargings"].append({"time": start_time, "type": "start", "ampere": ampere})
chargers_bussy[chargerCode]["chargings"].append({"time": end_time, "type": "end", "ampere": ampere})

for bus in busses_charge:
    if busses_charge[bus]['charge'] > 95 or busses_charge[bus]['charge'] < busses_charge[bus]['soc_end']:
        # print(busses_charge[bus]['charge'], busses_charge[bus]['soc_end'])
        not_good4+=1
    else:
        good4+=1


for charger in chargers_bussy:
    if len(chargers_bussy[charger]["chargings"]) > 0:
        chargers_bussy[charger]["chargings"] = sorted(chargers_bussy[charger]["chargings"], key=lambda x: x["time"])
        currAmpere = 0 
        maxAmpere = chargers_bussy[charger]["maxAmpere"]
        for charging in chargers_bussy[charger]["chargings"]:
            if charging["type"] == "start":
                currAmpere+=charging["ampere"] 
                if currAmpere>maxAmpere:
                    not_good7+=1
                else:
                    good7+=1
            else:
                currAmpere-=charging["ampere"] 

# print(good1, not_good1)
cost1 = w1*not_good1/(good1+not_good1)
cost2 = w2*not_good2/(good2+not_good2)
cost4 = w4*not_good4/(good4+not_good4)
# print(financial_cost,max_cost,min_cost)
cost7 = w7*not_good7/(good7+not_good7)
'''

