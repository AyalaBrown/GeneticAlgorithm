import numpy as np

# Constants
MAX_COST = float('inf')  # A large value for cost initialization
INVALID_SOLUTION_PENALTY = 100

def validate_solution(solution):
    print("validateSolution")
    # Check if there is no overlap in charging times for buses using the same charger
    chargers_schedule = {}  # Dictionary to store charging schedule for each charger
    for i in range(0, len(solution), 5):
        charger_code, _, start_time, end_time, _ = solution[i:i+5]
        start_time, end_time = int(start_time), int(end_time)
        if charger_code not in chargers_schedule:
            chargers_schedule[charger_code] = set()
        schedule_set = chargers_schedule[charger_code]
        for time in range(start_time, end_time):
            if time in schedule_set:
                return False  # Overlapping charging times for buses on the same charger
            schedule_set.add(time)

    # Check if end time is greater than start time for each bus
    for i in range(2, len(solution), 5):
        start_time, end_time = solution[i], solution[i+1]
        if end_time <= start_time:
            return False  # Invalid charging time

    return True  # Solution is valid

def fitness_func(ga_instance, solution, solution_idx):
    valid = validate_solution(solution)
    print(valid)
    if not valid:
        # Penalize invalid solutions by adding a penalty to the total cost
        print(1 + MAX_COST + INVALID_SOLUTION_PENALTY)
        cost = 1 / (1 + MAX_COST + INVALID_SOLUTION_PENALTY)
        print(f"Invalid solution, cost {cost}")
        return cost
    
    total_cost = 0
    total_amper = np.zeros(len(solution[0]))  # Initialize total amperage for each time slot
    
    for i in range(0, len(solution), 5):
        charger_code, bus_code, start_time, end_time, amper_level = solution[i:i+5]

        # Constraint: Ensure every bus exits the parking lot on time with enough SoC
        # if bus_info["socStart"] + amper_level > bus_info["socEnd"]:
        #     total_cost += MAX_COST  # Penalize solutions where a bus cannot exit on time with enough SoC

        # Constraint: Avoid exceeding the total charge (maxAmper) at any given moment
        # total_amper[bus_code] += amper_level
        # if total_amper[bus_code] > ga_instance.maxAmper:
        #     total_cost += MAX_COST  # Penalize solutions exceeding maxAmper

        # Objective: Minimize the total cost of charging for all buses
        # time_range = (start_time, end_time)
        # for price_info in ga_instance.prices:
        #     if price_info["from"] <= time_range[0] < price_info["to"] and price_info["from"] <= time_range[1] < price_info["to"]:
        #         total_cost += amper_level * (price_info["finalPriceInAgorot"] / 100)  # Add cost based on price

        # Objective: Minimize the use of fastest charging in high-level ampere
        # if amper_level == 1 and total_amper[bus_code] > ga_instance.maxAmper * 0.7:
        #     total_cost += MAX_COST  # Penalize fastest charging at high-level ampere

        # Objective: Minimize the number of chargers used
        # total_cost += len(set([solution[i] for i in range(0, len(solution), 5)])) * 10  # Penalize for each charger used

    return 1 / (1 + total_cost)  # Return the inverse to maximize fitness

# Example usage:

# Example desired_output (can be empty or set to None for multi-objective problems)
desired_output = None

# Assuming prices is a list of (from, to, finalPriceInAgorot)
# prices = initializations.getPrices()


