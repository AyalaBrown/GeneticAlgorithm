import numpy as np
import pygad
import datetime
import initializations

prices = None
max_amper = None
valid_chargers = None
valid_buses = None
valid_amper_levels = None
entry_times = None
values = None

def create_schedule_chromosome():
    return np.random.randint(1, 5, size=(5,))

def create_initial_population(population_size):
    return [create_schedule_chromosome() for _ in range(population_size)]

def get_total_cost(solution, prices):
    total_cost = 0
    for i in range(0, len(solution), 5):
        charger_code, track_code, start_time, end_time, amper_level = solution[i:i+5]
        time_range = (start_time, end_time)
        for price_info in prices:
            if time_range[0] >= price_info["from"] and time_range[1] <= price_info["to"]:
                total_cost += (amper_level * price_info["finalPriceInAgorot"])
                break
    return total_cost

def is_valid_charger(charger_code, valid_chargers):
    return charger_code in valid_chargers

def is_valid_bus(track_code, valid_buses):
    return track_code in valid_buses

def is_valid_amper_level(amper_level, valid_amper_levels):
    return amper_level in valid_amper_levels

def fitness_function(ga_instance, solution, solution_idx):

    global prices, max_amper, valid_chargers, valid_buses, valid_amper_levels, entry_times

    total_cost = get_total_cost(solution, prices)

    # Constraint 1: Ensure every bus exits from the parking lot on time with enough SOC
    valid_exit_times = [solution[i+3] for i in range(0, len(solution), 5)]
    invalid_exit_times = [bus_exit_time - entry_time for bus_exit_time, entry_time in zip(valid_exit_times, entry_times) if bus_exit_time < entry_time]
    constraint1_penalty = sum(invalid_exit_times) * 1000  # Penalize if any bus exits late
    
    # Constraint 2: Ensure the total amount of charge does not exceed max_amper at any moment
    total_amper = np.sum(solution[4::5])
    constraint2_penalty = max(0, total_amper - max_amper) * 10000  # Penalize if total amper exceeds max_amper

    # Constraint 3: Prefer to charge buses when the price per Kilowatt is cheapest
    constraint3_penalty = 0  # No need for penalty, as this is already optimized in the cost calculation

    # Constraint 4: Avoid fastest charging in high-level ampere
    constraint4_penalty = 0  # No need for penalty, as this is already optimized in the cost calculation

    # Constraint 5: Use as few chargers as possible
    used_chargers = set(solution[::5])
    constraint5_penalty = (len(valid_chargers) - len(used_chargers)) * 100000  # Penalize for using fewer chargers
    
    return -total_cost - constraint1_penalty - constraint2_penalty - constraint3_penalty - constraint4_penalty - constraint5_penalty

def custom_mutation_function(offspring, ga_instance, valid_values):
    mutated_solution = offspring.copy()
    mutation_gene_index = np.random.randint(len(offspring))
    valid_gene_values = valid_values[mutation_gene_index % 5]

    if valid_gene_values is not None:
        mutated_solution[mutation_gene_index] = np.random.choice(valid_gene_values)

    return mutated_solution

def mutation_func(offspring, ga_instance):
    global values
    offspring = custom_mutation_function(offspring, ga_instance, values)
    return offspring

# Data initialization
population = initializations.getPopulation()
function_inputs = initializations.getFunctionInputs()
entry_times = [bus_info["entryTime"] for bus_info in function_inputs["busses"]]

# Set global variables
values = initializations.getValues()
prices = function_inputs["prices"]
max_amper = function_inputs["maxAmper"]
valid_chargers = values[0]
valid_buses = values[1]
valid_amper_levels = values[4]

# Genetic Algorithm parameters
num_generations = 100
population_size = 20

# Create the initial population
initial_population = create_initial_population(population_size)

# Create the GA instance
ga_instance = pygad.GA(num_generations=num_generations,
                       num_parents_mating=10,
                       sol_per_pop=population_size,
                       num_genes=len(initial_population[0]),
                       fitness_func=fitness_function,
                       mutation_type=mutation_func,
                       random_mutation_min_val=0.0,
                       random_mutation_max_val=1.0
                    )

# Run the GA
ga_instance.run()

# Get the best solution
best_solution = ga_instance.best_solution()

# Print the best solution
print("Best Solution:")
print(best_solution)
print("Total Cost:", -best_solution[1])

# Decode the best solution and print the schedule
decoded_solution = best_solution[0].reshape(-1, 5)
print("\nDecoded Schedule:")
for schedule in decoded_solution:
    print(schedule)
