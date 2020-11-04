import brownie

ADD_MEMBER = 1
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_add_member(gov, accounts):
    to_add = accounts[9]
    tx = gov.addMember(to_add, {'from': accounts[0]})
    assert tx.return_value == 1

    # Verify Tx State
    assert tx.events["Submission"]["transactionId"] == 1
    assert tx.events["Confirmation"]["sender"] == accounts[0]
    assert tx.events["Confirmation"]["transactionId"] == 1
    assert gov.getConfirmationCount(1) == 1
    assert gov.getConfirmationCount(1) < gov.requiredVotes()
    assert not gov.isConfirmed(1)
    assert gov.confirmations(1, accounts[0])
    for m in accounts[3:5]:
        assert not gov.confirmations(1, m)
    assert gov.transactionCount() == 1

    tx_info = gov.transactions(1)
    assert tx_info[0] == ADD_MEMBER
    assert not tx_info[1]  # executed
    assert gov.addressPayloads(1) == to_add

    assert gov.getTransactionIds(False) == [1]
    assert gov.getTransactionIds(True) == []

    # Check Can't Execute
    tx_fail = gov.executeTransaction(1, {'from': accounts[0]})
    assert "Executed" not in tx_fail.events
    assert not gov.transactions(1)[1]
    assert not gov.isMember(to_add)
    assert not tx_fail.return_value  # returns false on failed execution

    # Confirm and Execute
    tx_ok = gov.confirmTransaction(1, {'from': accounts[2]})

    # Check Events
    assert tx_ok.events["Confirmation"]["sender"] == accounts[2]
    assert tx_ok.events["Confirmation"]["transactionId"] == 1
    assert tx_ok.events["MemberAddition"]["member"] == to_add
    assert tx_ok.events["Execution"]["transactionId"] == 1

    assert gov.getConfirmationCount(1) == 2
    assert gov.confirmations(1, accounts[2])
    assert gov.getConfirmations(1) == [accounts[0], accounts[2]]
    assert not gov.isConfirmed(1)  # The new member will push the quorum to 3
    assert gov.transactions(1)[1]  # executed
    assert gov.getTransactionIds(False) == []
    assert gov.getTransactionIds(True) == [1]

    members = gov.getMembers()
    assert len(members) == 5
    assert members[-1] == to_add
    assert gov.isMember(to_add)
    assert gov.requiredVotes() == 3  # New Quorum: 50% of 5 is 3

    # can no longer confirm
    with brownie.reverts("Gov: transaction already executed"):
        gov.confirmTransaction(1, {'from': accounts[1]})


def test_add_member_reverts(gov, accounts):
    with brownie.reverts("Gov: caller is not a member"):
        gov.addMember(accounts[9], {'from': accounts[9]})

    with brownie.reverts("Gov: member already exists"):
        gov.addMember(accounts[1], {'from': accounts[1]})

    with brownie.reverts("Gov: new member is the zero address"):
        gov.addMember(ZERO_ADDRESS, {'from': accounts[1]})

