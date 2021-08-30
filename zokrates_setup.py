import argparse
import os

import toml
from bitcoinpy.client import BitcoinClient
from zk_relay.actor import Actor


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="batch num (integer)")
    parser.add_argument("--rpc_config", "-r", required=False, default="./rpc_config.toml", type=str)
    parser.add_argument("--batch_num", "-b", required=True, type=int, nargs=1)

    # parse configuration arguments
    args = parser.parse_args()
    rpc_config_path = args.rpc_config
    batch_num = args.batch_num[0]

    # check whether rpc configuration file exists
    rpc_config = None
    try:
        rpc_config = toml.load(rpc_config_path)
    except FileNotFoundError:
        print("[Error] There is no rpc config file.")
        exit()
    except toml.decoder.TomlDecodeError:
        print("[Error] Invalid rpc config file.")
        exit()

    zok_config_path = "./zk_relay/conf/config_batch{}.toml".format(3)
    if not os.path.exists(zok_config_path):
        print("[Error] The setup for batch {} was not executed".format(batch_num))
        exit()

    btc_cli = BitcoinClient(rpc_config["url"], rpc_config["id"], rpc_config["pwd"], rpc_config["wallet_name"])
    actor = Actor(btc_cli, zok_config_path)

    # setup and export verifier
    actor.setup_and_export_verifier()

