import brownie

CHANGE_QUORUM = 6


def test_change_quorum(gov, accounts):
    assert gov.quorum() == 50
    new_quorum = 75

    tx = gov.changeQuorum(new_quorum, {'from': accounts[0]})
    assert tx.return_value == 1

    # Verify Tx State
    assert tx.events["Submission"]["transactionId"] == 1
    assert tx.events["Confirmation"]["sender"] == accounts[0]
    assert tx.events["Confirmation"]["transactionId"] == 1
    assert gov.getConfirmationCount(1) == 1

    tx_info = gov.transactions(1)
    assert tx_info[0] == CHANGE_QUORUM
    assert not tx_info[1]  # executed
    assert gov.uintPayloads(1) == new_quorum

    # Check Can't Execute
    tx_fail = gov.executeTransaction(1, {'from': accounts[0]})
    assert "Executed" not in tx_fail.events
    assert not gov.transactions(1)[1]
    assert gov.quorum != new_quorum
    assert not tx_fail.return_value

    # Confirm and Execute
    tx_ok = gov.confirmTransaction(1, {'from': accounts[2]})

    # Check Events
    assert tx_ok.events["Confirmation"]["sender"] == accounts[2]
    assert tx_ok.events["Confirmation"]["transactionId"] == 1
    assert tx_ok.events["QuorumChange"]["oldQuorum"] == 50
    assert tx_ok.events["QuorumChange"]["newQuorum"] == new_quorum
    assert tx_ok.events["Execution"]["transactionId"] == 1

    assert gov.transactions(1)[1]  # executed

    assert gov.quorum() == 75
    assert gov.requiredVotes() == 3  # New Quorum: 75% of 4 is 3


def test_change_quorum_reverts(gov, accounts):
    with brownie.reverts("Gov: caller is not a member"):
        gov.changeQuorum(1, {'from': accounts[9]})

    with brownie.reverts("Gov: new quorum must be between 0 and 100"):
        gov.changeQuorum(150, {'from': accounts[1]})
