import brownie


def test_deploy(cif, deployer):
    assert cif.totalSupply() == 0
    assert cif.address == "0xC1f000000234AF1E3770eB17fA0C837E703f9b29"
    assert cif.owner() == deployer.address

    '''
    bytes4(keccak256('name()')) == 0x06fdde03
    bytes4(keccak256('symbol()')) == 0x95d89b41
    bytes4(keccak256('tokenURI(uint256)')) == 0xc87b56dd
     
    => 0x06fdde03 ^ 0x95d89b41 ^ 0xc87b56dd == 0x5b5e139f
    '''
    assert cif.supportsInterface("0x5b5e139f")
    assert cif.name() == "CIF ESports Trophy"
    assert cif.symbol() == "CIF"
    assert cif.baseURI() == ""


def test_no_tokens_reverts(cif):
    with brownie.reverts("Cif: trophy does not exist"):
        cif.currentTrophy()
    with brownie.reverts("ERC721Metadata: URI query for nonexistent token"):
        cif.tokenURI(0)

