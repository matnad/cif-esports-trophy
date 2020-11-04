import time


def test_trophy_info(cif, accounts):
    cif.passTrophy("Tournament 1", "0xdef", [accounts[0], accounts[1]], ["Jonas", "Daniel"])
    cif.passTrophy("Tournament 2", "0x123", [accounts[9]], ["Philipp"])

    info = cif.currentTrophy()
    assert info[0] == "Tournament 2"
    assert info[1] == 2
    assert str(info[2]).endswith("123")
    assert info[3] == ("Philipp",)
    assert info[4] == (3, )
    assert int(time.time()) - info[5] < 50

    info2 = cif.getInfoByTrophyId(2)
    for i in range(6):
        assert info[i] == info2[i]

    info3 = cif.getInfoByTrophyId(1)
    assert info3[0] == "Tournament 1"
    assert info3[1] == 1
    assert str(info3[2]).endswith("def")
    assert info3[3] == ("Jonas", "Daniel")
    assert info3[4] == (1, 2)
    assert int(time.time()) - info3[5] < 50

    info4 = cif.getInfoByTokenId(2)
    for i in range(6):
        assert info3[i] == info4[i]

    assert cif.hasAddressCurrentTrophy(accounts[9])
    assert cif.currentTrophyId() == 2

