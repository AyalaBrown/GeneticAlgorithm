import numpy as np
import matplotlib.pyplot as plt
from deap import base, creator, tools, algorithms

# Define the problem
def sphere(individual):
    x = np.array(individual)
    return sum(x**2),

# Custom statistics functions
def get_avg(population):
    return np.mean([ind.fitness.values[0] for ind in population]),

def get_min(population):
    return np.min([ind.fitness.values[0] for ind in population]),

def get_max(population):
    return np.max([ind.fitness.values[0] for ind in population]),

# Genetic Algorithm parameters
pop_size = 50
genetic_algorithm_params = {
    'cxpb': 0.7,   # Crossover probability
    'mutpb': 0.2,  # Mutation probability
    'ngen': 100,   # Number of generations
}

# Create DEAP types
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

# Create DEAP toolbox
toolbox = base.Toolbox()
toolbox.register("attr_float", np.random.uniform, -10, 10)
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_float, n=5)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

# Evaluation function
toolbox.register("evaluate", sphere)

# Genetic operators
toolbox.register("mate", tools.cxBlend, alpha=0.5)
toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.1, indpb=0.2)
toolbox.register("select", tools.selTournament, tournsize=3)

# Create the population and run the genetic algorithm
population = toolbox.population(n=pop_size)
hall_of_fame = tools.HallOfFame(maxsize=1)  # To track the best individual

# Additional logging
stats = tools.Statistics()
stats.register("avg", get_avg)
stats.register("min", get_min)
stats.register("max", get_max)

# Run the genetic algorithm with additional suggestions
# Adjusting mutation and crossover rates
toolbox.register("mate", tools.cxBlend, alpha=0.5)  # Change the crossover operator
genetic_algorithm_params['mutpb'] = 0.5  # Experiment with different values
genetic_algorithm_params['cxpb'] = 0.8   # Experiment with different values

# Run the genetic algorithm
algorithms.eaMuPlusLambda(population, toolbox, mu=pop_size, lambda_=2*pop_size, stats=stats, halloffame=hall_of_fame, **genetic_algorithm_params)

# Extract and print the values
avg_values = stats.functions["avg"](population)
min_values = stats.functions["min"](population)
max_values = stats.functions["max"](population)

print("Average values:", avg_values)
print("Minimum values:", min_values)
print("Maximum values:", max_values)

# Plotting
num_generations = genetic_algorithm_params['ngen']
gen = range(1, num_generations + 1)
avg = [stats.functions["avg"](population) for _ in gen]
min_ = [stats.functions["min"](population) for _ in gen]
max_ = [stats.functions["max"](population) for _ in gen]

plt.plot(gen, avg, label="average")
plt.plot(gen, min_, label="minimum")
plt.plot(gen, max_, label="maximum")
plt.xlabel("Generation")
plt.ylabel("Fitness")
plt.legend()
plt.show()
