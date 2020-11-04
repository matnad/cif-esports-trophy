import brownie


def test_invalid_transaction(gov, accounts):
    with brownie.reverts("Gov: invalid transaction"):
        gov.confirmTransaction(2, {'from': accounts[0]})
