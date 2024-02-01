import os
from json import loads
from requests import get
from requests_html import HTMLSession
from js2py import run_file
import urllib3
from tabulate import tabulate
tabulate.WIDE_CHARS_MODE = True



################################################
#                 initializing                 #
################################################
if __name__ == '__main__':
    # get current script path
    filepath = os.path.realpath(__file__)
    CURRENT_PATH = os.path.dirname(filepath)
    # supperss urllib3 warnings
    urllib3.disable_warnings()



################################################
#        customization message foramt          #
################################################
def err(message: str):
    print('\n\tERR -->', message + '!\n\r')
def info(message: str):
    print(f"\n[INFO] {10 * '-'}> ", message)



################################################
#       get user current wallet balance        #
################################################
def get_wallet_balance():
    # get user wallet balance
    # wallet_balance = input('*up to 2 decimal are allowed and they can be separated by dot or comma.\n\tenter your current wallet balance: ')
    wallet_balance = input('enter your current wallet balance: ')
    # check that the input is not empty
    if not wallet_balance or wallet_balance == 0:
        return float(0)
    # prevent enter non-allowed characters
    specialChars = '[@_!#$%^&*()<>.?/\|}{~:]'
    for char in specialChars:
        if char in wallet_balance:
            err('use comma for decimal digits')
            return get_wallet_balance()
    else:
        if ',' in wallet_balance:
            # check max length
            if len(wallet_balance[wallet_balance.find(',') + 1:]) > 2:
                err('only 2 decimals are accepted')
            else:
                try:
                    wallet_balance = float(wallet_balance.replace(',', '.'))
                except:
                    err('use comma for decimal digits')
    # the final received data
    return float(wallet_balance)



################################################
#        get finall game price by appid        #
################################################
def get_game_price(wallet_balance: float):
    game = {}
    appid, price = '', 0.0
    # get game/product appid
    # appid = input('*in Steam, all games have a unique appid that is all numbers and is visible at the end of the page url\n\tenter appid of the game you want: ')
    userInput = input('enter appid of the game/price of game you want: ')
    # check that the input is not empty
    if not userInput or len(userInput.strip()) == 0:
        err('enter a valid steam appid or price (must have a comma and 2 decimal places)')
        return get_game_price(wallet_balance)
    # find out user input type
    if userInput.find(',') != -1:
        price = userInput
        game['price'] = float(price.replace(',', '.'))
    else:
        appid = userInput
        # check the existence of appid in steam
        if get(url=f'https://store.steampowered.com/app/{appid}').url == 'https://store.steampowered.com/':
            err('this appid does not exist')
            return get_game_price(wallet_balance)
        # get name of game by appid
        response = get(url='https://api.steampowered.com/ISteamApps/GetAppList/v2').json()
        response = response['applist']['apps']
        for app in response:
            if app['appid'] == int(appid):
                game['name'] = app['name']
                break
        # get finall price of game
        response = get(url='https://store.steampowered.com/api/appdetails', verify=False, params={
                'appids': appid,
                'cc': 'TR'
            }).text
        # convert to json
        response = response[response.find('{', 1):-1]
        response = loads(response)['data']['price_overview']['final_formatted']
        response = response[:-3]
        game['price'] = float(response[1:])
    # add current balance to calculation
    if wallet_balance < game['price']:
        game['price'] -= wallet_balance
    else:
        err('de akhe kooni...')
        quit()
    return game



################################################
#   get item sale price without fee in market  #
################################################
def get_real_item_price(amount: str):
    # load js algorithm
    # stolen and slightly optimized from Steams' economy_common.js
    eval_result, script = run_file(f'{CURRENT_PATH}\steam_fee_calculator.js')
    result = script.calculate.update('buyer', amount).split(',')
    # item_fees = result[0]
    item_price = result[1]
    return item_price



################################################
#       convert item_name to item_nameid       #
################################################
def get_item_nameid(item_appid: str, item_name: str, user_agent: str):
    session = HTMLSession()
    response = session.get(url=f'https://steamcommunity.com/market/listings/{item_appid}/{item_name}', headers={
            'User-Agent': user_agent
        })
    response.html.render()
    try:
        item_nameid = response.html.search('Market_LoadOrderSpread( {} );')[0]
    except:
        return False
    return item_nameid


################################################
#          get market item buy orders          #
################################################
def get_item_price(game_price: float, item_nameid: str, currency: str, user_agent: str):
    # receive current buyers orders
    response = get(url='https://steamcommunity.com/market/itemordershistogram?', verify=False, headers = {'User-agent': user_agent}, timeout=3, params={
        'language': 'english',
        'country': 'TR',
        'currency': '1',
        'item_nameid': item_nameid
    }).json()['buy_order_graph']
    # check each order
    result = {}
    safePercent = 0.8
    required = game_price
    totalSaleCount = 0
    bestBuyPrice = 0
    for record in response:
        rAmount = float(record[0])
        rAmountReal = float(get_real_item_price(str(rAmount)))
        bestBuyPrice = rAmountReal
        rQuantity = int(record[1])
        saleCount = 0
        result[str(rAmount)] = [f'{currency}{rAmount} -> {currency}{rAmountReal:.2f}', '0', '0']
        # get the number of items needed for sale
        for _ in range(int(safePercent * rQuantity)):
            totalSaleCount += 1
            saleCount += 1
            required -= rAmountReal
            result[str(rAmount)][1] = str(saleCount)
            result[str(rAmount)][2] = f'{currency}{round(saleCount * rAmountReal, 2)}'
            if required <= 0:
                items = {
                    '': [
                        'Toman: ', str(totalSaleCount), f'Remaining: {currency}{str(round(-required, 2))}'
                    ],
                    ' ': [
                        ' '
                    ]
                }
                items.update(result)
                return (items, bestBuyPrice)



