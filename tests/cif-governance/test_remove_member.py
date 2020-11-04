import brownie

REMOVE_MEMBER = 2


def test_remove_member(gov, accounts):
    # Add a fifth member
    assert len(gov.getMembers()) == 4
    gov.addMember(accounts[9], {'from': accounts[0]})
    gov.confirmTransaction(1, {'from': accounts[2]})
    assert len(gov.getMembers()) == 5
    assert gov.requiredVotes() == 3

    # Submit Removal
    to_remove = accounts[1]
    tx = gov.removeMember(to_remove, {'from': accounts[0]})
    assert tx.return_value == 2

    # Verify Tx State
    assert tx.events["Submission"]["transactionId"] == 2
    assert tx.events["Confirmation"]["sender"] == accounts[0]
    assert tx.events["Confirmation"]["transactionId"] == 2
    assert gov.getConfirmationCount(2) == 1
    assert not gov.isConfirmed(2)
    assert gov.confirmations(2, accounts[0])
    for m in accounts[3:5]:
        assert not gov.confirmations(2, m)
    assert gov.transactionCount() == 2

    tx_info = gov.transactions(2)
    assert tx_info[0] == REMOVE_MEMBER
    assert not tx_info[1]  # executed
    assert gov.addressPayloads(2) == to_remove

    assert gov.getTransactionIds(False) == [2]
    assert gov.getTransactionIds(True) == [1]

    # Check Can't Execute
    tx_fail = gov.executeTransaction(2, {'from': accounts[0]})
    assert "Executed" not in tx_fail.events
    assert not gov.transactions(2)[1]
    assert gov.isMember(to_remove)
    assert not tx_fail.return_value  # returns false on failed execution

    # Check Confirm Twice
    with brownie.reverts("Gov: transaction already confirmed"):
        gov.confirmTransaction(2, {'from': accounts[0]})

    # Confirm and Execute (required Votes = 3)
    tx_c = gov.confirmTransaction(2, {'from': accounts[2]})
    assert tx_c.events["Confirmation"]["sender"] == accounts[2]
    assert tx_c.events["Confirmation"]["transactionId"] == 2
    assert "Submission" not in tx_c.events
    assert "Execution" not in tx_c.events
    assert gov.isMember(to_remove)

    tx_ok = gov.confirmTransaction(2, {'from': accounts[9]})

    # Check Events
    assert tx_ok.events["Confirmation"]["sender"] == accounts[9]
    assert tx_ok.events["Confirmation"]["transactionId"] == 2
    assert tx_ok.events["MemberRemoval"]["member"] == to_remove
    assert tx_ok.events["Execution"]["transactionId"] == 2

    assert gov.getConfirmationCount(2) == 3
    assert gov.confirmations(2, accounts[9])
    assert gov.isConfirmed(2)
    assert gov.transactions(2)[1]  # executed
    assert gov.getTransactionIds(False) == []
    assert gov.getTransactionIds(True) == [1, 2]

    members = gov.getMembers()
    assert len(members) == 4
    assert to_remove not in members
    assert not gov.isMember(to_remove)
    assert gov.requiredVotes() == 2  # New Quorum: 50% of 4 is 2

    # can no longer confirm
    with brownie.reverts("Gov: transaction already executed"):
        gov.confirmTransaction(2, {'from': accounts[0]})


def test_add_member_reverts(gov, accounts):
    with brownie.reverts("Gov: caller is not a member"):
        gov.removeMember(accounts[1], {'from': accounts[7]})

    with brownie.reverts("Gov: member does not exist"):
        gov.removeMember(accounts[7], {'from': accounts[1]})

