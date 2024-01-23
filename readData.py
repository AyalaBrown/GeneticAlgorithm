import numpy as np
import pyodbc

# Define the connection parameters
server = '192.168.16.3'
database = 'Electric_Ml'
username = 'Ayala'
password = 'isr1953'

# Create a connection string
connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

# Establish a connection
connection = pyodbc.connect(connection_string)
cursor = connection.cursor()

# Example: Read solutions from the database
table_name = 'dbo.ChargerSolution'
query = f'SELECT chargerCode, trackCode, startTime, endTime, amperLevel, priceInAgorot FROM {table_name}'
query2 = f"exec dbo.GetElectricRate_PerDate '20240201'"

cursor.execute(query2)

# Fetch all the rows
initial_solutions = cursor.fetchall()

# Close the cursor and connection
cursor.close()
connection.close()

# Convert each solution to binary
binary_population = []

for solution in initial_solutions:
    # Convert each field to binary and concatenate
    binary_solution = []
    for field in solution:
        if isinstance(field, float):
            field = int(field)  # Convert float to int
        binary_solution.extend(list(bin(field)[2:].zfill(8)))  # Assuming 8 bits for each field

    binary_population.append(binary_solution)

# Convert the binary population to a NumPy array
binary_population = np.array(binary_population, dtype=int)

# Now, binary_population contains the initial population in binary format
print(binary_population)
