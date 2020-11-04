//SPDX-License-Identifier: MIT
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "@openzeppelin/contracts/utils/Counters.sol";

interface ICifEsportsMultiTrophy {
    function trophies(uint256 trophyId) external view returns (
        string calldata tournament,
        bytes32 infoHash,
        uint256 timeReceived,
        uint256[] calldata winnerIds
    );
    function transferOwnership(address newOwner) external;
    function hasAddressCurrentTrophy(address holder) external view returns (bool);
    function currentTrophyId() external view returns (uint256 trophyId);
    function setBaseURI(string memory baseURI) external;
    function passTrophy(
        string memory _tournament,
        bytes32 _infoHash,
        address[] memory _winnerAddresses,
        string[] memory _winnerNames
    ) external;
}

/// @title Governance Contract for the CIF Esports Trophy
/// @author Matthias Nadler, University of Basel
/// @notice Implements flexible quorum voting for governance members
contract CifGovernance {
    using Counters for Counters.Counter;

    event Confirmation(address indexed sender, uint256 indexed transactionId);
    event Revocation(address indexed sender, uint256 indexed transactionId);
    event Submission(uint256 indexed transactionId);
    event Execution(uint256 indexed transactionId);
    event ExecutionFailure(uint256 indexed transactionId);
    event MemberAddition(address indexed member);
    event MemberRemoval(address indexed member);
    event QuorumChange(uint256 indexed oldQuorum, uint256 indexed newQuorum);

    address immutable public cifTrophyAddress;
    ICifEsportsMultiTrophy private _cifTrophy;

    mapping(address => bool) public isMember;
    address[] public members;
    uint256 public quorum; // In percent of members (0-100)
    uint256 public requiredVotes;

    // Transactions and Payloads (Information Containers)
    // --------------------------------------------------
    // Payloads are mappings that use the same ID as the underlying transaction.
    // Each Transaction uses exactly one payload, depending on its type.
    enum TransactionType {
        invalid,
        addMember,
        removeMember,
        replaceMember,
        passTrophy,
        transferOwnership,
        changeQuorum,
        setBaseURI
    }
    struct Transaction {
        TransactionType txnType;
        bool executed;
    }

    Counters.Counter public transactionCount;
    mapping(uint256 => Transaction) public transactions;
    mapping(uint256 => mapping(address => bool)) public confirmations;

    mapping(uint256 => address) public addressPayloads;
    mapping(uint256 => uint256) public uintPayloads;
    mapping(uint256 => string) public stringPayloads;

    struct ReplaceMemberPayload {
        address oldMember;
        address newMember;
    }
    mapping(uint256 => ReplaceMemberPayload) public replaceMemberPayloads;

    struct PassTrophyPayload {
        uint256 currentTrophyId;
        string tournament;
        bytes32 infoHash;
        address[] winnerAddresses;
        string[] winnerNames;
    }
    mapping(uint256 => PassTrophyPayload) public passTrophyPayloads;


    // Modifiers

    modifier onlyMember() {
        require(isMember[msg.sender], "Gov: caller is not a member");
        _;
    }

    modifier validTransaction(uint256 _transactionId) {
        require(uint256(transactions[_transactionId].txnType) > 0, "Gov: invalid transaction");
        _;
    }


    // Contract Functions

    constructor (address _cifTrophyAddress, uint256 _initialQuorum, address[] memory _members) public {
        quorum = _initialQuorum;
        uint256 nMembers = _members.length;
        for (uint256 i = 0; i < nMembers; i++) {
            isMember[_members[i]] = true;
        }
        members = _members;
        _updateRequiredVotes();

        // The reference to the CIF Trophy contract can never be changed
        cifTrophyAddress = _cifTrophyAddress;
        _cifTrophy = ICifEsportsMultiTrophy(_cifTrophyAddress);
    }

    /// @dev Always rounds up to the next full number of members
    function _updateRequiredVotes() internal {
        requiredVotes = (members.length * quorum + 99) / 100;
    }

    function addMember(address _newMember) public onlyMember returns (uint256 transactionId) {
        require(_newMember != address(0), "Gov: new member is the zero address");
        require(!isMember[_newMember], "Gov: member already exists");
        transactionCount.increment();
        transactionId = transactionCount.current();
        transactions[transactionId] = Transaction(TransactionType.addMember, false);
        addressPayloads[transactionId] = _newMember;
        emit Submission(transactionId);
        confirmTransaction(transactionId);
        return transactionId;
    }

    function _addMember(uint256 _transactionId) internal validTransaction(_transactionId) {
        address _newMember = addressPayloads[_transactionId];
        require(_newMember != address(0), "Gov: new member is the zero address");
        require(!isMember[_newMember], "Gov: member already exists");
        isMember[_newMember] = true;
        members.push(_newMember);
        _updateRequiredVotes();
        emit MemberAddition(_newMember);
    }

    function removeMember(address _oldMember) public onlyMember returns (uint256 transactionId){
        require(isMember[_oldMember], "Gov: member does not exist");
        transactionCount.increment();
        transactionId = transactionCount.current();
        transactions[transactionId] = Transaction(TransactionType.removeMember, false);
        addressPayloads[transactionId] = _oldMember;
        emit Submission(transactionId);
        confirmTransaction(transactionId);
        return transactionId;
    }

    function _removeMember(uint256 _transactionId) internal validTransaction(_transactionId) {
        address _oldMember = addressPayloads[_transactionId];
        require(isMember[_oldMember], "Gov: member does not exist");
        isMember[_oldMember] = false;
        for (uint256 i = 0; i < members.length - 1; i++) {
            if (members[i] == _oldMember) {
                members[i] = members[members.length - 1];
                break;
            }
        }
        members.pop();
        _updateRequiredVotes();
        emit MemberRemoval(_oldMember);
    }

    function replaceMember(address _oldMember, address _newMember) public onlyMember returns (uint256 transactionId){
        require(_newMember != address(0), "Gov: new member is the zero address");
        require(isMember[_oldMember], "Gov: old member does not exist");
        require(!isMember[_newMember], "Gov: new member already exists");

        transactionCount.increment();
        transactionId = transactionCount.current();
        transactions[transactionId] = Transaction(TransactionType.replaceMember, false);
        replaceMemberPayloads[transactionId] = ReplaceMemberPayload(_oldMember, _newMember);
        emit Submission(transactionId);
        confirmTransaction(transactionId);
        return transactionId;
    }

    /// @dev More efficient than remove -> add
    function _replaceMember(uint256 _transactionId) internal validTransaction(_transactionId) {
        ReplaceMemberPayload storage _replacementAddresses = replaceMemberPayloads[_transactionId];
        require(_replacementAddresses.newMember != address(0), "Gov: new member is the zero address");
        require(isMember[_replacementAddresses.oldMember], "Gov: old member does not exist");
        require(!isMember[_replacementAddresses.newMember], "Gov: new member already exists");

        isMember[_replacementAddresses.oldMember] = false;
        isMember[_replacementAddresses.newMember] = true;
        for (uint256 i = 0; i < members.length; i++) {
            if (members[i] == _replacementAddresses.oldMember) {
                members[i] = _replacementAddresses.newMember;
                break;
            }
        }
        emit MemberRemoval(_replacementAddresses.oldMember);
        emit MemberAddition(_replacementAddresses.newMember);
    }

    function passTrophy(
        string memory _tournament,
        bytes32 _infoHash,
        address[] memory _winnerAddresses,
        string[] memory _winnerNames
    ) public onlyMember returns (uint256 transactionId) {
        require(_winnerAddresses.length == _winnerNames.length, "Gov: not same length for address- and name arrays");
        uint256 currentTrophyId = _cifTrophy.currentTrophyId();

        // Conditions for passing the trophy without quorum:
        // This prevents winners from passing the trophy to themselves.
        // 1. The transaction sender must be a governance member (checked in modifier)
        // 2. The transaction sender must own a token of the current trophy
        // 3. The transaction sender can't be a winner of the next trophy
        // 4. All winners of the next trophy must be governance members
        if (_cifTrophy.hasAddressCurrentTrophy(msg.sender)) {
            bool conditionsOk = true;
            for (uint256 i=0; i<_winnerAddresses.length; i++) {
                if (_winnerAddresses[i] == msg.sender || !isMember[_winnerAddresses[i]]) {
                    conditionsOk = false;
                    break;
                }
            }
            if (conditionsOk) {
                // No transaction is created, trophy is passed immediately
                _cifTrophy.passTrophy(_tournament, _infoHash, _winnerAddresses, _winnerNames);
                return 0;
            }
        }

        // Otherwise start a quorum vote to pass the trophy
        transactionCount.increment();
        transactionId = transactionCount.current();
        transactions[transactionId] = Transaction(TransactionType.passTrophy, false);
        passTrophyPayloads[transactionId] = PassTrophyPayload(
            currentTrophyId,
            _tournament,
            _infoHash,
            _winnerAddresses,
            _winnerNames
        );
        emit Submission(transactionId);
        confirmTransaction(transactionId);
        return transactionId;
    }

    function _passTrophy(uint256 _transactionId) internal validTransaction(_transactionId) {
        PassTrophyPayload storage payload = passTrophyPayloads[_transactionId];
        require(payload.currentTrophyId == _cifTrophy.currentTrophyId(), "Gov: trophy has been passed already");
        _cifTrophy.passTrophy(
            payload.tournament,
            payload.infoHash,
            payload.winnerAddresses,
            payload.winnerNames
        );
    }

    function transferOwnership(address _newOwner) public onlyMember returns (uint256 transactionId){
        require(_newOwner != address(0), "Gov: new owner is the zero address");
        transactionCount.increment();
        transactionId = transactionCount.current();
        transactions[transactionId] = Transaction(TransactionType.transferOwnership, false);
        addressPayloads[transactionId] = _newOwner;
        emit Submission(transactionId);
        confirmTransaction(transactionId);
        return transactionId;
    }

    function _transferOwnership(uint256 _transactionId) internal validTransaction(_transactionId) {
        _cifTrophy.transferOwnership(addressPayloads[_transactionId]);
    }

    function changeQuorum(uint256 _newQuorum) public onlyMember returns (uint256 transactionId){
        require(_newQuorum <= 100, "Gov: new quorum must be between 0 and 100");
        transactionCount.increment();
        transactionId = transactionCount.current();
        transactions[transactionId] = Transaction(TransactionType.changeQuorum, false);
        uintPayloads[transactionId] = _newQuorum;
        emit Submission(transactionId);
        confirmTransaction(transactionId);
        return transactionId;
    }

    function _changeQuorum(uint256 _transactionId) internal validTransaction(_transactionId) {
        uint256 _newQuorum = uintPayloads[_transactionId];
        uint256 _oldQuorum = quorum;
        quorum = _newQuorum;
        _updateRequiredVotes();
        emit QuorumChange(_oldQuorum, _newQuorum);
    }

    function setBaseURI(string memory _baseURI) public onlyMember returns (uint256 transactionId){
        transactionCount.increment();
        transactionId = transactionCount.current();
        transactions[transactionId] = Transaction(TransactionType.setBaseURI, false);
        stringPayloads[transactionId] = _baseURI;
        emit Submission(transactionId);
        confirmTransaction(transactionId);
        return transactionId;
    }

    function _setBaseURI(uint256 _transactionId) internal validTransaction(_transactionId) {
        _cifTrophy.setBaseURI(stringPayloads[_transactionId]);
    }

    function confirmTransaction(uint256 _transactionId) public onlyMember validTransaction(_transactionId) {
        require(!transactions[_transactionId].executed, "Gov: transaction already executed");
        require(!confirmations[_transactionId][msg.sender], "Gov: transaction already confirmed");
        confirmations[_transactionId][msg.sender] = true;
        emit Confirmation(msg.sender, _transactionId);
        executeTransaction(_transactionId);
    }

    function revokeConfirmation(uint256 _transactionId) public onlyMember validTransaction(_transactionId) {
        require(!transactions[_transactionId].executed, "Gov: transaction already executed");
        require(confirmations[_transactionId][msg.sender], "Gov: transaction not confirmed");
        confirmations[_transactionId][msg.sender] = false;
        emit Revocation(msg.sender, _transactionId);
    }

    function executeTransaction(uint256 _transactionId) public onlyMember validTransaction(_transactionId) returns (bool success){
        require(!transactions[_transactionId].executed, "Gov: transaction already executed");
        if (isConfirmed(_transactionId)) {
            Transaction storage txn = transactions[_transactionId];
            txn.executed = true;
            if (txn.txnType == TransactionType.addMember) {
                _addMember(_transactionId);
            } else if (txn.txnType == TransactionType.removeMember) {
                _removeMember(_transactionId);
            } else if (txn.txnType == TransactionType.replaceMember) {
                _replaceMember(_transactionId);
            } else if(txn.txnType == TransactionType.transferOwnership) {
                _transferOwnership(_transactionId);
            } else if (txn.txnType == TransactionType.passTrophy) {
                _passTrophy(_transactionId);
            } else if (txn.txnType == TransactionType.changeQuorum) {
                _changeQuorum(_transactionId);
            } else if (txn.txnType == TransactionType.setBaseURI) {
                _setBaseURI(_transactionId);
            } else {
                emit ExecutionFailure(_transactionId);
                return false;
            }
            emit Execution(_transactionId);
            return true;
        }
        return false;
    }

    function isConfirmed(uint256 _transactionId) public view validTransaction(_transactionId) returns (bool) {
        uint256 count = 0;
        for (uint256 i = 0; i < members.length; i++) {
            if (confirmations[_transactionId][members[i]]) {
                count += 1;
            }
            if (count == requiredVotes) {
                return true;
            }
        }
        return false;
    }


    // Web3 View Functions

    function getConfirmationCount(uint256 _transactionId) public view validTransaction(_transactionId) returns (uint256 count) {
        for (uint256 i=0; i<members.length; i++) {
            if (confirmations[_transactionId][members[i]]) {
                count += 1;
            }
        }
        return count;
    }

    function getMembers() external view returns (address[] memory _members) {
        return members;
    }

    function getConfirmations(uint256 _transactionId) external view returns (address[] memory _confirmations) {
        address[] memory confirmationsTemp = new address[](members.length);
        uint256 count = 0;
        uint256 i;
        for (i=0; i<members.length; i++) {
            if (confirmations[_transactionId][members[i]]) {
                confirmationsTemp[count] = members[i];
                count += 1;
            }
        }
        _confirmations = new address[](count);
        for (i=0; i<count; i++) {
            _confirmations[i] = confirmationsTemp[i];
        }
    }

    function getTransactionIds(bool isExecuted) external view returns (uint256[] memory _transactionIds)
    {
        uint256[] memory transactionIdsTemp = new uint[](transactionCount.current());
        uint256 count = 0;
        uint256 i;
        for (i=1; i<=transactionCount.current(); i++) {
            if (transactions[i].executed == isExecuted) {
                transactionIdsTemp[count] = i;
                count += 1;
            }
        }
        _transactionIds = new uint256[](count);
        for (i=0; i<count; i++) {
            _transactionIds[i] = transactionIdsTemp[i];
        }
        return _transactionIds;
    }
}
