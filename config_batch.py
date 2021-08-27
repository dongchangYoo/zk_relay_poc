import argparse
import os

import toml

static_config: dict = {
    'zokrates': {
        'BIN_PATH': 'ToBeSet',
        'STDLIB_PATH': 'ToBeSet'
    },
    'context': {
        'PROVING_SCHEME_NAME': 'ToBeSet',
        'ROOT_DIR': 'ToBeSet',
        'code': {
            'CODE_DIR': 'code/',
            'CODE_FILE_NAME': 'ToBeSet'
        },
        'data': {
            'DATA_DIR': 'ToBeSet',
            'PROGRAM_FILE_NAME': 'zok',
            'ABI_FILE_NAME': 'abi.json',
            'VKEY_FILE_NAME': 'verification.key',
            'PKEY_FILE_NAME': 'proving.key',
            'WITNESS_FILE_NAME': 'witness',
            'PROOF_FILE_NAME': 'proof.json'
        },
        'contract': {
            'CONTRACT_DIR': 'contract/',
            'CONTRACT_FILE_NAME': 'ToBeSet'
        }
    }
}

head_static_code = """
import "utils/pack/u32/pack256.zok" as pack256
import "utils/pack/u32/nonStrictUnpack256.zok" as unpack256
import "utils/pack/u32/pack128.zok" as pack128
import "utils/pack/u32/unpack128.zok" as unpack128

import "./libs/update_target.zok" as update_target
import "./libs/to_big_endian256.zok" as to_big_endian256
import "./libs/validate_block_header.zok" as validate_block_header


def main(field epoch_head_time_and_bits, field prev_hash, private u32[{intermediate_num}][32] intermediate_blocks, field[5] final_block) -> (field, field):
    u32[4] tmp = unpack128(epoch_head_time_and_bits)
    u32 little_head_time = tmp[1]
    u32 little_head_bits = tmp[2]

    u32[8] big_prev_hash = unpack256(prev_hash)
    u32[8] little_prev_hash = to_big_endian256(big_prev_hash)

    u32[32] little_final_block = [
        ...unpack128(final_block[0]),
        ...unpack128(final_block[1]),
        ...unpack128(final_block[2]),
        ...unpack128(final_block[3]),
        ...unpack128(final_block[4]),
        2147483648, ...[0; 10], 640
    ]

    u32 little_tail_time = intermediate_blocks[0][17]
    u32 little_next_bits = little_final_block[18]
    
    // validate intermediate headers
"""

intermediate_code_block = """    little_prev_hash = validate_block_header(little_head_bits, little_prev_hash, intermediate_blocks[{batch_loop}])
"""

tail_static_code = """
    // validate final block header
    u32[8] little_final_hash = validate_block_header(little_next_bits, little_prev_hash, little_final_block)

    // validate target
    field big_updated_target = update_target(little_head_time, little_head_bits, little_tail_time)

    field big_final_hash = pack256(to_big_endian256(little_final_hash))
    return big_final_hash, big_updated_target
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="batch num (integer)")
    parser.add_argument("--project_root", "-r", required=False, default=os.path.dirname(os.path.abspath(__file__)) + "/", type=str)
    parser.add_argument("--zokrates_bin_path", "-z", required=False, default="/Users/dc/research_project/ZoKrates/target/release/zokrates", type=str)
    parser.add_argument("--stdlib_path", "-s", required=False, default="/Users/dc/research_project/ZoKrates/zokrates_stdlib/stdlib", type=str)
    parser.add_argument("--proving_scheme", "-p", required=False, default="g16", type=str)
    parser.add_argument("--batch_num", "-b", required=True, type=int, nargs=1)

    # parse configuration arguments
    args = parser.parse_args()
    project_root = args.project_root
    zokrates_bin_path = args.zokrates_bin_path
    stdlib_path = args.stdlib_path
    proving_scheme = args.proving_scheme
    batch_num = args.batch_num[0]

    # set arguments to static_config dictionary
    config = static_config
    config["zokrates"]["BIN_PATH"] = zokrates_bin_path
    config["zokrates"]["STDLIB_PATH"] = stdlib_path
    config["context"]["PROVING_SCHEME_NAME"] = proving_scheme
    config["context"]["ROOT_DIR"] = project_root + "zk_relay/zok_src/"
    config["context"]["code"]["CODE_FILE_NAME"] = "validate_batch{}.zok".format(batch_num)
    config["context"]["data"]["DATA_DIR"] = "data/batch{}/".format(batch_num)
    config["context"]["contract"]["CONTRACT_FILE_NAME"] = "verifier{}.sol".format(batch_num)

    # export configuration toml file
    with open(project_root + "/zk_relay/conf/config_batch{}.toml".format(batch_num), "w") as f:
        config_toml = toml.dumps(config)
        f.write(config_toml)

    head_code = head_static_code.format(intermediate_num=(batch_num-1))
    body_code = "".join([intermediate_code_block.format(batch_loop=i) for i in range(batch_num - 1)])
    code = head_code + body_code + tail_static_code

    code_path = config["context"]["ROOT_DIR"] + config["context"]["code"]["CODE_DIR"] + config["context"]["code"]["CODE_FILE_NAME"]
    with open(code_path, "w") as f:
        f.write(code)
    print("[Success] Configuration for batch {} completes.".format(batch_num))
