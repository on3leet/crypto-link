class VotingPoolManager:
    """Class dealing with corporate withdrawal history"""

    def __init__(self, connection):
        self.connection = connection
        self.crypto_link = self.connection['CryptoLink']
        self.voting_guild_profiles = self.crypto_link.votingGuildProfiles
        self.voting_pools = self.crypto_link.votingPools
        self.voting_pools_history = self.crypto_link.votingPoolsHistory

    def register_server_for_voting_service(self, data: dict):
        """
        Register server for voting service
        """
        result = self.voting_guild_profiles.insert_one(data)
        if result.inserted_id:
            return True
        else:
            return False

    def check_server_voting_reg_status(self, guild_id: int):
        """
        Check if server has already registered into the voting service
        """
        result = self.voting_guild_profiles.find_one({"guildId": guild_id})
        if result:
            return True
        else:
            return False

    def new_ballot(self, ballot_data: dict):
        """
        Creates new ballot
        """
        result = self.voting_pools.insert_one(ballot_data)
        if result.inserted_id:
            return True
        else:
            return False

    def check_ballot_id(self, ballot_id: int):
        result = self.voting_pools.find_one({"ballotId": ballot_id},
                                            {"_id": 0})
        if result:
            return True
        else:
            return False

    def ballot_to_history(self, ballot_data: dict):
        result = self.voting_pools_history.insert_one(ballot_data)
        if result.inserted_id:
            return True
        else:
            return False

    def remove_ballot(self, ballot_data):
        pass

    def update_ballot_voters(self):
        # TODO make ballot counter
        pass

    def get_ballot_data(self, ballot_id: int, server_id: int):
        result = self.voting_pools.find_one({"guildId": server_id, "ballotId": ballot_id},
                                            {"_id": 0,
                                             "assetCode": 1,
                                             "votesFor": 1,
                                             "votesAgainst": 1,
                                             "voterFor": 1,
                                             "voterAgainst": 1,
                                             "endBallot":1,
                                             "guildId": 1})
        return result

    def get_ballot_rights_role(self, guild_id: int):
        """
        Get the role id used for ballot creation rights
        """
        result = self.voting_guild_profiles.find_one({"guildId": int(guild_id)},
                                                     {"_id": 0,
                                                      "mngRoleId": 1})
        return int(result["mngRoleId"])

    def update_ballot_box(self, ballot_id: int, guild_id: int, new_ballot_data):
        result = self.voting_pools.update_one({"ballotId": ballot_id, "guildId": guild_id},
                                              {"$inc": {new_ballot_data["toIncrement"]},
                                               "$set": {new_ballot_data["toUpdate"]}})
        return result.modified_count > 0

