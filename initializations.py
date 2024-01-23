import readingFromDb

data = readingFromDb.read_data()

def getFunctionInputsDB():
    chargers = list(data["chargers"].keys())
    chargerCodes = []
    for code in chargers:
        chargerCodes.append(code[0])
    busses = list(data["busses"].keys())
    amperes = []

    for i in range(0, len(data["amperLevels"])):
        amperes.append(data["amperLevels"][i]["low"]+(data["amperLevels"][i]["high"]-data["amperLevels"][i]["low"])/2)
    u_amperes = list(set(amperes))
    values = [chargerCodes, [1,2], busses, 'start', 'end', u_amperes, None]
    data["values"] = values
    return data

def getFunctionInputs():
    return {
        "busses": [
            {"trackCode":101, "entryTime":7, "exitTime":13, "socStart":20, "socEnd":80},
            {"trackCode":102, "entryTime":8, "exitTime":11, "socStart":50, "socEnd":90},
            {"trackCode":103, "entryTime":9, "exitTime":14, "socStart":20, "socEnd":40},
            {"trackCode":104, "entryTime":9, "exitTime":15, "socStart":30, "socEnd":40},
            {"trackCode":105, "entryTime":7, "exitTime":11, "socStart":20, "socEnd":80},
            {"trackCode":106, "entryTime":7, "exitTime":12, "socStart":40, "socEnd":60},
            {"trackCode":107, "entryTime":7, "exitTime":13, "socStart":20, "socEnd":80},
            {"trackCode":108, "entryTime":8, "exitTime":11, "socStart":50, "socEnd":90},
            {"trackCode":109, "entryTime":9, "exitTime":14, "socStart":20, "socEnd":40},
            {"trackCode":110, "entryTime":9, "exitTime":15, "socStart":30, "socEnd":40},
            {"trackCode":111, "entryTime":7, "exitTime":11, "socStart":20, "socEnd":80},
            {"trackCode":112, "entryTime":7, "exitTime":12, "socStart":40, "socEnd":60},
            {"trackCode":113, "entryTime":9, "exitTime":15, "socStart":30, "socEnd":40},
            {"trackCode":114, "entryTime":7, "exitTime":11, "socStart":20, "socEnd":80},
            {"trackCode":115, "entryTime":7, "exitTime":12, "socStart":40, "socEnd":60},
            {"trackCode":116, "entryTime":7, "exitTime":11, "socStart":20, "socEnd":80},
            {"trackCode":117, "entryTime":7, "exitTime":12, "socStart":40, "socEnd":60},
            {"trackCode":118, "entryTime":9, "exitTime":15, "socStart":30, "socEnd":40},
            {"trackCode":119, "entryTime":7, "exitTime":11, "socStart":20, "socEnd":80},
            {"trackCode":120, "entryTime":7, "exitTime":12, "socStart":40, "socEnd":60}
        ],
        "maxPower": 4000000,
        "prices": [
            {"from": 1704578400000, "to": 1704639599000, "finalPriceInAgorot": 41.84},
            {"from": 1704639600000, "to": 1704657599000, "finalPriceInAgorot": 114.78}, 
            {"from": 1704657600000, "to": 1704664799000, "finalPriceInAgorot": 41.84}
        ],
        "chargers": [
            {"chargerCode": 1, "connectorId":1, "voltage":650},
            {"chargerCode": 1, "connectorId":2, "voltage":650},
            {"chargerCode": 2, "connectorId":1, "voltage":648},
            {"chargerCode": 2, "connectorId":2, "voltage":648},
            {"chargerCode": 3, "connectorId":1, "voltage":652},
            {"chargerCode": 3, "connectorId":2, "voltage":652},
            {"chargerCode": 4, "connectorId":1, "voltage":650},
            {"chargerCode": 4, "connectorId":2, "voltage":650}
        ],
        "amperLevels": [
            {"levelCode": 1, "low": 140, "high": 170}, 
            {"levelCode": 2, "low": 107, "high": 135}, 
            {"levelCode": 3, "low": 95, "high": 106}, 
            {"levelCode": 4, "low": 70, "high": 90}, 
            {"levelCode": 5, "low": 40, "high": 45}
        ],
        "values": [
            [1, 2, 3, 4],
            [1, 2],
            [101, 102, 103, 104, 105, 106],
            None,
            None,
            [155, 121, 100.5, 80, 42.5],
            None
        ]
    }