"""
COGS: Management of the whole payment system
"""
import os
import sys
import time
from datetime import datetime

from discord import Embed, Colour
from discord.ext import commands
from git import Repo, InvalidGitRepositoryError
from cogs.utils.monetaryConversions import get_normal, get_rates
from utils.customCogChecks import is_animus, is_one_of_gods
from cogs.utils.systemMessaages import CustomMessages
from utils.tools import Helpers

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)

helper = Helpers()
custom_messages = CustomMessages()
auto_channels = helper.read_json_file(file_name='autoMessagingChannels.json')

CONST_STELLAR_EMOJI = '<:stelaremoji:684676687425961994>'
CONST_CORP_TRANSFER_ERROR_TITLE = '__Corporate Transfer Error__'
CONST_MERCHANT_LICENSE_CHANGE = '__Merchant monthly license change information__'
CONST_WARNING_TITLE = f':warning: __Restricted area__ :warning: '
CONST_WARNING_MESSAGE = f'You do not have rights to access this are of the bot'
CONST_FEE_INFO = '__Stellar Lumen withdrawal fee information__'

# Extensions integrated into Crypto Link
extensions = ['cogs.help', 'cogs.transactions', 'cogs.accounts',
              'cogs.system', 'cogs.withdrawals',
              'cogs.guildMerchant', 'cogs.consumer', 'cogs.automatic', 'cogs.guildOwners']


