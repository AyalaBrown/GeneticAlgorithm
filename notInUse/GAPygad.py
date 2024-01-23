import numpy as np
import pygad
import fit
import initializations
import convertions
import random

function_inputs = initializations.getFunctionInputs() # Function inputs.
desired_output = None # Function output.
def fitness_func(ga_instance, solution, solution_idx):
    return 0

# def fitness_func(ga_instance, solution, solution_idx):
#     output = np.sum(solution*function_inputs)
#     fitness = 1.0 / np.abs(output - desired_output)
#     # print(fitness)
#     return fitness

num_generations = 50
num_parents_mating = 5

population = convertions.initial_population()

fitness_function = fitness_func

sol_per_pop = len(population)
num_genes = len(population[0])

init_range_low = 0
init_range_high = 5

parent_selection_type = "sss"
keep_parents = 1

crossover_type = "single_point"

mutation_type = "random"
mutation_percent_genes = 5



def _mutation_func(offspring, ga_instance, values=None):
    print("_mutation_func", offspring)
    for chromosome_idx in range(offspring.shape[0]):
        random_gene_idx = np.random.choice(range(offspring.shape[1]))
        param_inx = random_gene_idx % 5
        param_values = values[param_inx]
        if param_values is not None:
            offspring[chromosome_idx, random_gene_idx] = int(random.choice(param_values))
        else:
            offspring[chromosome_idx, random_gene_idx] += int(np.round(np.random.random()))
    return offspring

def mutation_func(offspring, ga_instance):
    values = initializations.getValues()
    offspring = _mutation_func(offspring, ga_instance, values)
    return offspring

def on_gen(ga_instance):
    print("Generation : ", ga_instance.generations_completed)
    print("Fitness of the best solution :", ga_instance.best_solution()[1])

ga_instance = pygad.GA(num_generations=num_generations,
                       on_generation=on_gen,
                       num_parents_mating=num_parents_mating,
                       fitness_func=fitness_function,
                       sol_per_pop=sol_per_pop,
                       num_genes=num_genes,
                       initial_population=population,
                       init_range_low=init_range_low,
                       init_range_high=init_range_high,
                       parent_selection_type=parent_selection_type,
                       keep_parents=keep_parents,
                       crossover_type=crossover_type,
                       mutation_type=mutation_func,
                       mutation_percent_genes=mutation_percent_genes)

ga_instance.run()

ga_instance.plot_fitness()

solution, solution_fitness, solution_idx = ga_instance.best_solution()
print(f"Parameters of the best solution : {solution}")
print(f"Fitness value of the best solution = {solution_fitness}")
print(f"Index of the best solution : {solution_idx}")

if ga_instance.best_solution_generation != -1:
    print(f"Best fitness value reached after {ga_instance.best_solution_generation} generations.")

filename = './genetic'
ga_instance.save(filename=filename)

loaded_ga_instance = pygad.load(filename=filename)

print(loaded_ga_instance.best_solution())