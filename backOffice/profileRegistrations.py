import os
import sys
from uuid import uuid4

from pymongo import MongoClient
from pymongo import errors

from utils.tools import Helpers

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)

helper = Helpers()
d = helper.read_json_file(file_name='botSetup.json')
hot = helper.read_json_file(file_name='hotWallets.json')


class AccountManager(object):
    """
    Class handling discord user accounts
    """

    def __init__(self):
        self.hot_wallet_addr = hot['xlm']
        # main db connection
        self.connection = MongoClient(d['database']['connection'])

        # Database of bot users
        self.cl_connection = self.connection['CryptoLink']
        self.user_profiles = self.cl_connection.userProfiles
        self.user_wallets = self.cl_connection.userWallets

    @staticmethod
    def get_xlm_payment_id():
        """
        Create user memo when wallet is created for deposits
        :return: STR
        """
        string_length = 20
        random_string = uuid4().hex  # get a random string in a UUID fromat
        memo = random_string.upper().lower()[0:string_length]
        return str(memo)

    def __create_stellar_wallet(self, discord_id: int, discord_username: str, deposit_id):
        """
        Creates stellar wallet for the user
        :param discord_id:
        :param discord_username:
        :return:
        """

        create_multi_wallet = {
            "userId": discord_id,
            "userName": discord_username,
            "depositId": deposit_id,
            "xlm": int(0),
            "clToken": int(0)
        }

        result = self.user_wallets.insert_one(create_multi_wallet)

        if result.inserted_id:
            return True
        else:
            return False

    def update_user_wallet_balance(self, discord_id: int, ticker: str, direction: int, amount: int):
        """
        Updating the user wallet balance used with merchant system
        """
        if direction != 0:
            amount = amount * (-1)

        try:
            self.user_wallets.update_one({"userId": int(discord_id)},
                                         {"$inc": {f"{ticker}": amount},
                                          "$currentDate": {"lastModified": True}})
            return True
        except errors.PyMongoError as e:
            print(f' Could not update user wallet with xlm: {e}')
            return False

    def get_account_details(self, discord_id: int):
        """Get basic account details from user"""
        result = self.user_profiles.find_one({"userId": discord_id},
                                             {"_id": 0})

        return result

    def register_user(self, discord_id: int, discord_username: str):
        """
        Registers user into the system
        :param discord_id: Discord Unique ID
        :param discord_username: Discord Current username
        :return: bool

        """
        stellar_deposit_id = self.get_xlm_payment_id()

        self.__create_stellar_wallet(discord_id=discord_id, discord_username=discord_username,
                                     deposit_id=stellar_deposit_id)
        new_user = {
            "userId": discord_id,
            "userName": discord_username,
            "stellarDepositId": stellar_deposit_id,
            "xlmStats": {"depositsCount": int(0),
                         "totalDeposited": float(0.0),
                         "withdrawalsCount": int(0),
                         "totalWithdrawn": float(0.0),
                         'privateTxSendCount': int(0),
                         "privateTxReceivedCount": int(0),
                         'privateSent': float(0.0),
                         'privateReceived': float(0.0),
                         'publicTxSendCount': int(0),
                         "publicTxReceivedCount": int(0),
                         'publicSent': float(0.0),
                         'publicReceived': float(0.0),
                         'spentOnRoles': float(0.0),
                         'roleTxCount': int(0),
                         'emojiTxCount': int(0),
                         'emojiTotalCount': float(0.0),
                         'multiTxCount': int(0),
                         'multiTotalCount': float(0.0)
                         },

            "clCoinStats": {"depositsCount": int(0),
                            "totalDeposited": float(0.0),
                            "withdrawalsCount": int(0),
                            "totalWithdrawn": float(0.0),
                            'privateTxSendCount': int(0),
                            "privateTxReceivedCount": int(0),
                            'privateSent': float(0.0),
                            'privateReceived': float(0.0),
                            'publicTxSendCount': int(0),
                            "publicTxReceivedCount": int(0),
                            'publicSent': float(0.0),
                            'publicReceived': float(0.0),
                            'spentOnRoles': float(0.0),
                            'roleTxCount': int(0),
                            'emojiTxCount': int(0),
                            'emojiTotalCount': float(0.0),
                            'multiTxCount': int(0),
                            'multiTotalCount': float(0.0)
                            }}

        try:
            self.user_profiles.insert_one(new_user)
            return True
        except errors.PyMongoError:
            return False

    def check_user_existence(self, user_id: int):
        """
        Checks if the user is already registered into the system
        :param user_id: Discord unique ID
        :return: bool
        """

        result = self.user_profiles.find_one({"userId": user_id})

        if result:
            return True
        else:
            return False

    def get_user_memo(self, user_id: int):
        """
        Gets whole user profile data based on the ID
        :param user_id: Unique Discord ID
        :return: dictionary of data
        """
        result = self.user_profiles.find_one({"userId": user_id},
                                             {"_id": 0,
                                              "stellarDepositId": 1})

        return result

    def get_balance_based_on_ticker(self, user_id, ticker):
        balance = self.user_wallets.find_one({"userId": int(user_id)},
                                             {"_id": 0,
                                              f"{ticker}": 1})
        return balance[f'{ticker}']

    def get_all(self):
        users = list(self.user_profiles.find({}))
        return users
