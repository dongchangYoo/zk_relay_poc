from bitcoinpy.base.header import Header
from bitcoinpy.client import BitcoinClient
import os
import json


class BTCMock(BitcoinClient):
    def __init__(self, url: str, id: str, pwd: str, wallet_name: str):
        super().__init__(url, id, pwd, wallet_name)
        self.DIRECTORY_DATABASE_PATH = "data"

    def query_and_store_batch_headers(self, start_height: int, end_height: int):
        """ query and store block which have heights from """
        print("start_height: {}, end_height: {}, num_blocks: {}".format(start_height, end_height, end_height - start_height + 1))
        os.makedirs(self.DIRECTORY_DATABASE_PATH, exist_ok=True)
        for i in range(end_height - start_height + 1):
            self.get_header_by_height(start_height + i)

    def get_header_by_height(self, height: int) -> Header:
        os.makedirs(self.DIRECTORY_DATABASE_PATH, exist_ok=True)
        block_path = self.DIRECTORY_DATABASE_PATH + "/mainnet_{}.json".format(height)
        if not os.path.exists(block_path):
            header_str = self.get_block_header_by_height(height)
            with open(block_path, "w") as f:
                contents = {"hex": header_str}
                f.write(json.dumps(contents))

        if os.path.exists(block_path):
            with open(block_path, "r") as json_data:
                header_str = json.load(json_data)["hex"]
        header_obj = Header.from_raw_str(header_str)
        header_obj.height = height
        return header_obj


# TODO testcase
if __name__ == "__main__":
    btc = BTCMock("http://btc.chain.thebifrost.io:8332", "pilab", "HUcb?2VXABmTgJsHBs9n", "btcUser")

    start_height = 647037
    end_height = 647136
    num_blocks = end_height - start_height + 1
    btc.query_and_store_batch_headers(start_height, end_height)

    header = btc.get_header_by_height(647139)
    print(header)