import asyncio
import py_nillion_client as nillion
import os

from py_nillion_client import NodeKey, UserKey
from dotenv import load_dotenv
from nillion_python_helpers import get_quote_and_pay, create_nillion_client, create_payments_config

from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.keypairs import PrivateKey

home = os.getenv("HOME")
load_dotenv(f"{home}/.config/nillion/nillion-devnet.env")

async def main():
    # 1. Initial setup
    cluster_id = os.getenv("NILLION_CLUSTER_ID")
    grpc_endpoint = os.getenv("NILLION_NILCHAIN_GRPC")
    chain_id = os.getenv("NILLION_NILCHAIN_CHAIN_ID")
    seed = "my_seed"
    userkey = UserKey.from_seed(seed)
    nodekey = NodeKey.from_seed(seed)

    # 2. Initialize NillionClient against nillion-devnet
    client = create_nillion_client(userkey, nodekey)

    party_id = client.party_id
    user_id = client.user_id

    # 3. Pay for and store the program
    program_name = "main"
    program_mir_path = f"../nada_quickstart_programs/target/{program_name}.nada.bin"

    payments_config = create_payments_config(chain_id, grpc_endpoint)
    payments_client = LedgerClient(payments_config)
    payments_wallet = LocalWallet(
        PrivateKey(bytes.fromhex(os.getenv("NILLION_NILCHAIN_PRIVATE_KEY_0"))),
        prefix="nillion",
    )

    receipt_store_program = await get_quote_and_pay(
        client,
        nillion.Operation.store_program(program_mir_path),
        payments_wallet,
        payments_client,
        cluster_id,
    )

    action_id = await client.store_program(
        cluster_id, program_name, program_mir_path, receipt_store_program
    )

    program_id = f"{user_id}/{program_name}"
    print("Stored program. action_id:", action_id)
    print("Stored program_id:", program_id)

    # 4. Create secrets for the bids, add permissions, pay for and store them in the network
    bid_secrets = nillion.NadaValues(
        {
            "bid0": nillion.SecretUnsignedInteger(100),
            "bid1": nillion.SecretUnsignedInteger(200),
            "bid2": nillion.SecretUnsignedInteger(150),
        }
    )

    party_names = ["Bidder0", "Bidder1", "Bidder2"]
    party_ids = {name: client.party_id for name in party_names}

    permissions = nillion.Permissions.default_for_user(client.user_id)
    permissions.add_compute_permissions({client.user_id: {program_id}})

    receipt_store = await get_quote_and_pay(
        client,
        nillion.Operation.store_values(bid_secrets, ttl_days=5),
        payments_wallet,
        payments_client,
        cluster_id,
    )
    store_ids = await client.store_values(
        cluster_id, bid_secrets, permissions, receipt_store
    )

    print(f"store_ids type: {type(store_ids)}")
    print(f"store_ids content: {store_ids}")

    if isinstance(store_ids, str):
        store_ids_list = [store_ids]
    elif isinstance(store_ids, dict):
        store_ids_list = list(store_ids.values())
    elif isinstance(store_ids, list):
        store_ids_list = store_ids
    else:
        raise ValueError("store_ids should be a string, dictionary, or list.")

    print(f"Use secret store_ids: {store_ids_list}")

    # 5. Create compute bindings to set input and output parties, and pay for & run the computation
    compute_bindings = nillion.ProgramBindings(program_id)

    for party_name in party_names:
        compute_bindings.add_input_party(party_name, party_ids[party_name])

    # Do not include output parties if not required
    compute_bindings.add_output_party("OutParty", party_id) # Uncomment if needed

    computation_time_secrets = nillion.NadaValues({})

    receipt_compute = await get_quote_and_pay(
        client,
        nillion.Operation.compute(program_id, computation_time_secrets),
        payments_wallet,
        payments_client,
        cluster_id,
    )

    print(f"compute request details:")
    print(f"  program_id: {program_id}")
    print(f"  store_ids: {store_ids_list}")
    print(f"  computation_time_secrets: {computation_time_secrets}")

    compute_id = await client.compute(
        cluster_id,
        compute_bindings,
        store_ids_list,
        computation_time_secrets,
        receipt_compute,
    )

    # 6. Return the computation result
    print(f"The computation was sent to the network. compute_id: {compute_id}")
    while True:
        compute_event = await client.next_compute_event()
        if isinstance(compute_event, nillion.ComputeFinishedEvent):
            print(f"✅  Compute complete for compute_id {compute_event.uuid}")
            print(f"🖥️  The result is {compute_event.result.value}")
            return compute_event.result.value

if __name__ == "__main__":
    asyncio.run(main())
