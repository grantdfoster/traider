import os
import json
import cdp
from dotenv import load_dotenv
from cdp.errors import UnsupportedAssetError
from decimal import Decimal
from typing import Union


# TODO, figure out how to get the private key from the wallet from the seed
class Wallet:
    def __init__(self):
        load_dotenv()
        self.env = os.getenv("ENV")
        self.network = "base-mainnet" if self.is_production() else "base-sepolia"
        self.wallet_file_path = f"wallet-{self.env}.json"
        self.wallet = None
        self.configure_wallet()
        self.faucet()
        print(f"Wallet Balance: {self.balance()}")

    def is_production(self):
        return self.env == "production"

    def is_development(self):
        return self.env == "development"

    def configure_wallet(self):
        if os.path.exists(self.wallet_file_path):
            self.load_wallet()
        else:
            self.create_wallet()

    def load_wallet(self):
        with open(self.wallet_file_path, "r") as file:
            data = json.load(file)
        wallet_id = list(data.keys())[0]
        self.wallet = cdp.Wallet.fetch(wallet_id)
        self.wallet.load_seed(self.wallet_file_path)
        print("Loaded wallet!")

    def create_wallet(self):
        self.wallet = cdp.Wallet.create(network_id=self.network)
        self.wallet.save_seed(self.wallet_file_path)
        print("Saved wallet!")

    def address(self):
        return self.wallet.default_address

    def balance(self, currency="eth"):
        return self.wallet.balance(currency)

    def faucet(self):
        if self.is_development():
            print("Getting funds from faucet...")
            try:
                faucet_transaction = self.wallet.faucet()  # base eth
                print(f"Faucet transaction hash: {faucet_transaction.transaction_hash}")
            except Exception as e:
                print(f"Error getting funds from faucet: {e}")

    # Function to create a new ERC-20 token
    def create_token(self, name, symbol, initial_supply):
        """
        Create a new ERC-20 token.

        Args:
            name (str): The name of the token
            symbol (str): The symbol of the token
            initial_supply (int): The initial supply of tokens

        Returns:
            str: A message confirming the token creation with details
        """
        deployed_contract = self.wallet.deploy_token(name, symbol, initial_supply)
        deployed_contract.wait()
        return f"Token {name} ({symbol}) created with initial supply of {initial_supply} and contract address {deployed_contract.contract_address}"

    # Function to deploy an ERC-721 NFT contract
    def deploy_nft(self, name, symbol, base_uri):
        """
        Deploy an ERC-721 NFT contract.

        Args:
            name (str): Name of the NFT collection
            symbol (str): Symbol of the NFT collection
            base_uri (str): Base URI for token metadata

        Returns:
            str: Status message about the NFT deployment, including the contract address
        """
        try:
            deployed_nft = self.wallet.deploy_nft(name, symbol, base_uri)
            deployed_nft.wait()
            contract_address = deployed_nft.contract_address

            return f"Successfully deployed NFT contract '{name}' ({symbol}) at address {contract_address} with base URI: {base_uri}"

        except Exception as e:
            return f"Error deploying NFT contract: {str(e)}"

    # Function to transfer assets
    def transfer_asset(self, amount, asset_id, destination_address):
        """
        Transfer an asset to a specific address.

        Args:
            amount (Union[int, float, Decimal]): Amount to transfer
            asset_id (str): Asset identifier ("eth", "usdc") or contract address of an ERC-20 token
            destination_address (str): Recipient's address

        Returns:
            str: A message confirming the transfer or describing an error
        """
        try:
            # Check if we're on Base Mainnet and the asset is USDC for gasless transfer
            is_mainnet = self.wallet.network_id == "base-mainnet"
            is_usdc = asset_id.lower() == "usdc"
            gasless = is_mainnet and is_usdc

            # For ETH and USDC, we can transfer directly without checking balance
            if asset_id.lower() in ["eth", "usdc"]:
                transfer = self.wallet.transfer(
                    amount, asset_id, destination_address, gasless=gasless
                )
                transfer.wait()
                gasless_msg = " (gasless)" if gasless else ""
                return f"Transferred {amount} {asset_id}{gasless_msg} to {destination_address}"

            # For other assets, check balance first
            try:
                balance = self.wallet.balance(asset_id)
            except UnsupportedAssetError:
                return f"Error: The asset {asset_id} is not supported on this network. It may have been recently deployed. Please try again in about 30 minutes."

            if balance < amount:
                return f"Insufficient balance. You have {balance} {asset_id}, but tried to transfer {amount}."

            transfer = self.wallet.transfer(amount, asset_id, destination_address)
            transfer.wait()
            return f"Transferred {amount} {asset_id} to {destination_address}"
        except Exception as e:
            return f"Error transferring asset: {str(e)}. If this is a custom token, it may have been recently deployed. Please try again in about 30 minutes, as it needs to be indexed by CDP first."

    # Function to mint an NFT
    def mint_nft(self, contract_address, mint_to):
        """
        Mint an NFT to a specified address.

        Args:
            contract_address (str): Address of the NFT contract
            mint_to (str): Address to mint NFT to

        Returns:
            str: Status message about the NFT minting
        """
        try:
            mint_args = {"to": mint_to, "quantity": "1"}

            mint_invocation = self.wallet.invoke_contract(
                contract_address=contract_address, method="mint", args=mint_args
            )
            mint_invocation.wait()

            return f"Successfully minted NFT to {mint_to}"

        except Exception as e:
            return f"Error minting NFT: {str(e)}"

    # Function to swap assets (only works on Base Mainnet)
    def swap_assets(
        self, amount: Union[int, float, Decimal], from_asset_id: str, to_asset_id: str
    ):
        """
        Swap one asset for another using the trade function.
        This function only works on Base Mainnet.

        Args:
            amount (Union[int, float, Decimal]): Amount of the source asset to swap
            from_asset_id (str): Source asset identifier
            to_asset_id (str): Destination asset identifier

        Returns:
            str: Status message about the swap
        """
        if self.wallet.network_id != "base-mainnet":
            return "Error: Asset swaps are only available on Base Mainnet. Current network is not Base Mainnet."

        try:
            trade = self.wallet.trade(amount, from_asset_id, to_asset_id)
            trade.wait()
            return f"Successfully swapped {amount} {from_asset_id} for {to_asset_id}"
        except Exception as e:
            return f"Error swapping assets: {str(e)}"
            # Function to read data from the blockchain

    def read_contract_data(self, contract_address, method, args=None):
        """
        Read data from a specified contract on the blockchain.

        Args:
            contract_address (str): Address of the contract
            method (str): Method to call on the contract
            args (dict, optional): Arguments to pass to the method. Defaults to None.

        Returns:
            Any: Data returned from the contract method
        """
        try:
            if args is None:
                args = {}

            data = self.wallet.call_contract(
                contract_address=contract_address, method=method, args=args
            )

            return data

        except Exception as e:
            return f"Error reading contract data: {str(e)}"
