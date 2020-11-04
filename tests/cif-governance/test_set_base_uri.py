import brownie

SET_BASE_URI = 7


def test_set_base_uri(gov, cif, deployer, accounts):
    cif.transferOwnership(gov, {'from': deployer})
    assert cif.baseURI() == ""
    new_base_uri = "http://example.com/cif/"

    tx = gov.setBaseURI(new_base_uri, {'from': accounts[0]})
    assert tx.return_value == 1

    # Verify Tx State
    assert tx.events["Submission"]["transactionId"] == 1
    assert tx.events["Confirmation"]["sender"] == accounts[0]
    assert tx.events["Confirmation"]["transactionId"] == 1
    assert gov.getConfirmationCount(1) == 1

    tx_info = gov.transactions(1)
    assert tx_info[0] == SET_BASE_URI
    assert not tx_info[1]  # executed
    assert gov.stringPayloads(1) == new_base_uri

    # Check Can't Execute
    tx_fail = gov.executeTransaction(1, {'from': accounts[0]})
    assert "Executed" not in tx_fail.events
    assert not gov.transactions(1)[1]
    assert cif.baseURI() == ""
    assert not tx_fail.return_value

    # Confirm and Execute
    tx_ok = gov.confirmTransaction(1, {'from': accounts[2]})

    # Check Events
    assert tx_ok.events["Confirmation"]["sender"] == accounts[2]
    assert tx_ok.events["Confirmation"]["transactionId"] == 1
    assert tx_ok.events["Execution"]["transactionId"] == 1

    assert gov.transactions(1)[1]  # executed

    assert cif.baseURI() == new_base_uri


def test_change_quorum_reverts(gov, accounts):
    with brownie.reverts("Gov: caller is not a member"):
        gov.setBaseURI("foo", {'from': accounts[9]})

