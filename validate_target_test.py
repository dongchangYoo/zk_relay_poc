
def pack_max_variance(length: int):
    if length > 32:
        return 0
    return 2 ** (length * 4) - 1


def get_hex_length(bits: int):
    bit_length = bits.bit_length()
    return bit_length // 4 if bit_length % 4 == 0 else bit_length // 4 + 1


def bits_to_target(bits: int) -> int:
    # seperate exponent and coefficient
    exp = (bits & 0xff000000) >> 24
    coef = bits & 0x00ffffff
    # calculate and return target
    target = coef * 256 ** (exp - 3)
    return target


def pack_target(bits: int):
    exp = (bits & 0xff000000) >> 6
    coef = (bits & 0x00ffffff)
    return coef << (8 * exp + 152)


def to_big_endian(bits: int) -> int:
    return (bits & 0xff000000) >> 24 & (bits & 0x00ff0000) >> 8 & (bits & 0x0000ff00) << 8 & (bits & 0x000000ff) << 24


def validate_target(epoch_head: str, epoch_tail: str, next_epoch_head: str):
    time_head = int.from_bytes(bytes.fromhex(epoch_head[8:16])[::-1], byteorder="big")
    time_tail = int.from_bytes(bytes.fromhex(epoch_tail[8:16])[::-1], byteorder="big")

    epoch_head_bits = int.from_bytes(bytes.fromhex(epoch_head[16:24])[::-1], byteorder="big")
    next_epoch_head_bits = int.from_bytes(bytes.fromhex(next_epoch_head[16:24])[::-1], byteorder="big")

    time_delta = time_tail - time_head
    target_time_delta = 1209600  # 2016 * 600 (time interval of 10 minutes)

    current_target = pack_target(epoch_head_bits)
    current_target = bits_to_target(epoch_head_bits)
    target = current_target * time_delta  # target_time_delta

    encoded_target = pack_target(next_epoch_head_bits)
    encoded_target_extended = encoded_target * target_time_delta

    max_variance = pack_max_variance(get_hex_length(target) - get_hex_length(next_epoch_head_bits & 0xffffff))

    target = 95832923060582736897701037735936000 if target > 95832923060582736897701037735936000 else target
    delta = target - encoded_target_extended
    delta = delta if target >= encoded_target_extended else max_variance + 1
    valid = True if delta <= max_variance else False
    return valid, current_target


def target_floor(target: int):
    byte_len = len(bytes.fromhex(hex(target)[2:]))
    first_mask = 0xff * 256 ** (byte_len - 1)
    first_byte = (target & first_mask) / 256 ** (byte_len - 1)

    coef_len = 2 if first_byte > 0x7f else 3
    coef_mask = 0xffffff * 256 ** (byte_len - coef_len)

    return target & coef_mask


if __name__ == "__main__":
    # test_epoch_head = "4b1e5e4a29ab5f49ffff001d1dac2b7c"
    # test_epoch_tail = "57233e0e61bc6649ffff001d01e36299"
    # test_next_head = "22c90f9bb0bc6649ffff001d08d2bd61"

    # test_epoch_head = "4b1e5e4a29ab5f49ffff001d1dac2b7c"
    # test_epoch_tail = "13cd8ca26c087f49ffff001d30b73231"
    # test_next_head = "6b6d2c576b0e7f49ffff001d33f0192f"

    # test_epoch_head = "0a63cb5374caaf53d15f4118dd7834fb"
    # test_epoch_tail = "74c13ea150b2c153d15f4118738fb8f9"
    # test_next_head = "58629ce886bdc153e66b3f18c7e8c140"
    #
    # result_valid, result_current_target = validate_target(test_epoch_head, test_epoch_tail, test_next_head)
    # print(result_valid)
    # print(result_current_target)

    bits = 0x171398ce
    target1 = 1877009475827353279654828838027187714710153476809162752
    target2 = 0x98ce0000000000000000000000000000000000000000
    offset = 123123

    result = target_floor(target2 + offset)
    print(hex(result))