class BotManagementCommands(commands.Cog):
    def __init__(self, bot):
        """
        Passing discord bot instance
        """
        self.bot = bot
        self.backoffice = bot.backoffice
        self.command_string = bot.get_command_str()

    async def send_token_stats(self, ctx, cl_on_chain: dict, cl_off_chain: dict, token: str):
        """
        Send stats on tokens
        """
        on_stats = Embed(title='__Crypto Link On Chain__',
                         colour=Colour.greyple())
        on_stats.add_field(name=f'Total Deposits',
                           value=f'{cl_on_chain["depositCount"]}')
        on_stats.add_field(name=f'Total Deposited',
                           value=f'{cl_on_chain["depositAmount"]} XLM')
        on_stats.add_field(name=f'Total Withdrawals',
                           value=f'{cl_on_chain["withdrawalCount"]}')
        on_stats.add_field(name=f'Total Withdrawn',
                           value=f'{cl_on_chain["withdrawnAmount"]} XLM')
        await ctx.author.send(embed=on_stats)

        off_chain = Embed(title=f'__Crypto Link off chain__',
                          colour=Colour.greyple())
        off_chain.add_field(name=f'Total Transactions done',
                            value=f'{cl_off_chain["totalTx"]}')
        off_chain.add_field(name=f'Total {token} moved',
                            value=f'{round(cl_off_chain["totalMoved"], 7)}')
        off_chain.add_field(name=f'Total Public TX',
                            value=f'{cl_off_chain["totalPublicCount"]}')
        off_chain.add_field(name=f'Total Public Moved',
                            value=f'{round(cl_off_chain["totalPublicMoved"], 7)}')
        off_chain.add_field(name=f'Total Private TX',
                            value=f'{cl_off_chain["totalPrivateCount"]}')
        off_chain.add_field(name=f'Total Private Moved',
                            value=f'{round(cl_off_chain["totalPrivateMoved"], 7)}')
        off_chain.add_field(name=f'Total Emoji Tx',
                            value=f'{cl_off_chain["totalEmojiTx"]}')
        off_chain.add_field(name=f'Total Emoji Moved',
                            value=f'{cl_off_chain["totalEmojiMoved"]}')
        off_chain.add_field(name=f'Total Multi Tx',
                            value=f'{cl_off_chain["multiTxCount"]}')
        off_chain.add_field(name=f'Total Multi moved',
                            value=f'{cl_off_chain["multiTxMoved"]}')
        off_chain.add_field(name=f'Total Merchant Tx',
                            value=f'{cl_off_chain["merchantPurchases"]}')
        off_chain.add_field(name=f'Total Merchant moved',
                            value=f'{cl_off_chain["merchantMoved"]}')
        await ctx.author.send(embed=off_chain)

    @staticmethod
    def filter_db_keys(fee_type: str):

        if fee_type == 'withdrawal_fees':
            fee_type = "Coin withdrawal fees"
        elif fee_type == 'merch_transfer_cost':
            fee_type = "Merchant wallet withdrawal fee"
        elif fee_type == 'merch_license':
            fee_type = "Merchant Monthly License cost"
        elif fee_type == 'merch_transfer_min':
            fee_type = 'Merchant minimum transfer'

        return fee_type

    #############################  Crypto Link Commands #############################

    @commands.command()
    @commands.check(is_one_of_gods)
    async def gods(self, ctx):
        title = ':man_mage:  __Crypto Link commands__ :man_mage:  '
        description = "All commands and their subcommands to operate with the Crypto Link System as administrator" \
                      " owner of the system"
        list_of_values = [
            {"name": "Crypto Link off-chain wallet", "value": f"{self.command_string}cl"},
            {"name": "Crypto Link system backend", "value": f"{self.command_string}system"},
            {"name": "Crypto Link COG Management", "value": f"{self.command_string}cogs"},
            {"name": "Crypto Link HOT Wallet Management", "value": f"{self.command_string}hot"},
            {"name": "Crypto Link fee management", "value": f"{self.command_string}fee"}

        ]

        await custom_messages.embed_builder(ctx=ctx, title=title, description=description, data=list_of_values,
                                            destination=ctx.message.author, thumbnail=self.bot.user.avatar_url)

    @commands.group()
    @commands.check(is_one_of_gods)
    async def cl(self, ctx):
        """
        Entry point for cl sub commands
        """

        if ctx.invoked_subcommand is None:
            title = ':joystick: __Crypto Link commands__:joystick: '
            description = "All commands and their subcommands to operate with the Crypto Link System as administrator" \
                          " owner of the system"
            list_of_values = [
                {"name": "Check Corporate Balance", "value": f"{self.command_string}cl balance"},
                {"name": "Withdrawing XLM from Corp to personal",
                 "value": f"{self.command_string}cl sweep"},
                {"name": "Statistics of crypto link system",
                 "value": f"{self.command_string}cl stats"},
                {"name": "Other categories",
                 "value": f"{self.command_string}system\n"
                          f"{self.command_string}manage\n"
                          f"{self.command_string}hot"}
            ]

            await custom_messages.embed_builder(ctx=ctx, title=title, description=description, data=list_of_values,
                                                destination=ctx.message.author, thumbnail=self.bot.user.avatar_url)

    @cl.command(aliases=['balance'])
    async def bal(self, ctx):
        """
        Check the off-chain balance status of Crypto Link system
        """
        data = self.backoffice.bot_manager.get_bot_wallets_balance()
        values = Embed(title="Balance of Crypto-Link Off chain balance",
                       description="Current state of Crypto Link Lumen wallet",
                       color=Colour.blurple())
        for bal in data:
            ticker = bal['ticker']
            conversion = int(bal["balance"])
            normal = get_normal(conversion, 7)
            values.add_field(name=ticker.upper(),
                             value=f'{normal}',
                             inline=False)
        await ctx.channel.send(embed=values)

    @cl.command()
    async def stats(self, ctx, token: str = None):
        """
        Statistical information on Crypto Link system
        """
        if not token:
            data = self.backoffice.stats_manager.get_all_stats()
            cl_off_chain = data["xlm"]["offChain"]
            cl_on_chain = data['xlm']['onChain']

            guilds = await self.bot.fetch_guilds(limit=150).flatten()
            reach = len(self.bot.users)
            world = Embed(title='__Crypto Link__',
                          colour=Colour.magenta(),
                          timestamp=datetime.utcnow())
            world.add_field(name='Guild reach',
                            value=f'{len(guilds)}',
                            inline=False)
            world.add_field(name='Member reach',
                            value=f'{reach}',
                            inline=False)
            await ctx.author.send(embed=world)

            await self.send_token_stats(ctx=ctx, cl_on_chain=cl_on_chain, cl_off_chain=cl_off_chain)
        else:
            off_chain_stats, on_chain_stats = self.bot.stats_manager.get_token_stats_global(token=token)
            await self.send_token_stats(ctx=ctx, cl_on_chain=on_chain_stats, cl_off_chain=off_chain_stats)

    @cl.command()
    async def bridges(self, ctx):
        stats = self.backoffice.stats_manager.get_top_builders(limit=10)

        bridges = '\U0001F309'
        string = ''
        rank = 1
        for u in stats:
            try:
                username = u['userName']
                brdiges = u["bridges"]
                line = f'{rank}.' + ' ' + f'***{username}***' + ' ' + f'\n{brdiges}' + ' \n'
                string += line
                rank += 1
            except KeyError:
                pass

        bridges_embed = Embed(title=f'Stats')
        bridges_embed.add_field(name="Top 5",
                                value=f"{bridges} Bridge Builders Hall of Fame {bridges}\n" + f'{string}')
        await ctx.author.send(embed=bridges_embed)

    @cl.command()
    @commands.check(is_one_of_gods)
    async def sweep(self, ctx, ticker: str):
        """
        Transfer funds from Crypto Link to develop wallet
        """

        balance = int(self.backoffice.bot_manager.get_bot_wallet_balance_by_ticker(ticker=ticker))
        print(balance)
        if balance > 0:  # Check if balance greater than -
            # Checks if recipient exists
            if not self.backoffice.account_mng.check_user_existence(user_id=ctx.message.author.id):
                self.backoffice.account_mng.register_user(discord_id=ctx.message.author.id,
                                                          discord_username=f'{ctx.message.author}')

            if self.backoffice.stellar_manager.update_stellar_balance_by_discord_id(
                    discord_id=ctx.message.author.id,
                    stroops=int(balance), direction=1):
                # Deduct the balance from the community balance
                if self.backoffice.bot_manager.update_lpi_wallet_balance(amount=balance, wallet="xlm", direction=2):
                    # Store in history and send notifications to owner and to channel
                    dec_point = 7
                    normal_amount = get_normal(str(balance), decimal_point=dec_point)

                    # Store into the history of corporate transfers
                    self.backoffice.corporate_hist_mng.store_transfer_from_corp_wallet(time_utc=int(time.time()),
                                                                                       author=f'{ctx.message.author}',
                                                                                       destination=int(
                                                                                           ctx.message.author.id),
                                                                                       amount_atomic=balance,
                                                                                       amount=normal_amount,
                                                                                       currency='xlm')

                    # notification to corp account discord channel
                    stellar_channel_id = auto_channels['stellar']
                    stellar_notify_channel = self.bot.get_channel(id=int(stellar_channel_id))

                    await custom_messages.send_transfer_notification(ctx=ctx, member=ctx.message.author,
                                                                     sys_channel=stellar_notify_channel,
                                                                     normal_amount=normal_amount,
                                                                     emoji=CONST_STELLAR_EMOJI,
                                                                     chain_name='Stellar Chain')

                else:
                    # Revert the user balance if community balance can not be updated
                    self.backoffice.stellar_manager.update_stellar_balance_by_discord_id(
                        discord_id=ctx.message.author.id,
                        stroops=int(balance), direction=2)

                    message = f"Stellar funds could not be deducted from corporate account. Please try again later"
                    await custom_messages.system_message(ctx, color_code=1, message=message, destination=0,
                                                         sys_msg_title=CONST_CORP_TRANSFER_ERROR_TITLE)
            else:
                message = f"Stellar funds could not be moved from corporate account to {ctx.message.author}." \
                          f"Please try again later "
                await custom_messages.system_message(ctx, color_code=1, message=message, destination=0,
                                                     sys_msg_title=CONST_CORP_TRANSFER_ERROR_TITLE)
        else:
            message = f"You can not sweep the account as its balance is 0.0000000 {CONST_STELLAR_EMOJI}"
            await custom_messages.system_message(ctx, color_code=1, message=message, destination=0,
                                                 sys_msg_title=CONST_CORP_TRANSFER_ERROR_TITLE)

    #############################  Crypto Link System #############################

    @commands.group(aliases=["sys"])
    @commands.check(is_one_of_gods)
    async def system(self, ctx):
        if ctx.invoked_subcommand is None:
            value = [{'name': '__Turning bot off__',
                      'value': f"***{self.command_string}system off*** "},
                     {'name': '__Pulling update from Github__',
                      'value': f"***{self.command_string}system update*** "},
                     ]

            await custom_messages.embed_builder(ctx, title='Available sub commands for system',
                                                description='Available commands under category ***system***',
                                                data=value)

    @system.command(aliases=["stop"])
    async def off(self, ctx):
        guild = await self.bot.fetch_guild(guild_id=756132394289070102)
        role = guild.get_role(role_id=773212890269745222)
        channel = self.bot.get_channel(id=int(773157463628709898))
        message = f':robot: {role.mention} I am going Offline for Maintenance'
        await channel.send(content=message)
        await self.bot.close()
        sys.exit(0)

    @system.command()
    async def update(self, ctx):
        notification_str = ''
        current_time = datetime.utcnow()
        try:
            repo = Repo()  # Initiate repo
            git = repo.git
            git.pull()
            notification_str += 'GIT UPDATE STATUS\n' \
                                ' Latest commits pulled :green_circle: \n' \
                                '=============================================\n'
        except InvalidGitRepositoryError:
            notification_str += 'GIT UPDATE: There has been an error while pulling latest commits :red_circle:  \n' \
                                'Error: Git Repository could not be found\n' \
                                '=============================================\n'
            await ctx.author.send(content=notification_str)

        notification_str += 'STATUS OF COGS AFTER RELOAD\n'
        for extension in extensions:
            print(f'Trying to load extension {extension}')
            try:
                self.bot.unload_extension(f'{extension}')
                self.bot.load_extension(f'{extension}')
                notification_str += f'{extension} :green_circle:  \n'
                print('success')
                print('=========')
            except Exception as e:
                notification_str += f'{extension} :red_circle:' \
                                    f'Error: {e} \n'
                print('failed')
                print('=========')
        notification_str += 'GIT UPDATE STATUS\n' \
                            ' Latest commits pulled :green_circle: \n' \
                            '=============================================\n'
        load_status = Embed(title='System update message',
                            description='Status after git update',
                            colour=Colour.green())
        load_status.add_field(name='Time of execution',
                              value=f'{current_time}',
                              inline=False)
        load_status.add_field(name='Status Message',
                              value=notification_str,
                              inline=False)
        await ctx.author.send(embed=load_status)

    #############################  Token management #############################
    @commands.group()
    @commands.check(is_one_of_gods)
    async def tokens(self, ctx):
        if ctx.invoked_subcommand is None:
            value = [{'name': '__Add new support__',
                      'value': f"***{self.command_string}tokens new <issuer> <tick>*** "},
                     {'name': '__Add new with trust DONE!__',
                      'value': f"***{self.command_string}tokens trusted <issuer> <amount>*** "},
                     {'name': '__Update token profiles__',
                      'value': f"***{self.command_string}tokens profile*** "},
                     ]

            await custom_messages.embed_builder(ctx, title='Available sub commands for system',
                                                description='Available commands under category ***system***',
                                                data=value)

    @tokens.group()
    async def profile(self, ctx):
        if ctx.invoked_subcommand is None:
            value = [{'name': '__Set homepage __',
                      'value': f"***{self.command_string}tokens profile home <issuer> <tick> <homepage address>*** "},
                     {'name': '__Set Expert__',
                      'value': f"***{self.command_string}tokens profile expert <issuer> <tick> <expert address>***"},
                     {'name': '__Set Token Withdrawal Limit__',
                      'value': f"***{self.command_string}tokens profile withdrawal <issuer> <tick> <amount limit float>***"},
                     {'name': '__Set Token TOML link__',
                      'value': f"***{self.command_string}tokens profile toml <issuer> <tick> <toml https>***"}
                     ]

            await custom_messages.embed_builder(ctx, title='Available sub commands for system',
                                                description='Available commands under category ***system***',
                                                data=value)
        pass

    @profile.command()
    async def toml(self, ctx, issuer: str, asset_code: str, address: str):
        if self.bot.backoffice.token_manager.check_token_existence(issuer=issuer.upper(), code=asset_code.lower()):
            if self.bot.backoffice.token_manager.update_token_profile(issuer=issuer.upper(),
                                                                      asset_code=asset_code.lower(),
                                                                      to_update={"toml": address}):

                await ctx.channel.send(
                    content=f'You have successfully updated the TOML link for token {asset_code.upper()} {issuer}')
            else:
                await ctx.channel.send(
                    content="There has been issue in the backend while trying to update token details")
        else:
            await ctx.channel.send(content='This token is not registered in DB')

    @profile.command()
    async def withdrawal(self, ctx, issuer: str, asset_code: str, amount: float):
        if self.bot.backoffice.token_manager.check_token_existence(issuer=issuer.upper(), code=asset_code.lower()):
            amount_micro = int(amount * (10 ** 7))
            if self.bot.backoffice.token_manager.update_token_profile(issuer=issuer.upper(),
                                                                      asset_code=asset_code.lower(),
                                                                      to_update={"minimumWithdrawal": amount_micro}):

                await ctx.channel.send(
                    content=f'You have successfully updated the minimum withdrawal {amount_micro / (10 ** 7)} for token {asset_code.upper()} {issuer}')
            else:
                await ctx.channel.send(
                    content="There has been issue in the backend while trying to update token details")
        else:
            await ctx.channel.send(content='This token is not registered in DB')

    @profile.command()
    async def expert(self, ctx, issuer: str, asset_code: str, address: str):
        if self.bot.backoffice.token_manager.check_token_existence(issuer=issuer.upper(), code=asset_code.lower()):
            if self.bot.backoffice.token_manager.update_token_profile(issuer=issuer.upper(),
                                                                      asset_code=asset_code.lower(),
                                                                      to_update={"expert": address}):

                await ctx.channel.send(
                    content=f'You have successfully updated the expert link for token {asset_code.upper()} {issuer}')
            else:
                await ctx.channel.send(
                    content="There has been issue in the backend while trying to update token details")
        else:
            await ctx.channel.send(content='This token is not registered in DB')

    @profile.command()
    async def homepage(self, ctx, issuer: str, asset_code: str, address: str):
        if self.bot.backoffice.token_manager.check_token_existence(issuer=issuer.upper(), code=asset_code.lower()):
            if self.bot.backoffice.token_manager.update_token_profile(issuer=issuer.upper(),
                                                                      asset_code=asset_code.lower(),
                                                                      to_update={"homepage": address}):

                await ctx.channel.send(
                    content=f'You have successfully updated the hoemapage link for token {asset_code.upper()} {issuer}')
            else:
                await ctx.channel.send(
                    content="There has been issue in the backend while trying to update token details")
        else:
            await ctx.channel.send(content='This token is not registered in DB')

    @tokens.command()
    async def new(self, ctx, asset_issuer: str, asset_code: str):
        """Ads support for ne token"""
        try:
            assets = self.bot.backoffice.stellar_wallet.server.assets()
            asset = assets.for_code(asset_code=asset_code.upper()).for_issuer(
                asset_issuer=asset_issuer.upper()).call()
            asset_data = asset["_embedded"]['records'][0]
            if asset_data:
                data = self.bot.backoffice.stellar_wallet.establish_trust(asset_issuer=asset_data["asset_issuer"],
                                                                          token=asset_data["asset_code"])

                if data[0]:
                    token = {
                        "toml": asset_data["_links"]["toml"]["href"],
                        "assetCode": asset_data["asset_code"].lower(),
                        "assetIssuer": asset_data["asset_issuer"],
                        "assetType": asset_data["asset_type"],
                        "pagingToken": asset_data["paging_token"],
                        "coingGeckoListing": False,
                        "minimumWithdrawal": 100000000,
                        "ownerId": None,
                        "ownerName": None,
                        "expert": None,
                        "homepage": None,
                    }

                    # insert new token into database
                    await ctx.author.send(content="Trying to insert new token data")
                    if self.bot.backoffice.token_manager.insert_new_token(token):
                        await ctx.author.send(content="Details of new token to db created")
                        # Create CL wallet for fee collections
                        await ctx.author.send(content="Trying to create cl wallets")
                        if self.bot.backoffice.bot_manager.create_cl_wallet(
                                {"ticker": asset_data["asset_code"].lower(), "balance": int(0),
                                 "issuer": asset_data["asset_issuer"]}):
                            await ctx.author.send(content="Cl wallet for fees created successfully")
                            # fee category
                            # Update fee categories
                            await ctx.author.send(content="Trying to update fee structures")
                            if self.bot.backoffice.bot_manager.manage_fees_and_limits(key="withdrawals",
                                                                                      data_to_update={
                                                                                          f"fee_list.{asset_data['asset_code'].lower()}": 1.0}):
                                await ctx.author.send(content="New fee category created")

                                all_guild_ids = self.bot.backoffice.guild_profiles.get_all_guild_ids()

                                if all_guild_ids:
                                    guild_stats_data = {f"{asset_data['asset_code'].lower()}": {"volume": float(0.0),
                                                                                                "txCount": int(0),
                                                                                                "privateCount": int(0),
                                                                                                "publicCount": int(0),
                                                                                                "roleTxCount": int(0),
                                                                                                "emojiTxCount": int(0),
                                                                                                "multiTxCount": int(0)}
                                                        }

                                    # For every registered guild add new token for stats collections
                                    await ctx.author.send(content="Trying to update guild stats")
                                    for g_id in all_guild_ids:
                                        await self.bot.backoffice.guild_profiles.update_guild_profile(
                                            guild_id=int(g_id["guildId"]),
                                            data_to_update=guild_stats_data)

                                    await ctx.author.send(content="All guilds have been updated with stats")

                                # update crypot link stats
                                stats_off = {
                                    "ticker": asset_data['asset_code'].lower(),
                                    "totalTx": int(0),
                                    "totalMoved": float(0.0),
                                    "totalPrivateCount": int(0),
                                    "totalPrivateMoved": float(0.0),
                                    "totalPublicCount": int(0),
                                    "totalPublicMoved": float(0.0),
                                    "totalEmojiTx": int(0),
                                    "totalEmojiMoved": float(0),
                                    "multiTxCount": int(0),
                                    "multiTxMoved": float(0.0),
                                    "merchantPurchases": int(0),
                                    "merchantMoved": float(0)
                                }
                                await ctx.author.send(content="Updating crypto link stats off chain")
                                if self.bot.backoffice.stats_manager.register_new_off_chain_bot_stat(stats_off):
                                    await ctx.author.send(content="Global off chain stats for token created")

                                    stats_on_chain = {

                                        "ticker": asset_data['asset_code'].lower(),
                                        "depositCount": 0,
                                        "withdrawalCount": 0,
                                        "depositAmount": 0.0,
                                        "withdrawnAmount": 0.0,
                                        "issuer": asset_data["asset_issuer"]
                                    }
                                    if self.bot.backoffice.stats_manager.register_new_on_chain_bot_stats(
                                            stats_on_chain):

                                        # Send to explorer the support information for new coin
                                        load_channels = [self.bot.get_channel(id=int(chn)) for chn in
                                                         self.bot.backoffice.guild_profiles.get_all_explorer_applied_channels()]

                                        explorer_msg = f':new: :coin: New token integrated with asset code ***{asset_data["asset_code"]}***' \
                                                       f'from issuer ***{asset_data["asset_issuer"]}*** :rocket:'

                                        await custom_messages.explorer_messages(applied_channels=load_channels,
                                                                                message=explorer_msg)
                                        await ctx.author.send(content='Integration completed')
                                    else:
                                        msg = "On chain stats collector document could not be created"
                                        await ctx.author.send(content=msg)
                            else:
                                msg = "There has has been error in creating fees into database"
                                await ctx.author.send(content=msg)
                        else:
                            msg = "Crypto Link off-chain wallet could not be created"
                            await ctx.author.send(content=msg)
                    else:
                        msg = ("System could not store token data into database")
                        await ctx.author.send(content=msg)
                else:
                    await ctx.channel.send(content='There has been an issue with executing the trust op in package')
                    await ctx.channel.send(content=f'{data[1]}')
            else:
                await ctx.send(content=f'Asset was not found please recheck issuer and asset code')
        except Exception as e:
            await ctx.send(content=f'It seems like there hass been an issue\n'
                                   f'```{e}```')

    @tokens.command()
    async def trusted(self, ctx, asset_issuer: str, asset_code: str):
        data = self.backoffice.stellar_wallet.get_account_assets()
        assets = data["balances"]
        for asset in assets:
            if "asset_code" in asset:
                if asset_code == asset_code.upper() and asset["asset_issuer"] == asset_issuer.upper():
                    details = self.bot.backoffice.stellar_wallet.get_asset_details(asset_code=asset_code.upper(),
                                                                                   asset_issuer=asset_issuer.upper())
                    asset_data = details["_embedded"]['records'][0]
                    token = {
                        "toml": asset_data["_links"]["toml"]["href"],
                        "assetCode": asset_data["asset_code"].lower(),
                        "assetIssuer": asset_data["asset_issuer"],
                        "assetType": asset_data["asset_type"],
                        "pagingToken": asset_data["paging_token"],
                        "coingGeckoListing": False,
                        "minimumWithdrawal": 100000000,
                        'webPage': None,
                        "ownerId": None,
                        "ownerName": None,
                        "expert": None,
                        "homepage": None
                    }

                    # insert new token into database
                    await ctx.author.send(content="Trying to insert new token data")
                    if self.bot.backoffice.token_manager.insert_new_token(token):
                        await ctx.author.send(content="Details of new token to db created")
                        # Create CL wallet for fee collections
                        await ctx.author.send(content="Trying to create cl wallets")
                        if self.bot.backoffice.bot_manager.create_cl_wallet(
                                {"ticker": asset_data["asset_code"].lower(), "balance": int(0),
                                 "issuer": asset_data["asset_issuer"]}):
                            await ctx.author.send(content="Cl wallet for fees created successfully")
                            # fee category
                            # Update fee categories
                            await ctx.author.send(content="Trying to update fee structures")
                            if self.bot.backoffice.bot_manager.manage_fees_and_limits(key="withdrawals",
                                                                                      data_to_update={
                                                                                          f"fee_list.{asset_data['asset_code'].lower()}": 1.0}):
                                await ctx.author.send(content="New fee category created")

                                all_guild_ids = self.bot.backoffice.guild_profiles.get_all_guild_ids()

                                if all_guild_ids:
                                    guild_stats_data = {f"{asset_data['asset_code'].lower()}": {"volume": float(0.0),
                                                                                                "txCount": int(0),
                                                                                                "privateCount": int(0),
                                                                                                "publicCount": int(0),
                                                                                                "roleTxCount": int(0),
                                                                                                "emojiTxCount": int(0),
                                                                                                "multiTxCount": int(0)}
                                                        }

                                    # For every registered guild add new token for stats collections
                                    await ctx.author.send(content="Trying to update guild stats")
                                    for g_id in all_guild_ids:
                                        await self.bot.backoffice.guild_profiles.update_guild_profile(
                                            guild_id=int(g_id["guildId"]),
                                            data_to_update=guild_stats_data)

                                    await ctx.author.send(content="All guilds have been updated with stats")

                                # update crypto link stats
                                stats_off = {
                                    "ticker": asset_data['asset_code'].lower(),
                                    "totalTx": int(0),
                                    "totalMoved": float(0.0),
                                    "totalPrivateCount": int(0),
                                    "totalPrivateMoved": float(0.0),
                                    "totalPublicCount": int(0),
                                    "totalPublicMoved": float(0.0),
                                    "totalEmojiTx": int(0),
                                    "totalEmojiMoved": float(0),
                                    "multiTxCount": int(0),
                                    "multiTxMoved": float(0.0),
                                    "merchantPurchases": int(0),
                                    "merchantMoved": float(0)
                                }
                                await ctx.author.send(content="Updating crypto link stats off chain")
                                if self.bot.backoffice.stats_manager.register_new_off_chain_bot_stat(stats_off):
                                    await ctx.author.send(content="Global off chain stats for token created")

                                    stats_on_chain = {

                                        "ticker": asset_data['asset_code'].lower(),
                                        "depositCount": 0,
                                        "withdrawalCount": 0,
                                        "depositAmount": 0.0,
                                        "withdrawnAmount": 0.0,
                                        "issuer": asset_data["asset_issuer"]
                                    }
                                    if self.bot.backoffice.stats_manager.register_new_on_chain_bot_stats(
                                            stats_on_chain):

                                        # Send to explorer the support information for new coin
                                        load_channels = [self.bot.get_channel(id=int(chn)) for chn in
                                                         self.bot.backoffice.guild_profiles.get_all_explorer_applied_channels()]

                                        explorer_msg = f':new: :coin: New token integrated with asset code ***{asset_data["asset_code"]}***' \
                                                       f'from issuer ***{asset_data["asset_issuer"]}*** :rocket:'

                                        await custom_messages.explorer_messages(applied_channels=load_channels,
                                                                                message=explorer_msg)
                                        await ctx.author.send(content='Integration completed')
                                    else:
                                        msg = "On chain stats collector document could not be created"
                                        await ctx.author.send(content=msg)

                            else:
                                await ctx.author.send(content="Withdrawals and limits could not be created")
                        else:
                            await ctx.author.send(content="Wallet could not be created")
                    else:
                        await ctx.author.send(content="Data for new token could not be set in DB ")

    # @commands.check(is_one_of_gods)
    # async def cogs(self, ctx):
    #     if ctx.invoked_subcommand is None:
    #         value = [{'name': '__List all cogs__',
    #                   'value': f"***{self.command_string}cogs list*** "},
    #                  {'name': '__Loading specific cog__',
    #                   'value': f"***{self.command_string}cogs load <cog name>*** "},
    #                  {'name': '__Unloading specific cog__',
    #                   'value': f"***{self.command_string}cogs unload <cog name>*** "},
    #                  {'name': '__Reload all cogs__',
    #                   'value': f"***{self.command_string}cogs reload*** "}
    #                  ]
    #
    #         await custom_messages.embed_builder(ctx, title='Available sub commands for system',
    #                                             description='Available commands under category ***system***',
    #                                             data=value)

    # @cogs.command()
    # async def load(self, ctx, extension: str):
    #     """
    #     Load specific COG == Turn ON
    #     :param ctx: Context
    #     :param extension: Extension Name as str
    #     :return:
    #     """
    #     try:
    #         self.bot.load_extension(f'cogs.{extension}')
    #         embed_unload = Embed(name='Boom',
    #                              title='Cogs management',
    #                              colour=Colour.green())
    #         embed_unload.add_field(name='Extension',
    #                                value=f'You have loaded ***{extension}*** COGS')
    #
    #         await ctx.channel.send(embed=embed_unload)
    #     except Exception as error:
    #         await ctx.channel.send(content=error)

    # @cogs.command()
    # async def unload(self, ctx, extension: str):
    #     """
    #     Unloads COG == Turns OFF commands under certain COG
    #     :param ctx: Context
    #     :param extension: COG Name
    #     :return:
    #     """
    #     try:
    #         self.bot.unload_extension(f'cogs.{extension}')
    #         embed_unload = Embed(name='Boom',
    #                              title='Cogs management',
    #                              colour=Colour.red())
    #         embed_unload.add_field(name='Extension',
    #                                value=f'You have unloaded ***{extension}*** COGS')
    #
    #         await ctx.channel.send(embed=embed_unload)
    #     except Exception as error:
    #         await ctx.channel.send(content=error)
    #
    # @cogs.command()
    # async def list(self, ctx):
    #     """
    #     List all cogs implemented in the system
    #     """
    #     cog_list_embed = Embed(title='All available COGS',
    #                            description='All available cogs and their description',
    #                            colour=Colour.green())
    #     for cg in extensions:
    #         cog_list_embed.add_field(name=cg,
    #                                  value='==============',
    #                                  inline=False)
    #     await ctx.channel.send(embed=cog_list_embed)
    #
    # @cogs.command()
    # async def reload(self, ctx):
    #     """
    #      Reload all cogs
    #     """
    #     notification_str = ''
    #     ext_load_embed = Embed(title='System message',
    #                            description='Status of the cogs after reload',
    #                            colour=Colour.blue())
    #     for extension in extensions:
    #         try:
    #             self.bot.unload_extension(f'{extension}')
    #             self.bot.load_extension(f'{extension}')
    #             notification_str += f'{extension} :smile: \n'
    #         except Exception as e:
    #             notification_str += f'{extension} :angry: {e}\n'
    #
    #     ext_load_embed.add_field(name='Status',
    #                              value=notification_str)
    #     await ctx.channel.send(embed=ext_load_embed)

    #############################  Crypto Link Hot Wallet #############################

    @commands.group()
    @commands.check(is_animus)
    async def hot(self, ctx):
        """
        Command entry point for hot wallet functions
        """
        if ctx.invoked_subcommand is None:
            value = [{'name': f'***{self.command_string}hot balance*** ',
                      'value': "Returns information from wallet RPC on stellar balance"}
                     ]
            await custom_messages.embed_builder(ctx, title='Querying hot wallet details',
                                                description="All available commands to operate with hot wallets",
                                                data=value, destination=1)

    @hot.command()
    async def balance(self, ctx):
        """
        Check Stellar hot wallet details
        """
        data = self.backoffice.stellar_wallet.get_stellar_hot_wallet_details()

        if data:
            bal_start = Embed(title='Stellar hot wallet details',
                              description=f'{data["account_id"]}')

            await ctx.author.send(embed=bal_start)

            for coin in data["balances"]:
                if not coin.get('asset_code'):
                    cn = 'XLM'
                else:
                    cn = coin["asset_code"]

                coin_nfo = Embed(title=f'Details for {cn}')
                coin_nfo.add_field(name=f'Balance',
                                   value=f"{coin['balance']}")

                await ctx.author.send(embed=coin_nfo)
        else:
            sys_msg_title = 'Stellar Wallet Query Server error'
            message = 'Status of the wallet could not be obtained at this moment'
            await custom_messages.system_message(ctx=ctx, color_code=1, message=message, destination=1,
                                                 sys_msg_title=sys_msg_title)

    #############################  Crypto Link Fee management #############################

    @commands.command()
    async def fees(self, ctx):
        fees = self.backoffice.bot_manager.get_all_fees()
        fee_info = Embed(title='Applied fees for system',
                         description='State of fees for each segment of the bot',
                         colour=Colour.blue())

        rates = get_rates(coin_name='stellar')
        for data in fees:
            if not data.get('fee_list'):
                # conversion = convert_to_currency(amount=float(data['fee']), coin_name='stellar')
                # fee_type = self.filter_db_keys(fee_type=data['type'])
                #
                # fee_info.add_field(name=fee_type,
                #                    value=f"XLM = {conversion['total']} {CONST_STELLAR_EMOJI}\n"
                #                          f"Dollar = {data['fee']}$",
                #                    inline=False)
                pass
            else:
                fee_type = self.filter_db_keys(fee_type=data['type'])
                fee_info.add_field(name=fee_type,
                                   value=f"{data['fee_list']['xlm']} XLM",
                                   inline=False)

        fee_info.add_field(name='Conversion rates',
                           value=f'{rates["stellar"]["usd"]} :dollar: / {CONST_STELLAR_EMOJI}\n'
                                 f'{rates["stellar"]["eur"]} :euro: / {CONST_STELLAR_EMOJI}')

        fee_info.set_thumbnail(url=self.bot.user.avatar_url)
        fee_info.set_footer(text='Conversion rates provided by CoinGecko',
                            icon_url='https://static.coingecko.com/s/thumbnail-'
                                     '007177f3eca19695592f0b8b0eabbdae282b54154e1be912285c9034ea6cbaf2.png')
        await ctx.channel.send(embed=fee_info)

    @commands.group()
    @commands.check(is_one_of_gods)
    async def fee(self, ctx):
        """
        Command category/ entry for the system
        :param ctx:
        :return:
        """
        if ctx.invoked_subcommand is None:
            title = '__All available commands to manipulate system fees__'
            description = "Commands presented bellow allow for manipulation of fees and their review per each segment."
            list_of_values = [
                {"name": f"{self.command_string}fee change",
                 "value": f"Entry to sub category of commands to set fees for various parts of {self.bot.user} system"}
            ]

            await custom_messages.embed_builder(ctx=ctx, title=title, description=description, data=list_of_values,
                                                thumbnail=self.bot.user.avatar_url, destination=ctx.message.author)

    @fee.group()
    async def change(self, ctx):
        """
        Commands entry for sub categories to manipulate fees
        :param ctx:
        :return:
        """
        if ctx.invoked_subcommand is None:
            title = '__Change fee commands__'
            description = "Representation of all commands needed to be execute if you are willing to change the fee"
            list_of_values = [
                {"name": f"{self.command_string}fee change min_merchant_transfer <value in $ in format 0.00>",
                 "value": "Minimum amount in $ crypto value to be eligible for withdrawal from it"},
                {"name": f"{self.command_string}fee change merchant_license_fee <value in $ in format 0.00>",
                 "value": "Monthly License Fee for Merchant"},
                {"name": f"{self.command_string}fee change merchant_wallet_transfer_fee <value in $ in format 0.00>",
                 "value": "Fee when transferring from merchant wallet of the community"},
                {"name": f"{self.command_string}fee change xlm_withdrawal_fee <value in $ in format 0.00>",
                 "value": "Withdrawal fee from personal wallet to outside wallet on Stellar chain"},

            ]

            await custom_messages.embed_builder(ctx=ctx, title=title, description=description, data=list_of_values,
                                                thumbnail=self.bot.user.avatar_url, destination=ctx.message.author)

    @change.command()
    async def coin_fee(self, ctx, value: float, ticker: str):
        """
        Set the coin withdrawal fee
        """
        if ticker in self.list_of_coins:
            penny = (int(value * (10 ** 2)))
            rounded = round(penny / 100, 2)

            fee_data = {
                f"fee_list.{ticker}": rounded
            }
            if self.backoffice.bot_manager.manage_fees_and_limits(key='withdrawals', data_to_update=fee_data):
                message = f'You have successfully set Stellar Lumen withdrawal fee to be {rounded}$.'
                await custom_messages.system_message(ctx=ctx, color_code=0, message=message, destination=1,
                                                     sys_msg_title=CONST_FEE_INFO)
            else:
                message = f'There has been an error while trying to set Stellar Lumen withdrawal fee to {rounded}$.' \
                          f'Please try again later or contact system administrator!'
                await custom_messages.system_message(ctx=ctx, color_code=1, message=message, destination=0,
                                                     sys_msg_title=CONST_FEE_INFO)
        else:
            message = f'Coin {ticker} not listed yet'
            await custom_messages.system_message(ctx=ctx, color_code=1, message=message, destination=0,
                                                 sys_msg_title=CONST_FEE_INFO)

    @change.command()
    async def min_merchant_transfer(self, ctx, value: float):
        """
        Set minimum amount in merchant wallet for withdrawal from it
        :param ctx: Discord Context
        :param value:
        :return:
        """

        # Get value in in pennies
        penny = (int(value * (10 ** 2)))
        rounded = round(penny / 100, 2)
        merch_data = {
            f"fee": rounded
        }
        if self.backoffice.bot_manager.manage_fees_and_limits(key='merchant_min', data_to_update=merch_data):
            message = f'You have successfully set merchant minimum withdrawal to be {rounded}$ per currency used.'
            await custom_messages.system_message(ctx=ctx, color_code=0, message=message, destination=1,
                                                 sys_msg_title=CONST_MERCHANT_LICENSE_CHANGE)
        else:
            message = f'There has been an error while trying to set merchant minimum withdrawal amount to {rounded}$.' \
                      f'Please try again later or contact system administrator!'
            await custom_messages.system_message(ctx=ctx, color_code=1, message=message, destination=0,
                                                 sys_msg_title=CONST_MERCHANT_LICENSE_CHANGE)

    @change.command()
    async def merchant_wallet_transfer_fee(self, ctx, value: float):
        """
        Change fee for merchant wallet transfer in $
        :param ctx: Discord Context
        :param value:
        :return:

        1% = 0.01 == 10
        """

        # Store percentage as micro
        percent_micro = int(value * (10 ** 2))

        merch_data = {
            f"fee": percent_micro
        }
        if self.backoffice.bot_manager.manage_fees_and_limits(key='wallet_transfer', data_to_update=merch_data):
            message = f'You have successfully set merchant wallet transfer fee to be {percent_micro / (10 ** 2)}%.'
            title = '__Merchant wallet transfer fee information__'
            await custom_messages.system_message(ctx=ctx, color_code=0, message=message, destination=1,
                                                 sys_msg_title=title)
        else:
            message = f'There has been an error while trying to set merchant wallet transfer fee to {percent_micro / (10 ** 2)}%.' \
                      f'Please try again later or contact system administrator!'
            title = '__Merchant wallet transfer fee information__'
            await custom_messages.system_message(ctx=ctx, color_code=1, message=message, destination=0,
                                                 sys_msg_title=title)

    @cl.error
    async def cl_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await custom_messages.system_message(ctx=ctx, color_code=1, message=CONST_WARNING_TITLE, destination=1,
                                                 sys_msg_title=CONST_WARNING_MESSAGE)

    @system.error
    async def sys_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await custom_messages.system_message(ctx=ctx, color_code=1, message=CONST_WARNING_TITLE, destination=1,
                                                 sys_msg_title=CONST_WARNING_MESSAGE)

    # @cogs.error
    # async def mng_error(self, ctx, error):
    #     if isinstance(error, commands.CheckFailure):
    #         await custom_messages.system_message(ctx=ctx, color_code=1, message=CONST_WARNING_TITLE, destination=1,
    #                                              sys_msg_title=CONST_WARNING_MESSAGE)

    @hot.error
    async def h_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await custom_messages.system_message(ctx=ctx, color_code=1, message=CONST_WARNING_TITLE, destination=1,
                                                 sys_msg_title=CONST_WARNING_MESSAGE)


def setup(bot):
    bot.add_cog(BotManagementCommands(bot))
