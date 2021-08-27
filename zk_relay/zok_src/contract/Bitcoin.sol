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

    function relay3(uint256 branchIndex, Proof memory proof, uint[9] memory input) view external returns (bool) {
        // check zk_proof
        bool result = verifyTx(proof, input);
        require(result == true, "Proof validation fails")

        // check connectivity between branch and submitted headers
        Branch storage branch = branches[branchIndex];
        uint256 predecessor_height = branch.blockHashToHeight[input[1]];
        require(predecessor_height != 0, "There is no predecessor.");

        // execute txs

        // store new header
        branch.heightToBlockHash[predecessor_height + 3] = input[7];
        branch.blockHashToHeight[input[7]] = predecessor_height + 3;

        return true;
    }

    function get_latestHeight(uint256 branchIndex) view external returns (uint256) {
        return branches[branchIndex].latestHeight;
    }
}
