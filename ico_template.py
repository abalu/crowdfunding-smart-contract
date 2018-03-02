"""
NEX ICO Template
===================================

Author: Thomas Saunders
Email: tom@neonexchange.org

Date: Dec 11 2017

"""

from boa.blockchain.vm.Neo.Runtime import GetTrigger, CheckWitness, Notify
from boa.blockchain.vm.Neo.TriggerType import Application, Verification
from nex.common.storage import StorageAPI
from nex.common.txio import Attachments,get_asset_attachments
from nex.token.mytoken import Token
from nex.token.nep5 import NEP5Handler
from nex.token.crowdsale import Crowdsale
from nex.token.crowdfunding import crowdfunding_create, crowdfunding_get_members
from nex.token.reward import reward_users, reward_user, calculate_reward, level_up, level_of


def Main(operation, args):
    """

    :param operation: str The name of the operation to perform
    :param args: list A list of arguments along with the operation
    :return:
        bytearray: The result of the operation
    """

    trigger = GetTrigger()
    token = Token()

    #print("Executing ICO Template")

    # This is used in the Verification portion of the contract
    # To determine whether a transfer of system assets ( NEO/Gas) involving
    # This contract's address can proceed
    if trigger == Verification:

        # check if the invoker is the owner of this contract
        is_owner = CheckWitness(token.owner)

        # If owner, proceed
        if is_owner:

            return True

        # Otherwise, we need to lookup the assets and determine
        # If attachments of assets is ok
        attachments = get_asset_attachments()  # type:Attachments

        storage = StorageAPI()

        crowdsale = Crowdsale()

        return crowdsale.can_exchange(token, attachments, storage, True)


    elif trigger == Application:

        if operation != None:

            nep = NEP5Handler()

            for op in nep.get_methods():
                if operation == op:
                    return nep.handle_nep51(operation, args, token)

            if operation == 'deploy':
                return deploy(token)

            if operation == 'circulation':
                storage = StorageAPI()
                return token.get_circulation(storage)

            # the following are handled by crowdsale

            sale = Crowdsale()

            if operation == 'mintTokens':
                return sale.exchange(token)

            # if operation == 'crowdsale_register':
            #     return sale.kyc_register(args, token)

            # if operation == 'crowdsale_status':
            #     return sale.kyc_status(args)

            if operation == 'crowdsale_available':
                return token.crowdsale_available_amount()

            if operation == 'crowdfunding_create':
                return crowdfunding_create(args)

            if operation == 'crowdfunding_total':
                storage = StorageAPI()
                crowdfunding_address = args[0]
                crowdfunding_total_key = storage.get_crowdfunding_total_key(crowdfunding_address)
                crowdfunding_total = storage.get(crowdfunding_total_key)
                msg = ["crowdfunding_total", crowdfunding_total]
                Notify(msg)
                return crowdfunding_total

            if operation == 'crowdfunding_test':
                crowdfunding_address = args[0]
                member_addresses = crowdfunding_get_members(crowdfunding_address)
                if not member_addresses:
                    return False

                Notify("Member addresses:")
                Notify(member_addresses)
                return True

            if operation == 'level':
                address = args[0]
                
                level = level_of(address)

                Notify("Level:")
                Notify(level)
                
                return level

            if operation == 'reward_user':
                address = args[0]
                
                success = reward_user(address)
                
                if success:
                    Notify("User was rewarded:")
                    Notify(address)
                    
                return success

            if operation == 'reward_users':
                addresses = args[0]
                reward = args[1]
                
                success = reward_users(addresses, reward)
                
                if success:
                    Notify("Users were rewarded:")
                    for address in addresses:
                        Notify(address)
                    
                return success

            return 'unknown operation'

    return False


def deploy(token: Token):
    """

    :param token: Token The token to deploy
    :return:
        bool: Whether the operation was successful
    """
    if not CheckWitness(token.owner):
        print("Must be owner to deploy")
        return False

    storage = StorageAPI()

    if not storage.get('initialized'):

        # do deploy logic
        storage.put('initialized', 1)
        storage.put(token.owner, token.initial_amount)
        token.add_to_circulation(token.initial_amount, storage)

        return True

    return False

