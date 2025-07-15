def leastCostRule(demand, supply, costValueMatrix):
    if sum(demand) != sum(supply):
        return "Invalid input"
    adjustedCostValueMatrix = costValueMatrix.copy()
    values = []
    keyPairValues = []
    #m is the demand or y axis
    #n is the supply or x axis
    m = 0
    n = 0
    Done = False
    while not Done:
        minCost = float('inf')
        for row in adjustedCostValueMatrix:
            if min(row) < minCost:
                minCost = min(row)
                m = adjustedCostValueMatrix.index(row)
                n = row.index(min(row))
        print(minCost, m, n)
        if demand[m] > supply[n]:
            values.append([supply[n], minCost])
            keyPairValues.append([m, n])
            demand[m] -= supply[n]
            for i in range(len(demand)):
                adjustedCostValueMatrix[i][n] = float('inf')
            supply[n] = 0

        elif demand[m] < supply[n]:
            values.append([demand[m], minCost])
            keyPairValues.append([m, n])
            supply[n] -= demand[m]
            for i in range(len(supply)):
                adjustedCostValueMatrix[m][i] = float('inf')
            demand[m] = 0
        elif demand[m] == supply[n]:
            values.append([demand[m], minCost])
            keyPairValues.append([m, n])
            demand[m] = 0
            supply[n] = 0
        if sum(demand) == 0 and sum(supply) == 0:
            Done = True
        print(adjustedCostValueMatrix)
    results = [value[0]*value[1] for value in values]
    return sum(results), keyPairValues


demand = [30, 80, 40]
supply = [60, 40, 50]
costValueMatrix = [[2, 3, 1], [5, 4, 7], [1, 6, 2]]
values, keyPairValues = leastCostRule(demand, supply, costValueMatrix)
print(values, keyPairValues)