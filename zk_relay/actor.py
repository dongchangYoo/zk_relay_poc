from unittest import TestCase

from bitcoinpy.base.header import Header
from bitcoinpy.client import BitcoinClient
from zk_relay.utils import padding, split_hex_to_int_array
from zokrates_libs.zokrates import Zokrates

import toml


class Actor:
    def __init__(self, btc_cli: BitcoinClient, zok_config_path: str):
        self.btc_cli = btc_cli
        self.zok_cli = Zokrates(zok_config_path)

    def get_header_batch(self, from_height: int, to_height: int):
        headers = list()
        while from_height <= to_height:
            raw_header = self.btc_cli.get_block_header_by_height(from_height)
            header = Header.from_raw_str(raw_header)
            headers.append(header)
            from_height += 1
        return headers

    def construct_batch(self, start_height: int, end_height) -> (Header, list):
        epoch_head: Header = Header.from_raw_str(self.btc_cli.get_block_header_by_height(start_height // 2016 * 2016))
        headers: list = self.get_header_batch(start_height, end_height)
        epoch_head_time_and_bits: str = epoch_head.get_word_of_single_word(4).hex()

        prev_hash: str = headers[0].prev_hash.hex_as_be  # big
        intermediate_blocks: str = ""
        for i in range(0, len(headers) - 1):
            intermediate_blocks += padding(headers[i].raw_header_str())
        final_block: str = headers[-1].raw_header_str()

        encoded_input = list()
        encoded_input.append(int(epoch_head_time_and_bits, 16))
        encoded_input.append(int(prev_hash, 16))
        encoded_input += split_hex_to_int_array(intermediate_blocks, 4)
        encoded_input += split_hex_to_int_array(final_block, 16)
        return encoded_input


class ActorTest(TestCase):
    def setUp(self):
        # initiate Bitcoin client
        config = toml.load("./rpc_config.toml")
        self.btc_cli = BitcoinClient(config["url"], config["id"], config["pwd"], config["wallet_name"])
        self.zok_config_path = "../conf/config.toml"

    def test_batch2(self):
        # init actor
        actor = Actor(self.btc_cli, self.zok_config_path)

        # setup zokrates program
        actor.zok_cli.integrated_setup()

        # generate input of zokrates program
        encoded_input = actor.construct_batch(647135, 647136)
        actor.zok_cli.prove(encoded_input)

    def test_batch7(self):
        # init actor
        actor = Actor(self.btc_cli, self.zok_config_path)

        # setup zokrates program
        actor.zok_cli.integrated_setup()

        # generate input of zokrates program
        encoded_input = actor.construct_batch(647130, 647136)
        actor.zok_cli.prove(encoded_input)

        # generate input of zokrates program
        encoded_input = actor.construct_batch(647130, 647136)
