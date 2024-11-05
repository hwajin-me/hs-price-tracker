
def findItem(list: [dict], key: str, value : any):
  for i in list:
    if key in i and i[key] == value:
      return i

  return None

def findValueOrDefault(list: [dict], key: str, defaultValue: any = None):
  return list[key] if key in list and list[key] is not None else defaultValue

def removeItem(list: [any], key: str, value: any):
  return list(filter(lambda x : x[key] != value, list))

def parseNumber(value: any):
  return float(str(value).replace(",", "").replace(" ", ""))
