import initializations

def fitness(solution, min_cost, max_cost):
    # try:
    parameters = initializations.getFunctionInputsDB()
    busses = parameters["busses"]
    chargers = parameters["chargers"]
    maxPower = parameters["maxPower"]
    capacity = parameters["capacity"]
    ampereLevels = {level["levelCode"]: {"low": level["low"], "high": level["high"]} for level in parameters["amperLevels"]}

    # constraints
    # constraint 1 - A bus is scheduled to charge while it is in the parking lot
    # constraint 2 - There are not conflicts between busses and chargers
    # constraint 3 - The the total consumption of the ampere in the parking lot not exceeds the max ampere 
    # constraint 4 - A bus charging enough for it's tasks
    # constraint 5 - Prefer the cheapest plan
    # constraint 6 - Charging as little as possible at the high level
    # constraint 7 - the ampere in each charger dosent over the max ampere of the charger

    # weights:
    # constraint 1
    w1 = 0.16
    # constraint 2
    w2 = 0.16
    # constraint 3 
    w3 = 0.16
    # constraint 4
    w4 = 0.16
    # constraint 5
    w5 = 0.12
    # constraint 6
    w6 = 0.8
    # constraint 7
    w7 = 0.16

    total_cost = 0

    # parameters:
    # constraint 1
    cost1 = 0
    good1 = 0
    not_good1 = 0
    # constraint 2
    cost2 = 0
    good2 = 0
    not_good2 = 0
    # constraint 3 
    start_ampere_list = []
    end_ampere_list = []
    cost3 = 0
    # constraint 4
    busses_charge = {}
    cost4 = 0
    good4 = 0
    not_good4 = 0
    # constraint 5
    financial_cost = 0
    cost5 = 0
    # constraint 6
    level1 = 0
    level2 = 0
    level3 = 0
    cost6 = 0
    # constraint 7
    chargers_bussy = {charger[0]:{"maxAmpere": chargers[charger]["ampere"], "chargings":[]} for charger in chargers.keys()}
    good7 = 0
    not_good7 = 0

    for bus in busses.keys():
        busses_charge[bus] = {'charge': 0,'soc_start': busses[bus]['socStart'], 'soc_end': busses[bus]['socEnd']}

    for i in range(0, len(solution), 7):
        
        chargerCode, connectorId, bus_code, start_time, end_time, ampere, price = solution[i:i+7] 
        voltage = 0
        if chargerCode in chargers:
            voltage = chargers[chargerCode]["voltage"]

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

        # constraint 3
        start_ampere_list.append({'start_time': start_time, 'ampere': ampere, 'voltage': voltage})
        end_ampere_list.append({'end_time': end_time, 'ampere': ampere, 'voltage': voltage})

        # constraint 4
        if bus_code not in busses_charge:
            raise Exception("Bus code not found")
        charging_time = end_time - start_time
        if bus_code in capacity:
            busses_charge[bus_code]['charge']+= charging_time/1000/60*ampere*voltage/1000/capacity[int(bus_code)]
        for bus in busses_charge:
            if busses_charge[bus]['charge'] > 95 or busses_charge[bus]['charge'] < busses_charge[bus]['soc_end']:
                not_good4+=1
            else:
                good4+=1
        
        # constraint 5
        financial_cost += price

        #constraint 6
        if ampereLevels[1]["low"] <= ampere and ampere <= ampereLevels[1]["high"]:
            level1+=1
        if ampereLevels[2]["low"] <= ampere and ampere <= ampereLevels[2]["high"]:
            level2+=1
        if ampereLevels[3]["low"] <= ampere and ampere <= ampereLevels[3]["high"]:
            level3+=1

        # constraint 7
        chargers_bussy[chargerCode]["chargings"].append({"time": start_time, "type": "start", "ampere": ampere})
        chargers_bussy[chargerCode]["chargings"].append({"time": end_time, "type": "end", "ampere": ampere})

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


    sum_of_schedules = good1+not_good1
    cost1 = w1*not_good1/(good1+not_good1)
    cost2 = w2*not_good2/(good2+not_good2)
    cost3 = w3*calculate_cost_3(start_ampere_list, end_ampere_list, maxPower)
    cost4 = w4*not_good4/(good4+not_good4)
    cost5 = w5*(financial_cost-min_cost)/(max_cost-min_cost)
    cost6 = w6*(level1/sum_of_schedules+0.5*level2/sum_of_schedules+0.25*level3/sum_of_schedules)
    cost7 = w7*not_good7/(good7+not_good7)
    total_cost = cost1 + cost2 + cost3 + cost4 + cost5 + cost6 + cost7
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
