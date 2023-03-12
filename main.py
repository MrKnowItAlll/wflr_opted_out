import json
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

optout_input = "0xf2a1f767"

# Flare RPC connection
rpcurl = "https://flare-api.flare.network/ext/C/rpc"
web3 = Web3(Web3.HTTPProvider(rpcurl))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

WFLR_ADDRESS = Web3.toChecksumAddress('0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d')
token_abi = read_json('token_abi.json')
wflr_contract = web3.eth.contract(WFLR_ADDRESS, abi=token_abi)


# Get distribution contract transactions
def get_contract_transactions():
    page = 1
    tx = []
    hasMore = True
    while hasMore:
        req = requests.get("https://flare-explorer.flare.network/api?module=account&action=txlist&address="
                           + "0x9c7A4C83842B29bB4A082b0E689CB9474BD938d0" + "&page=" + "{}".format(page))
        account_transactions_page = req.json()
        if len(account_transactions_page['result']) == 0:
            hasMore = False
        else:
            tx.append(account_transactions_page['result'])
        page += 1
    return tx


# Add Opted out account to the list
def add_account(account):
    accounts = read_json('account.json')
    for acc in accounts:
        if acc['account'] == account:
            return
    accounts.append({
        'account': account
    })
    write_json(accounts, 'account.json')


def get_accounts_from_tx(tx):
    for page in tx:
        for t in page:
            if t['input'] == optout_input and t['txreceipt_status'] == '1':
                add_account(t['from'])


def calculate_opted_amounts():
    tx = get_contract_transactions()
    get_accounts_from_tx(tx)
    total_excluded_amounts = 0
    accounts = read_json('account.json')

    for account in accounts:
        amount = Web3.fromWei(wflr_contract.functions.balanceOf(Web3.toChecksumAddress(account['account'])).call(), 'ether')
        total_excluded_amounts += amount

    return total_excluded_amounts

write_json([], "account.json")
opted_out = round(calculate_opted_amounts(),1)
total_wflr = round(Web3.fromWei(wflr_contract.functions.totalSupply().call(), 'ether'),1)
accounts = read_json('account.json')

print("Number of Accounts OptedOut: {}".format(len(accounts)))
print("Amount of WFLR Opted Out: {}".format(opted_out))
print("Total current WFLR eligible: {}".format(total_wflr - opted_out))

