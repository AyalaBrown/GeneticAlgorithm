import initializations
import readingFromDb

def min_max_price():
    """
    This function calculates the minimum and maximum price for the parking lot plan
    """
    data = initializations.getFunctionInputsDB()
    busses = data["busses"]
    prices = data["prices"]
    amperLevels = data["amperLevels"]
    total_min_price = 0
    total_max_price = 0
    busses = dict(sorted(busses.items(), key=lambda x: x[1]["entryTime"]))
    # try:
    lowAmpere = amperLevels[4]['low']+(amperLevels[4]['high']-amperLevels[4]['low'])/2
    highAmpere = amperLevels[0]['high']+(amperLevels[0]['high']-amperLevels[0]['low'])/2
    for bus in busses:
        min_time = readingFromDb.getChargingTime(bus, 5, busses[bus]["socStart"], busses[bus]["socEnd"])
        min_price = minPrice(min_time, busses[bus]["entryTime"], busses[bus]["exitTime"], prices, lowAmpere, 650)
        total_min_price+=min_price
        max_time = readingFromDb.getChargingTime(bus, 1, busses[bus]["socStart"], busses[bus]["socEnd"])
        max_price = maxPrice(max_time, busses[bus]["entryTime"], busses[bus]["exitTime"], prices, highAmpere, 650)
        total_max_price+=max_price
    return total_min_price, total_max_price

    # except Exception as e:
    #     print("error!!!!!!!!", e)
    #     return 0, 0
    
def minPrice(time, entry_time, exit_time, prices, ampere, voltage):
    prices = sorted(prices, key=lambda x: x['finalPriceInAgorot'])
    distinct_prices = sorted(set(entry['finalPriceInAgorot'] for entry in prices))
    distinct_prices_list = list(distinct_prices)
    for i in prices:
        if entry_time >= i['from']:
            if (entry_time+time) <= i['to']:
                price = distinct_prices_list[0]/100 * ampere *time/1000./60./60. * voltage/1000
                return price
            else:
                price = distinct_prices_list[0]/100 * ampere *(exit_time-entry_time)/1000./60./60. * voltage/1000
                price +=distinct_prices_list[1]/100 * ampere *(time-(exit_time-entry_time))/1000./60./60. * voltage/1000
                return price
        else:
            price = distinct_prices_list[1]/100 * ampere *time/1000./60./60. * voltage/1000
            return price
    return 0, 1

def maxPrice(time, entry_time, exit_time, prices, ampere, voltage):
    prices = sorted(prices, key=lambda x: x['finalPriceInAgorot'])
    distinct_prices = sorted(set(entry['finalPriceInAgorot'] for entry in prices))
    distinct_prices_list = list(distinct_prices)
    for i in prices:
        if entry_time >= i['from']:
            if entry_time+time <= i['to']:
                price = distinct_prices_list[1]/100 * ampere *time/1000./60./60. * voltage/1000
                return price
            else:
                price = distinct_prices_list[1]/100 * ampere *(exit_time-entry_time)/1000./60./60. * voltage/1000
                price +=distinct_prices_list[0]/100 * ampere *(time-(exit_time-entry_time))/1000./60./60. * voltage/1000
                return price
        else:
            price = distinct_prices_list[0]/100 * ampere *time/1000./60./60. * voltage/1000
            return price
    