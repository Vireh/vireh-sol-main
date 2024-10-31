import os
import re
import requests
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from engines.prompts import get_wallet_decision_prompt
from base58 import b58decode
from solana.keypair import Keypair
from solana.transaction import Transaction
from solana.system_program import SystemProgram, TransferParams

def get_wallet_balance(public_key, rpc_url):
    client = Client(rpc_url)
    balance_response = client.get_balance(public_key)
    if balance_response['result']:
        balance_lamports = balance_response['result']['value']
        return balance_lamports / 1_000_000_000  # Convert lamports to SOL
    return 0.0

def transfer_sol(sender_private_key, to_address, amount_in_sol, rpc_url):
    try:
        # Load the sender's account
        sender_account = Keypair.from_secret_key(b58decode(sender_private_key))
        
        # Initialize Solana client
        client = Client(rpc_url)

        # Prepare the transaction
        transaction = Transaction()
        transaction.add(
            SystemProgram.transfer(
                TransferParams(
                    from_pubkey=sender_account.public_key,
                    to_pubkey=to_address,
                    lamports=int(amount_in_sol * 1_000_000_000)  # Convert SOL to lamports
                )
            )
        )

        # Send the transaction
        response = client.send_transaction(transaction, sender_account, opts=TxOpts(skip_preflight=True))
        signature = response['result']
        
        if signature:
            return signature
        else:
            return "Transaction failed"
    except Exception as e:
        return f"An error occurred: {e}"

def wallet_address_in_post(posts, sender_private_key, llm_api_key: str, rpc_url: str):
    # Convert everything to strings first
    str_posts = [str(post) for post in posts]
    
    # Regex to find Solana addresses (base58) and potential ENS names
    solana_pattern = re.compile(r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b|\b\S+\.sol\b')
    matches = []
    
    for post in str_posts:
        found_matches = solana_pattern.findall(post)
        matches.extend(found_matches)
    
    # Retrieve wallet balance
    public_key = Keypair.from_secret_key(b58decode(sender_private_key)).public_key
    wallet_balance = get_wallet_balance(public_key, rpc_url)
    prompt = get_wallet_decision_prompt(posts, matches, wallet_balance)
    
    # Call the language model to decide on transfers
    response = requests.post(
        url="https://api.hyperbolic.xyz/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {llm_api_key}",
        },
        json={
            "messages": [
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": "Respond only with the wallet address(es) and amount(s) you would like to send to."
                }
            ],
            "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "presence_penalty": 0,
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
        }
    )
    
    if response.status_code == 200:
        print(f"SOL Addresses and amounts chosen from Posts: {response.json()}")
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"Error generating short-term memory: {response.text}")
