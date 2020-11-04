import brownie


def test_owner_transfer_reverts(cif, accounts):
    with brownie.reverts("Ownable: caller is not the owner"):
        cif.transferOwnership(accounts[0], {'from': accounts[0]})


def test_owner_transfer(cif, deployer, accounts):
    assert cif.owner() == deployer
    cif.transferOwnership(accounts[0], {'from': deployer})
    assert cif.owner() == accounts[0]
