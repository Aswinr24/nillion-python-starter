from nada_dsl import *

def nada_main():

    bidder0 = Party(name="Bidder0")
    bidder1 = Party(name="Bidder1")
    bidder2 = Party(name="Bidder2")
    outparty = Party(name="OutParty")

    bid0 = SecretUnsignedInteger(Input(name="bid0", party=bidder0))
    bid1 = SecretUnsignedInteger(Input(name="bid1", party=bidder1))
    bid2 = SecretUnsignedInteger(Input(name="bid2", party=bidder2))

    def max(a: SecretUnsignedInteger, b: SecretUnsignedInteger) -> SecretUnsignedInteger:
        return (a < b).if_else(b, a)

    # Find the maximum bid between bid0 and bid1
    max_bid0_1 = max(bid0, bid1)
    # Find the maximum bid between max_bid0_1 and bid2
    max_bid = max(max_bid0_1, bid2)

    # Output the highest bid
    highest_bid_output = Output(max_bid, "highest_bid", outparty)
    
    # Output the bid amounts of each bid
    bid0_output = Output(bid0, "bid0_amount", outparty)
    bid1_output = Output(bid1, "bid1_amount", outparty)
    bid2_output = Output(bid2, "bid2_amount", outparty)

    return [highest_bid_output, bid0_output, bid1_output, bid2_output]
