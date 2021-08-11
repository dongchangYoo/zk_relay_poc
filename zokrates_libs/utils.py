from hashlib import sha256
from typing import Union


def double_hash_as_little(pre: Union[str, bytes]) -> str:
    if isinstance(pre, str):
        pre = bytes.fromhex(pre)
    elif not isinstance(pre, bytes):
        raise Exception("pre-image should has bytes or str types")
    return sha256(sha256(pre).digest()).digest().hex()


def double_hash_as_big(pre: str) -> str:
    hash_little = double_hash_as_little(pre)
    return bytes.fromhex(hash_little)[::-1].hex()


def hex_to_word_array(target: str) -> list:
    if target.startswith("0x"):
        target = target[2:]
    ret = list()
    for i in range(len(target) // 8):
        parsed_int = int(target[i * 8:i*8+8], 16)
        ret.append(parsed_int)
    return ret


def encode_zokrates_input(*arg) -> list:
    encoded_inputs = list()
    for item in arg:
        encoded_inputs += hex_to_word_array(item)
    return encoded_inputs


def int_array_to_hex(targets: list) -> str:
    return "".join([hex(item)[2:].zfill(8) for item in targets])


def padding(value: str):
    bit_len = len(value) * 4
    # determine number of blocks
    num_blocks = bit_len // 512 + 2 if bit_len % 512 > 448 else bit_len // 512 + 1

    # set length suffix
    bit_len_hex = hex(bit_len)[2:]
    bit_len_hex = "0" + bit_len_hex if len(bit_len_hex) % 2 == 1 else bit_len_hex

    # determine number of zero-bytes
    zeros = (num_blocks * 512 - bit_len - 8 - len(bit_len_hex) * 4) // 8

    return value[:] + "80" + "00" * zeros + bit_len_hex


if __name__ == "__main__":
    test1 = "a76dd73790def7b57776f22fa211d19cf43121a709a37eaeda17230eaac258f5"
    test2 = "0100000000000000000000000000000000000000000000000000000000000000000000003ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a29ab5f49ffff001d1dac2b7c"
    print(padding(test1))




