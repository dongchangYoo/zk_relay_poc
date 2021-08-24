import argparse
import os

import toml

static_config = {
    'zokrates': {
        'BIN_PATH': '/Users/dc/research_project/ZoKrates/target/release/zokrates',
        'STDLIB_PATH': '/Users/dc/research_project/ZoKrates/zokrates_stdlib/stdlib'
    },
    'context': {
        'PROVING_SCHEME_NAME': 'g16',
        'ROOT_DIR': '/Users/dc/research_project/zk_relay_poc/zk_relay/zok_src/',
        'code': {
            'CODE_DIR': 'code/',
            'CODE_FILE_NAME': 'validate_batch2.zok'
        },
        'data': {
            'DATA_DIR': 'data/batch2/',
            'PROGRAM_FILE_NAME': 'zok',
            'ABI_FILE_NAME': 'abi.json',
            'VKEY_FILE_NAME': 'verification.key',
            'PKEY_FILE_NAME': 'proving.key',
            'WITNESS_FILE_NAME': 'witness',
            'PROOF_FILE_NAME': 'proof.json'
        },
        'contract': {
            'CONTRACT_DIR': 'contract/',
            'CONTRACT_FILE_NAME': 'verifier2.sol'
        }
    }
}


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
    config["context"]["data"]["DATA_DIR"] = "data/batch{}".format(batch_num)
    config["context"]["contract"]["CONTRACT_FILE_NAME"] = "verifier{}.sol".format(batch_num)

    # export configuration toml file
    with open(project_root + "/zk_relay/conf/config_batch{}.toml".format(batch_num), "w") as f:
        config_toml = toml.dumps(config)
        f.write(config_toml)

