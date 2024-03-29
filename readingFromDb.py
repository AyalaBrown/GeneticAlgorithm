import pyodbc
import pandas as pd
import json

server = '192.168.16.3'
database = 'electric_ML'
username = 'Ayala'
password = 'isr1953'

def read_init_pop(date, npop):
    cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = cnxn.cursor()
    query = f"exec dbo.Electric_InitialPopulation '{date}', {npop}"
    pop = {}
    try:
        pop = pd.read_sql(query, cnxn)
    except Exception as e:
        print("Error occurred while reading from SQL:", str(e))
    finally:
        cursor.close()
        cnxn.close()
    return pop

def read_data():
    cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = cnxn.cursor()
    query = "exec dbo.GetElectricPlan_trackSoc '20240107';"
    b = pd.read_sql(query, cnxn).to_dict(orient='records')
    busses = {}
    for i in b:
        busses[i["trackCode"]] = {"entryTime": i["entryTime"], "exitTime": i["exitTime"] , "socStart": i["socStart"], "socEnd": i["socEnd"]}
    query = "exec dbo.GetChargersList;"
    chargers = pd.read_sql(query, cnxn).to_dict(orient='records')
    chrgs = {}
    for charger in chargers:
        if charger['chargePointModel'] == 'DC 150kW':
            chrgs[(charger['code'], 1)] = {"voltage": charger['voltage'], "ampere": charger['ampere']/2}
            chrgs[(charger['code'], 2)] = {"voltage": charger['voltage'], "ampere": charger['ampere']/2}
        else:
            chrgs[(charger['code'], 1)] = {"voltage": charger['voltage'], "ampere": charger['ampere']}
    query = "exec dbo.GetElectricRate_PerDate '20240107';"
    prices = pd.read_sql(query, cnxn).to_dict(orient='records')
    query = "exec dbo.GetElectricRate_PerDate '20240108';"
    prices2 = pd.read_sql(query, cnxn).to_dict(orient='records')
    prices.extend(prices2)
    query = "exec dbo.GetElectricAmperLevels;"
    amperLevels = pd.read_sql(query, cnxn).to_dict(orient='records')
    query = "exec dbo.GetElectricCapacity;"
    c = pd.read_sql(query, cnxn)
    capacity = {}
    for i in range(0, len(c)):
        capacity[int(c.loc[i,"trackCode"])] = float(c.loc[i,"capacity"])
    data = {"busses": busses, "maxPower": 4000000, "chargers": chrgs, "prices": prices, "amperLevels": amperLevels, "capacity": capacity}
    cursor.close() 
    cnxn.close()
    return data

def write_data(solution, solutionDate):
    cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password, autocommit=True)
    cursor = cnxn.cursor()
    query = f"EXEC dbo.Electric_CreateSolutionCode '{solutionDate}'"
    result = pd.read_sql(query, cnxn).to_dict(orient='records')
    solutionCode = result[0]["solutionCode"]
    print(solutionCode)
    data_to_send = []
    for i in range(0, len(solution), 7):
        schedule = {
            "solutionCode": solutionCode,
            "chargerCode": solution[i],
            "connectorId": solution[i+1],
            "trackCode": solution[i+2],
            "startTime": solution[i+3],
            "endTime": solution[i+4],
            "ampere": solution[i+5],
            "price": solution[i+6]
        }
        data_to_send.append(schedule)
    json_param = json.dumps(data_to_send)
    query = f"exec dbo.Electric_InsertSolution '{json_param}'"
    try:
        # Execute the stored procedure with the JSON parameter
        result = pd.read_sql(query, cnxn).to_dict(orient='records')
        if result[0]["insertedRows"]< result[0]["dataRows"]:
            print("Somthing went wrong.... There are conflicts in your scheduling")
        print(result)
        # Commit the transaction and close the connection
        cursor.close()
        cnxn.close()
    except pyodbc.Error as ex:
        print("Error:", ex)

def getChargingTime(bus, ampereLevel, start, end):
    cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password, autocommit=True)
    cursor = cnxn.cursor()
    query = f"select dbo.calcBI('Electric Bus Charge','14:1F:BA:10:7D:61,{ampereLevel}',cast('<soc>{end}</soc>' as xml)).value('/result[1]/scaled[1]','float')-dbo.calcBI('Electric Bus Charge','14:1F:BA:10:7D:61,{ampereLevel}',cast('<soc>{start}</soc>' as xml)).value('/result[1]/scaled[1]','float')"
    cursor.execute(query)
    result = cursor.fetchone()
    i = ampereLevel+1 if ampereLevel==1 else ampereLevel-1
    while result[0]==None and i>1 and i<5:
        i = i+1 if ampereLevel == 1 else i-1
        query = f"select dbo.calcBI('Electric Bus Charge','14:1F:BA:10:7D:61,{i}',cast('<soc>{end}</soc>' as xml)).value('/result[1]/scaled[1]','float')-dbo.calcBI('Electric Bus Charge','14:1F:BA:10:7D:61,{i}',cast('<soc>{start}</soc>' as xml)).value('/result[1]/scaled[1]','float')"
        cursor.execute(query)
        result = cursor.fetchone()
    cursor.close()
    cnxn.close()
    if result[0]==None:
        print(f"No resulte for bus {bus}")
        return 10
    return int(result[0]*60*1000)

data = read_data()
print(len(data['busses']))
print(len(data['chargers']))