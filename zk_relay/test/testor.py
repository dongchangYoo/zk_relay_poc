from bitcoinpy.client import BitcoinClient
import os
import toml
import json


def generate_test_data(num_headers: int, end_height: int):
    config = toml.load("../rpc_config.toml")
    cli = BitcoinClient(config["url"], config["id"], config["pwd"], config["wallet_name"])

    start_height = end_height - num_headers + 1
    os.makedirs("./test_data", exist_ok=True)
    for i in range(num_headers):
        header_str = cli.get_block_header_by_height(start_height + i)
        with open("./test_data/mainnet_{}.json".format(start_height + i), "w") as f:
            contents = {
                "hex": header_str
            }
            f.write(json.dumps(contents))


def get_header_by_height(height: int):
    with open("./test_data/mainnet_{}.json".format(height), "r") as json_data:
        return json.load(json_data)["hex"]


if __name__ == "__main__":
    # num_headers = 100
    # end_height = 647136
    # generate_test_data(num_headers, end_height)
    result = get_header_by_height(647135)
    print(result)