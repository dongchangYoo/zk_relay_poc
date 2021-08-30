pragma solidity ^0.8.0;

import "./verifier3.sol";

contract Bitcoin is Verifier {

    struct Branch{
        // 자기 자신의 길이가 6이 넘어가면 부모 Branch를 실행한다.
        uint256 parentBranchIndex;
        uint256 branchStartHeight;

        mapping(uint256 => uint256) heightToBlockHash;
        mapping(uint256 => uint256) blockHashToHeight;
        mapping(uint256 => BlockData) heightToBlock;
        uint256 headTimeAndBits;

        // execute_tx는 confirmedHeight 부터 latestHeight까지 block을 돌면서 tx를 실행한다.
        uint256 confirmedHeight;  // 제출 height - 6
        uint256 latestHeight; // 마지막 제출 height로 갱신
    }

    struct BlockData {
        Transaction[] txs;
    }

    struct Transaction {
        uint256 amount;
        address recipient;
    }

    mapping(uint256 => Branch) branches;  // branch index => Branch
    uint256 numBranch = 0;

    uint256 constant BATCH_NUM = 3;

    // timeBits 값은 startHeight 가 2019인 경우, 2016의 timeBits값을 입력한다.
    // startHeight가 2019인 경우, 2016의 timeBits값을 입력한다.
    // 0x9dfdd, "0x00000000000000000000d14f8ae6e38cc42ecd2f79d1b55f860340d394e5d238", "0x0000000000000000000000000000000021738a2d8b7b435fea071017acc0cd5c"
    constructor(uint256 startHeight, uint256 startHash, uint256 timeBits) {
        Branch storage mainBranch = branches[++numBranch];
        mainBranch.parentBranchIndex = 0;
        mainBranch.branchStartHeight = startHeight;
        mainBranch.heightToBlockHash[startHeight] = startHash;
        mainBranch.blockHashToHeight[startHash] = startHeight;
        mainBranch.headTimeAndBits = timeBits;
        mainBranch.confirmedHeight = startHeight;
        mainBranch.latestHeight = startHeight;
    }


    /*
    description of inputs
    [0]: 16 bytes word including start header's time and bits
    [1]: start header's previous hash (32 bytes)
    [2:7]: 5 word of final header (16 bytes * 5)
    [7]: final header's hash (32 bytes)
    [8]: next target (32 bytes)
    */
    // 1, [["0x20e461558cade67612b58b85f970f5dcc3ca59129c3722aee7aa7a3dec55d28b", "0x0df8d53786370c06b43a981c98cf48980fc73b446efa658ba5d54ceb837367fd"], [["0x26b8723e0fa6745cab66c8040d3139f2850b626f6a29d6f156e7a442c1d2bacc", "0x196bb392b0ce1bb9070e7f71cff75e3b620d1b4efe41453c9a56c530a8e2e477"], ["0x2a9a10ab9d284883512a627ed4c1fbd6db28a6a819a516eb36990ee2137b091f", "0x036a5cb4946a430b1ad78cb9dc5275476381f0672fb429712b54a9a49955ecec"]], ["0x21137396d8067475d59aae309e0c441fa81e0512a7ac5ca98b84cd978ca6326b", "0x1d0833b630dd8b6b32f7cef20825dfee06ce70c65bc31a6c19d9ff6a3c1471c2"]], ["0x0000000000000000000000000000000021738a2d8b7b435fea071017acc0cd5c", "0x00000000000000000000d14f8ae6e38cc42ecd2f79d1b55f860340d394e5d238", "0x000000000000000000003355843ef2eefc24ef9a55a9ac5162f5a968552003c2", "0x000000000000000000000000000000000c5e2b76282c565f123a101749e4a793", "0x000000000000000000103a12b0eca8641fdb97530eca8641fdb97530eca8641f"]
    function relay3(uint256 branchIndex, Proof memory proof, uint[5] memory input) external returns (bool) {
        // check zk_proof
        bool result = verifyTx(proof, input);
        require(result == true, "Proof validation fails");

        // check connectivity between branch and submitted headers
        Branch storage branch = branches[branchIndex];
        uint256 predecessor_height = branch.blockHashToHeight[input[1]];
        require(predecessor_height != 0, "There is no predecessor.");

        // check wheather headTimeAndBits stored in the bitcoin contract equals to starting header's timeAndBits.
        require(branch.headTimeAndBits == input[0]);


        uint256 local_height = branch.latestHeight;
        bool difficulty_updating = is_updating_submit(local_height);

        if (difficulty_updating) {
            //check target
            uint256 expected_bits = targetToLittleBits(input[4]);  // little bits
            uint256 actual_bits = (input[3] & 0xffffffff00000000) >> 32;
            require(expected_bits == actual_bits, "Invalid updated bits");

            // update headTimeAndBits
            branch.headTimeAndBits = input[3];  // next timeAndBits
        }

        // execute txs
        branch.confirmedHeight = local_height + BATCH_NUM - 6;
        branch.latestHeight = local_height + BATCH_NUM;
        // store new header

        branch.heightToBlockHash[predecessor_height + BATCH_NUM] = input[2];
        branch.blockHashToHeight[input[2]] = predecessor_height + BATCH_NUM;

        return true;
    }

    function is_updating_submit(uint256 local_height) pure internal returns (bool) {
        uint256 updatingHeight = local_height % 2016 != 0 ? (local_height) / 2016 * 2016 + 2016 : local_height;
        require(updatingHeight > local_height, "last header height must be less than or equal to updatingHeight");
        return (local_height + BATCH_NUM) % 2016 == 0;
    }

    function targetToLittleBits(uint256 target) internal pure returns (uint32) {
        uint256 i;
        uint256 firstByte = 0xFF00000000000000000000000000000000000000000000000000000000000000;

        // find first index
        while(true) {
            if( ( (target << i) & firstByte ) != 0 ) {

                if((target << i) & firstByte > 0x7F00000000000000000000000000000000000000000000000000000000000000) {
                    // exception case.
                    if(i!=0) i-=8;
                }
                break;
            }
            i+=8;
        }

        uint32 little_bits = uint32( ( (256-i) << 21) | (target >> (232-i)) & 0xFFFFFF );

        uint32[4] memory tmp;
        tmp[0] = (little_bits & 0xff000000) >> 24;
        tmp[1] = (little_bits & 0x00ff0000) >> 8;
        tmp[2] = (little_bits & 0x0000ff00) << 8;
        tmp[3] = (little_bits & 0x000000ff) << 24;

        return tmp[0] | tmp[1] | tmp[2] | tmp[3];
    }

    function get_branch_info(uint256 branchIndex) view external returns (uint256, uint256, uint256, uint256) {
        Branch storage branch = branches[branchIndex];
        return (branch.latestHeight, branch.headTimeAndBits, branch.confirmedHeight, branch.latestHeight);
    }
}
