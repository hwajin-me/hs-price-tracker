import aiohttp

from custom_components.price_tracker.exception import ApiError


def findItem(list: [dict], key: str, value : any):
  for i in list:
    if key in i and i[key] == value:
      return i

  return None

async def request(url: str, headers: dict = None):
  async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
    async with session.get(url=url, headers=headers) as response:
      if response.status != 200:
        raise ApiError("Error while fetching data from the API (status code: {})".format(response.status))

      return await response.read()
