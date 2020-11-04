import brownie


def test_first_trophy_team(cif, deployer, accounts):
    cif.passTrophy(
        "Tournament 1",
        "0xabc",
        [accounts[0], accounts[1], accounts[2]],
        ["Jonas", "Daniel", "Hannes"],
        {'from': deployer}
    )

    assert cif.currentTrophyId() == 1
    trophy = cif.trophies(1)
    assert trophy[0] == "Tournament 1"
    assert str(trophy[1]).endswith("abc")
    assert brownie.chain.time() - trophy[2] < 100

    token1 = cif.winners(1)
    assert token1[0] == 1  # trophyId
    assert token1[1] == "Jonas"
    assert cif.ownerOf(1) == accounts[0]

    token2 = cif.winners(2)
    assert token2[0] == 1  # trophyId
    assert token2[1] == "Daniel"
    assert cif.ownerOf(2) == accounts[1]

    token3 = cif.winners(3)
    assert token3[0] == 1  # trophyId
    assert token3[1] == "Hannes"
    assert cif.ownerOf(3) == accounts[2]


def test_two_trophies(cif, accounts):
    cif.passTrophy("Tournament 1", "0xdef", [accounts[0], accounts[1]], ["Jonas", "Daniel"])
    cif.passTrophy("Tournament 2", "0x123", [accounts[9]], ["Philipp"])

    t1 = cif.trophies(1)
    t2 = cif.trophies(2)

    assert cif.currentTrophyId() == 2
    assert t1[0] == "Tournament 1"
    assert t2[0] == "Tournament 2"
    assert str(t2[1]).endswith("123")
    assert t1[2] <= t2[2]

    tkn3 = cif.winners(3)
    assert tkn3[0] == 2
    assert tkn3[1] == "Philipp"

    assert not cif.hasAddressCurrentTrophy(accounts[0])
    assert cif.hasAddressCurrentTrophy(accounts[9])


def test_pass_trophy_reverts(cif, accounts):
    with brownie.reverts("Ownable: caller is not the owner"):
        cif.passTrophy(
            "Tournament 1",
            "0xabc",
            [accounts[0], accounts[1], accounts[2]],
            ["Jonas", "Daniel", "Hannes"],
            {'from': accounts[0]}
        )

    with brownie.reverts("Cif: not same length for address- and name arrays"):
        cif.passTrophy(
            "Tournament 1",
            "0xabc",
            [accounts[0], accounts[1]],
            ["Jonas", "Daniel", "Hannes"]
        )

    with brownie.reverts("Cif: not same length for address- and name arrays"):
        cif.passTrophy(
            "Tournament 1",
            "0xabc",
            [accounts[0], accounts[1]],
            ["Jonas"]
        )

