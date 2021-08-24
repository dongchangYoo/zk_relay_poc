import toml
from bitcoinpy.client import BitcoinClient

from zk_relay.actor import Actor

if __name__ == "__main__":
    # initiate Actor
    config = toml.load("./rpc_config.toml")
    btc_cli = BitcoinClient(config["url"], config["id"], config["pwd"], config["wallet_name"])
    zok_config_path = "conf/config_batch2.toml"
    actor = Actor(btc_cli, zok_config_path)

    # setup and export verifier
    actor.setup_and_export_verifier()

    # generate proof
    actor.build_input_and_prove(647135, 647136)

    # flattening proof
    flat_proof = actor.flatten_proof()
    print(flat_proof)
