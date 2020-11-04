import brownie

TRANSFER_OWNERSHIP = 5
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_transfer_ownership(gov, cif, deployer, accounts):
    cif.transferOwnership(gov, {'from': deployer})
    assert cif.owner() == gov

    new_owner = accounts[0]
    tx = gov.transferOwnership(new_owner, {'from': accounts[0]})
    assert tx.return_value == 1

    # Verify Tx State
    assert tx.events["Submission"]["transactionId"] == 1
    assert tx.events["Confirmation"]["sender"] == accounts[0]
    assert tx.events["Confirmation"]["transactionId"] == 1
    assert gov.getConfirmationCount(1) == 1
    assert not gov.isConfirmed(1)
    assert not gov.transactions(1)[1]  # executed

    tx_info = gov.transactions(1)
    assert tx_info[0] == TRANSFER_OWNERSHIP
    assert not tx_info[1]  # executed
    assert gov.addressPayloads(1) == new_owner

    # Check Can't Execute
    tx_fail = gov.executeTransaction(1, {'from': accounts[0]})
    assert "Executed" not in tx_fail.events
    assert not gov.transactions(1)[1]
    assert cif.owner() == gov
    assert not tx_fail.return_value  # returns false on failed execution

    # Confirm and Execute
    tx_ok = gov.confirmTransaction(1, {'from': accounts[2]})

    # Check Events
    assert tx_ok.events["Confirmation"]["sender"] == accounts[2]
    assert tx_ok.events["Confirmation"]["transactionId"] == 1
    assert tx_ok.events["OwnershipTransferred"]["previousOwner"] == gov
    assert tx_ok.events["OwnershipTransferred"]["newOwner"] == new_owner
    assert tx_ok.events["Execution"]["transactionId"] == 1

    assert gov.transactions(1)[1]  # executed
    assert cif.owner() == new_owner


def test_transfer_ownership_reverts(gov, accounts):
    with brownie.reverts("Gov: caller is not a member"):
        gov.transferOwnership(accounts[0], {'from': accounts[7]})

    with brownie.reverts("Gov: new owner is the zero address"):
        gov.transferOwnership(ZERO_ADDRESS, {'from': accounts[1]})

