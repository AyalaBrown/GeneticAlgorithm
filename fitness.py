def fitness(solution, min_cost, max_cost):
    total_cost = 0
    for i in range(0, len(solution), 7):
        _, _, _, _, _, _, price = solution[i:i+7] 
        total_cost += price
    return total_cost