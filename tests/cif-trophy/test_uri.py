import brownie


def test_uri(cif, accounts):
    cif.passTrophy(
        "Tournament 1",
        "0xabc",
        [accounts[0], accounts[1]],
        ["Jonas", "Daniel"]
    )

    cif.setTokenURI(2, "http://example.com/tour-1/2")
    assert cif.tokenURI(2) == "http://example.com/tour-1/2"

    cif.setBaseURI("http://example.com/")
    assert cif.tokenURI(1) == "http://example.com/1"

    cif.setTokenURI(1, "tour-1/1")
    assert cif.tokenURI(1) == "http://example.com/tour-1/1"


def test_uri_reverts(cif, accounts):
    with brownie.reverts("Ownable: caller is not the owner"):
        cif.setBaseURI("http://example.com/", {'from': accounts[0]})
