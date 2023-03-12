import json
import time
import requests
from web3.middleware import geth_poa_middleware
from web3 import Web3

# json helper funcs
def read_json(path):
    with open(path) as json_file:
        return json.load(json_file)


def write_json(data, path):
    with open(path, 'w') as json_file:
        json.dump(data, json_file, indent=2)


# Flare RPC connection
rpcurl = "https://flare-api.flare.network/ext/C/rpc"
web3 = Web3(Web3.HTTPProvider(rpcurl))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

WFLR_ADDRESS = Web3.toChecksumAddress('0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d')
token_abi = read_json('token_abi.json')
wflr_contract = web3.eth.contract(WFLR_ADDRESS, abi=token_abi)


DIST_ADDRESS = Web3.toChecksumAddress('0x9c7A4C83842B29bB4A082b0E689CB9474BD938d0')
dist_abi = read_json('dist_contract_abi.json')
dist_contract = web3.eth.contract(DIST_ADDRESS, abi=dist_abi)


def get_wflr_holders():
    holders_list = []
    continue_fetch = True
    page = 1
    while continue_fetch:
        try:
            req = requests.get(
                "https://flare-explorer.flare.network/api?module=token&action=getTokenHolders&contractaddress=" +
                "0x1d80c49bbbcd1c0911346656b529df9e5c2f783d" + "&page=" + "{}".format(page))
            holders = req.json()
        except: # Strict RATE LIMIT
            print("Rate limit, waiting 2m for unblock before continuing")
            time.sleep(120)
            req = requests.get(
                "https://flare-explorer.flare.network/api?module=token&action=getTokenHolders&contractaddress=" +
                "0x1d80c49bbbcd1c0911346656b529df9e5c2f783d" + "&page=" + "{}".format(page))
            holders = req.json()
        for holder in holders['result']:
            if Web3.fromWei(int(holder['value']), 'ether') > 1000000:
                holders_list.append({
                    'address': holder['address'],
                    'amount': "{}".format(Web3.fromWei(int(holder['value']), 'ether'))
                })
            else:
                continue_fetch = False
        page += 1
    return holders_list


def is_opted_out(address):
    return dist_contract.functions.optOutCandidate(Web3.toChecksumAddress(address)).call()


# Get WFLR holders(70 pages)
wfl_holders = get_wflr_holders()
write_json(wfl_holders, "wflr_holders.json")

total_opted_out = 0
opted_out = []
for holder in wfl_holders:
    try:
        if is_opted_out(holder['address']):
            total_opted_out += float(holder['amount'])
            opted_out.append(holder)
            print("Opted out SUM: {}".format(total_opted_out))
    except: # Strict RATE LIMIT
        print("Rate limit, waiting 2m for unblock before continuing")
        time.sleep(120)
        if is_opted_out(holder['address']):
            total_opted_out += float(holder['amount'])
            opted_out.append(holder)
            print("Opted out SUM: {}".format(total_opted_out))
write_json(opted_out, "opted_out.json")

total_wflr = round(Web3.fromWei(wflr_contract.functions.totalSupply().call(), 'ether'),1)
print("Number of Accounts OptedOut: {}".format(len(opted_out)))
print("Amount of WFLR Opted Out: {}".format(round(total_opted_out, 1)))
print("Total current WFLR eligible: {}".format(total_wflr - int(total_opted_out)))