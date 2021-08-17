from unittest import TestCase

from bitcoinpy.base.header import Header
from bitcoinpy.client import BitcoinClient
from zk_relay.utils import padding, split_hex_to_int_array
from zokrates_libs.zokrates import Zokrates

import toml


class Actor:
    def __init__(self, btc_cli: BitcoinClient, zok_cli: Zokrates):
        self.btc_cli = btc_cli

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

        prev_hash: str = headers[0].prev_hash  # big
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
        self.cli = BitcoinClient(config["url"], config["id"], config["pwd"], config["wallet_name"])

    def test_batch2(self):
        # init actor
        actor = Actor(self.cli, 647135, 647136, 2)

        # generate input of zokrates program
        epoch_head, headers = actor.construct_batch()
        encoded_input = actor.generate_inputs(epoch_head, headers)

        expected = [44464440580593778464358404730717785436, 1413115512144597745417862046068109726134405896890164913, 32, 2972095471, 1566443217, 2834926071, 3014987434, 530490078, 3972009472, 0, 0, 72365708, 1602530947, 3971540981, 2425790749, 3629925988, 3735197967, 1124265418, 3784669897, 1261065823, 3926331415, 878507539, 2147483648, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 640, 1300611580146666036859639858579970, 16692286963318328199362419706042515456, 75004259440575824002881041129, 48489775222424419754234584628752695656, 16439693359090398983136057306418292627]
        for i, item in enumerate(encoded_input):
            self.assertEqual(item, expected[i])

    def test_batch7(self):
        # init actor
        actor = Actor(self.cli, 647135, 647136, 2)

        # generate input of zokrates program
        epoch_head, headers = actor.construct_batch()
        encoded_input = actor.generate_inputs(epoch_head, headers)

        expected = [44464440580593778464358404730717785436, 1413115512144597745417862046068109726134405896890164913, 32, 2972095471, 1566443217, 2834926071, 3014987434, 530490078, 3972009472, 0, 0, 72365708, 1602530947, 3971540981, 2425790749, 3629925988, 3735197967, 1124265418, 3784669897, 1261065823, 3926331415, 878507539, 2147483648, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 640, 1300611580146666036859639858579970, 16692286963318328199362419706042515456, 75004259440575824002881041129, 48489775222424419754234584628752695656, 16439693359090398983136057306418292627]
        for i, item in enumerate(encoded_input):
            self.assertEqual(item, expected[i])