import pyodbc
import pandas as pd
import json
import DateTime


server = '192.168.16.3'
database = 'electric_ML'
username = 'Ayala'
password = 'isr1953'

def read_data():
    cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = cnxn.cursor()
    query = "exec dbo.GetElectricPlan_trackSoc '20240107';"
    b = pd.read_sql(query, cnxn).to_dict(orient='records')
    busses = {}
    for i in b:
        if i["socStart"] > 0 and i["socStart"] < i["socEnd"] and i["entryTime"] < i["exitTime"]and i["entryTime"] > 0:
            busses[i["trackCode"]] = {"entryTime": i["entryTime"], "exitTime": i["exitTime"] , "socStart": i["socStart"], "socEnd": i["socEnd"]}
    query = "exec isrProject_test.dbo.GetChargersList;"
    chrgs = {}
    # chargers = pd.read_sql(query, cnxn).to_dict(orient='records')
    # for i in range(0, len(chargers)):
    #     if chargers[i]["voltage"] > 0:
    #         chrgs.append({"chargerCode": chargers[i]["code"], "connectorId": 1, "voltage": chargers[i]["voltage"]})
    #         chrgs.append({"chargerCode": chargers[i]["code"], "connectorId": 2, "voltage": chargers[i]["voltage"]})
    for i in range(150):
        chrgs[(i, 1)] = {"voltage": 650, "ampere": 112}
        chrgs[(i, 2)] = {"voltage": 650, "ampere": 112}
    query = "exec dbo.GetElectricRate_PerDate '20240107';"
    prices = pd.read_sql(query, cnxn).to_dict(orient='records')
    query = "exec dbo.GetElectricRate_PerDate '20240108';"
    prices2 = pd.read_sql(query, cnxn).to_dict(orient='records')
    prices.extend(prices2)
    query = "exec dbo.GetElectricAmperLevels;"
    amperLevels = pd.read_sql(query, cnxn).to_dict(orient='records')
    query = "exec  dbo.GetElectricCapacity;"
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

# write_data([1,2,3,4,5,6,7,1,2,3,4,5,6,7,1,2,3,4,5,6,7], '20240107')