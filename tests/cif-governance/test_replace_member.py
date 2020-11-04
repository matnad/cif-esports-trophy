import brownie

REPLACE_MEMBER = 3
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_replace_member(gov, accounts):
    to_add = accounts[8]
    to_remove = accounts[0]
    tx = gov.replaceMember(to_remove, to_add, {'from': accounts[0]})
    assert tx.return_value == 1

    # Verify Tx State
    assert tx.events["Submission"]["transactionId"] == 1
    assert tx.events["Confirmation"]["sender"] == accounts[0]
    assert tx.events["Confirmation"]["transactionId"] == 1
    assert gov.getConfirmationCount(1) == 1

    tx_info = gov.transactions(1)
    assert tx_info[0] == REPLACE_MEMBER
    assert not tx_info[1]  # executed
    assert gov.replaceMemberPayloads(1) == (to_remove, to_add)

    # Check Can't Execute
    tx_fail = gov.executeTransaction(1, {'from': accounts[0]})
    assert "Executed" not in tx_fail.events
    assert not gov.transactions(1)[1]
    assert not gov.isMember(to_add)
    assert gov.isMember(to_remove)
    assert not tx_fail.return_value  # returns false on failed execution

    # Confirm and Execute
    tx_ok = gov.confirmTransaction(1, {'from': accounts[2]})

    # Check Events
    assert tx_ok.events["Confirmation"]["sender"] == accounts[2]
    assert tx_ok.events["Confirmation"]["transactionId"] == 1
    assert tx_ok.events["MemberAddition"]["member"] == to_add
    assert tx_ok.events["MemberRemoval"]["member"] == to_remove
    assert tx_ok.events["Execution"]["transactionId"] == 1

    assert gov.requiredVotes() == 2
    assert gov.transactions(1)[1]  # executed

    members = gov.getMembers()
    assert len(members) == 4
    assert to_add in members
    assert to_remove not in members
    assert gov.isMember(to_add)
    assert not gov.isMember(to_remove)


def test_replace_member_reverts(gov, accounts):
    with brownie.reverts("Gov: caller is not a member"):
        gov.replaceMember(accounts[0], accounts[9], {'from': accounts[9]})

    with brownie.reverts("Gov: old member does not exist"):
        gov.replaceMember(accounts[8], accounts[7], {'from': accounts[1]})

    with brownie.reverts("Gov: new member already exists"):
        gov.replaceMember(accounts[1], accounts[2], {'from': accounts[1]})

    with brownie.reverts("Gov: new member already exists"):
        gov.replaceMember(accounts[2], accounts[2], {'from': accounts[1]})

    with brownie.reverts("Gov: new member is the zero address"):
        gov.replaceMember(accounts[1], ZERO_ADDRESS, {'from': accounts[1]})

