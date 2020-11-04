import brownie


def test_revoke_confirmation(gov, accounts):
    gov.addMember(accounts[9], {'from': accounts[0]})
    assert gov.getConfirmationCount(1) == 1

    tx = gov.revokeConfirmation(1, {'from': accounts[0]})
    assert gov.getConfirmationCount(1) == 0
    assert tx.events["Revocation"]["sender"] == accounts[0]
    assert tx.events["Revocation"]["transactionId"] == 1

    with brownie.reverts("Gov: transaction not confirmed"):
        gov.revokeConfirmation(1, {'from': accounts[0]})

    gov.confirmTransaction(1, {'from': accounts[0]})
    gov.confirmTransaction(1, {'from': accounts[1]})
    assert gov.isMember(accounts[9])

    with brownie.reverts("Gov: transaction already executed"):
        gov.revokeConfirmation(1, {'from': accounts[0]})