################################################
#       get quantity of available items        #
################################################
def get_num_of_items(item_appid: str, required: int, steam_id: str, steam_key: str):
    # get number of available item in our inventory
    response = None
    for _ in range(2):
        try:
            response = get(url=f'https://api.steampowered.com/IEconItems_{item_appid}/GetPlayerItems/v0001', timeout=3, params={
                'key': steam_key,
                'SteamID': steam_id
            }).json()['result']['items']
        except:
            continue
        finally:
            break
    # compare requested amount with the current inventory
    try:
        if len(response) >= required:
            return True
    except:
        return False



################################################
#         get USDT to IRT exchange Rate        #
################################################
def get_dollar_price(src:str):
    # response = get(url='https://one-api.ir/price', params={
    #     'token': '522846:64c8be288c9f8'
    # }).json()
    # response = response['result']['currencies']['dollar']['h']
    # dollar_price = int(response.replace(',', '')) // 10
    response = get(url=src).json()
    response = response['h']
    dollar_price = int(response.replace(',', '')) // 10
    return (round(dollar_price + getShaparakFee(dollar_price) + getZarinFee(dollar_price) + 1000)), dollar_price



################################################
#        calculate payment gateway fee         #
################################################
# more info >> https://www.zarinpal.com/blog/اصلاح-نظام-کارمزد-تراکنشها
def getShaparakFee(amount):
    if amount < 600000:
        return 120
    if amount >= 600000 and amount <= 20000000:
        return 0.0002 * amount
    else:
        return 4000

def getZarinFee(amount):
    fee = 0.01 * amount
    if fee > 4000:
        return 4000
    else:
        return fee



################################################
#          separation of three digits          #
################################################
def truncate_price(price: str):
    list = [x for x in price]
    reversed_list = []
    x = 0
    for i in reversed(list):
        reversed_list.append(i)
        x += 1
        if (x % 3 == 0 and x != len(price)):
            reversed_list.append(',')
    list = []
    for i in reversed(reversed_list):
        list.append(i)
    return ''.join(list)



################################################
#                     Main                     #
################################################
# get game_name + game_price
wallet_balance = get_wallet_balance()
game = get_game_price(wallet_balance)
# read config file to set item properties
config = {}
with open(f'{CURRENT_PATH}\config.json', 'r') as configFile:
    config = loads(configFile.read())
#Global var        Config PATH                         Default value
item_appid         = config['item']['item_appid']      # 440
item_nameid        = config['item']['item_nameid']     # 1
item_name          = config['item']['item_name']       # Mann Co. Supply Crate Key
params_ua_r        = config['params']['user-agent-R']  # 
params_ua_b        = config['params']['user-agent-B']  # 
safe_percent       = config['terms']['safe-percent']   # 0.8
currency_primary   = config['currencies']['primary']   # TL -> $
currency_secondary = config['currencies']['secondary'] # IRT
params_steamId     = config['params']['steam_id']
params_steamKey    = config['params']['steam_key']
d_src              = config['src']
# display some INFO
info(f'Current wallet balance: {currency_primary}{wallet_balance}')
if game.get('name') == None:
    info(f"Price of the desired product: {currency_primary}{game['price']:.2f}")
else:
    info(f"Name of the selected game: {game['name']}")
    info(f"Price of the selected game: {currency_primary}{str(game['price'])}")
# get item_nameid by name and checking its existence
if len(item_appid) > 0 and len(item_name) > 0 and len(item_nameid) == 0:
    item_nameid = get_item_nameid(item_appid, item_name, params_ua_r)
    if not item_nameid:
        err('item_appid or item_name is not valid. correct the value in config file')
        quit()
    else:
        info(f'item_nameid updated based on new changes: {item_nameid}')
elif not (len(item_appid) > 0 and len(item_name) > 0 and len(item_nameid) > 0):
    err('item_appid or item_name is not valid. correct the values in config file')
    quit()
# get sale items report
orders = get_item_price(game['price'], item_nameid, currency_primary, params_ua_b)
items = orders[0]
# get number of required_items need to sell
required_items = next(iter(items.items()))[-1][1].strip()
# put status about current seller inventory
num_of_items = get_num_of_items(item_appid, int(required_items), params_steamId, params_steamKey)
if num_of_items:
    next(iter(items.items()))[-1][1] = f'Status: {required_items} ✅'
    # info('you can place your order right now')
elif not num_of_items:
    next(iter(items.items()))[-1][1] = f'Status: {required_items} 🟠'
    # info('this amount of items is not available now. contact us before buying')
else:
    next(iter(items.items()))[-1][1] = f'Status: {required_items} 🔘'
    err('our inventory is currently unavailable')
# set IRT finall price
finall_price = get_dollar_price(d_src)
info(f"USD to IRT Exchange Rate: {truncate_price(str(finall_price[1]))}T")
next(iter(items.items()))[-1][0] = truncate_price(str(round(int(required_items) * orders[1] * finall_price[0]))) + f' {currency_secondary}'
# show report table
info('Report:\n')
print(tabulate([items[i] for i in items], headers=['Price', 'Quantity', 'Final value', 'Balance'], tablefmt='rounded_outline', colalign=('center', 'center')), '\n')