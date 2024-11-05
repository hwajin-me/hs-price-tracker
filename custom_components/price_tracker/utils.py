
def findItem(list: [dict], key: str, value : any):
  for i in list:
    if key in i and i[key] == value:
      return i
  
  return None