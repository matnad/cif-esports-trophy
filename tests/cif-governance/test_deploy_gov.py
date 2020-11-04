def test_deploy(gov, cif, accounts):
    assert gov.address == "0xC1FffFff65E7521597195FE011dd96a044761315"
    assert gov.cifTrophyAddress() == cif.address

    members = gov.getMembers()
    assert members == tuple(accounts[:4])

    for i, m in enumerate(accounts[:6]):
        if i < 4:
            assert gov.isMember(m)
        else:
            assert not gov.isMember(m)

    assert gov.quorum() == 50
    assert gov.requiredVotes() == 2
    assert gov.transactionCount() == 0
