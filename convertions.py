import initialPopulation

def convert_population_to_numeric(population):
    numeric_population = []
    for schedule in population:
        numeric_schedule = []
        for entry in schedule:
            numeric_schedule.extend([entry["chargerCode"], entry["connectorId"], entry["trackCode"], entry["startTime"], entry["endTime"], entry["ampere"], entry["price"]])
        numeric_population.append(numeric_schedule)
    return numeric_population

def initial_population():   
    bus_schedule = initialPopulation.init_pop(10)
    numeric_representation = convert_population_to_numeric(bus_schedule)
    return numeric_representation
