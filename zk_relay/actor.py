import json

from bitcoinpy.base.header import Header
from bitcoinpy.client import BitcoinClient
from zk_relay.utils import padding, split_hex_to_int_array
from zokrates_libs.zokrates import Zokrates

from unittest import TestCase
import toml


class Actor:
    def __init__(self, btc_cli: BitcoinClient, zok_config_path: str):
        self.btc_cli = btc_cli
        self.zok_cli = Zokrates(zok_config_path)

    def build_input(self, start_height: int, end_height) -> (Header, list):
        epoch_head: Header = Header.from_raw_str(self.btc_cli.get_block_header_by_height(start_height // 2016 * 2016))
        epoch_head_time_and_bits: str = epoch_head.get_word_of_single_word(4).hex()

        headers: list = self._get_header_batch(start_height, end_height)

        blocks: str = ""
        for i in range(len(headers)):
            blocks += padding(headers[i].raw_header_str())

        encoded_input = list()
        encoded_input.append(int(epoch_head_time_and_bits, 16))
        encoded_input += split_hex_to_int_array(blocks, 4)
        return encoded_input

    def setup_and_export_verifier(self):
        print(">>> setup...")
        self.zok_cli.integrated_setup()
        print(">>> exporting verifier")
        self.zok_cli.export_verifier()

    def build_input_and_prove(self, from_height: int, end_height: int):
        print(">>> build input to be entered to zokrates program")
        encoded_input = self.build_input(from_height, end_height)
        print(">>> generate proof")
        self.zok_cli.prove(encoded_input)

    def flatten_proof(self) -> str:
        with open(self.zok_cli.proof_path, "r") as json_data:
            proof_json = json.load(json_data)
        proof = list()
        proof.append(proof_json["proof"]["a"])
        proof.append(proof_json["proof"]["b"])
        proof.append(proof_json["proof"]["c"])
        contract_input = [proof, proof_json["inputs"]]
        return json.dumps(contract_input)[1:-1]

    def _get_header_batch(self, from_height: int, to_height: int):
        headers = list()
        while from_height <= to_height:
            raw_header = self.btc_cli.get_block_header_by_height(from_height)  # TODO change btc_cli to btc_mock?
            header = Header.from_raw_str(raw_header)
            headers.append(header)
            from_height += 1
        return headers


class ActorTest(TestCase):
    def setUp(self):
        # initiate Bitcoin client
        config = toml.load("./rpc_config.toml")
        btc_cli = BitcoinClient(config["url"], config["id"], config["pwd"], config["wallet_name"])
        zok_config_path = "conf/config_base.toml"
        # init actor
        self.actor = Actor(btc_cli, zok_config_path)

    def test_batch2(self):
        # setup zokrates program
        self.actor.zok_cli.integrated_setup()

        # generate input of zokrates program
        encoded_input = self.actor.build_input(647135, 647136)
        self.actor.zok_cli.prove(encoded_input)

    def test_batch7(self):
        # setup zokrates program
        self.actor.zok_cli.integrated_setup()

        # generate input of zokrates program
        encoded_input = self.actor.build_input(647130, 647136)
        self.actor.zok_cli.prove(encoded_input)
