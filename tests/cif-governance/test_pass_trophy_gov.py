import brownie
import pytest

PASS_TROPHY = 4


@pytest.fixture(scope="module")
def gov_trophy(gov, cif, deployer, accounts):
    cif.transferOwnership(gov, {'from': deployer})
    gov.passTrophy(
        "Tournament 1",
        "0xa1b2",
        [accounts[2], accounts[8]],
        ["Daniel", "Markus"],
        {'from': accounts[2]}
    )
    gov.confirmTransaction(1, {'from': accounts[1]})
    assert cif.hasAddressCurrentTrophy(accounts[2])
    assert gov.transactionCount() == 1
    assert cif.currentTrophyId() == 1
    yield gov


def test_pass_trophy_quorum(gov, cif, deployer, accounts):
    cif.transferOwnership(gov, {'from': deployer})
    tx = gov.passTrophy(
        "Tournament 1",
        "0xa1b2",
        [accounts[0], accounts[8]],
        ["Daniel", "Markus"],
        {'from': accounts[0]}
    )
    assert tx.return_value == 1

    # Verify Tx State
    assert tx.events["Submission"]["transactionId"] == 1
    assert tx.events["Confirmation"]["sender"] == accounts[0]
    assert tx.events["Confirmation"]["transactionId"] == 1
    assert gov.getConfirmationCount(1) == 1
    assert not gov.isConfirmed(1)
    assert gov.confirmations(1, accounts[0])
    assert gov.transactionCount() == 1

    tx_info = gov.transactions(1)
    assert tx_info[0] == PASS_TROPHY
    assert not tx_info[1]  # executed
    payload = gov.passTrophyPayloads(1)
    assert payload[0] == cif.currentTrophyId()
    assert payload[1] == "Tournament 1"
    assert str(payload[2]).endswith("a1b2")

    # Check Can't Execute
    tx_fail = gov.executeTransaction(1, {'from': accounts[0]})
    assert "Executed" not in tx_fail.events
    assert not gov.transactions(1)[1]
    assert cif.currentTrophyId() == 0
    assert not tx_fail.return_value  # returns false on failed execution

    # Confirm and Execute
    tx_ok = gov.confirmTransaction(1, {'from': accounts[2]})

    # Check Events
    assert tx_ok.events["Confirmation"]["sender"] == accounts[2]
    assert tx_ok.events["Confirmation"]["transactionId"] == 1
    assert tx_ok.events["Execution"]["transactionId"] == 1
    assert tx_ok.events["TrophyPassed"]["trophyId"] == 1

    assert gov.isConfirmed(1)  # The new member will push the quorum to 3
    assert gov.transactions(1)[1]  # executed

    assert cif.currentTrophyId() == 1
    assert cif.ownerOf(2) == accounts[8]


def test_pass_trophy_by_owner(gov_trophy, cif, accounts):
    # Pass Trophy by Owner respecting all conditions, should not generate a transaction
    tx = gov_trophy.passTrophy(
        "Tournament 2",
        "0xc3d4",
        [accounts[3], accounts[0]],
        ["Herbert", "Fridolin"],
        {'from': accounts[2]}
    )

    assert gov_trophy.transactionCount() == 1
    assert "Execution" not in tx.events
    assert "Confirmation" not in tx.events
    assert tx.events["TrophyPassed"]["trophyId"] == 2
    assert cif.currentTrophyId() == 2
    assert cif.ownerOf(3) == accounts[3]
    assert cif.winners(3)[1] == "Herbert"
    assert cif.currentTrophy()[0] == "Tournament 2"

    assert not cif.hasAddressCurrentTrophy(accounts[2])
    assert cif.hasAddressCurrentTrophy(accounts[3])


def test_pass_to_self(gov_trophy, cif, accounts):
    # Pass Trophy by Owner to self, should generate a transaction
    assert cif.hasAddressCurrentTrophy(accounts[2])
    tx_count = gov_trophy.transactionCount()
    tx = gov_trophy.passTrophy(
        "Tournament 2",
        "0xc3d4",
        [accounts[3], accounts[2]],
        ["Herbert", "Fridolin"],
        {'from': accounts[2]}
    )
    assert "TrophyPassed" not in tx.events
    assert cif.currentTrophyId() == 1
    assert gov_trophy.transactionCount() == tx_count + 1


def test_pass_to_non_member(gov_trophy, cif, accounts):
    # Pass Trophy by Owner to non governance member, should generate a transaction
    assert cif.hasAddressCurrentTrophy(accounts[2])
    tx_count = gov_trophy.transactionCount()
    tx = gov_trophy.passTrophy(
        "Tournament 2",
        "0xc3d4",
        [accounts[3], accounts[8]],
        ["Herbert", "Fridolin"],
        {'from': accounts[2]}
    )
    assert "TrophyPassed" not in tx.events
    assert cif.currentTrophyId() == 1
    assert gov_trophy.transactionCount() == tx_count + 1


def test_pass_trophy_racecondition(gov_trophy, cif, accounts):
    """ Quorum Vote is initiated, then Owner passes Trophy. """
    # Start Vote
    assert not cif.hasAddressCurrentTrophy(accounts[3])  # 2 and 8 have trophy
    tx = gov_trophy.passTrophy(
        "Tournament 2",
        "0xffff",
        [accounts[0], accounts[1]],
        ["Pascal", "Miguel"],
        {'from': accounts[3]}
    )
    pass_id = tx.return_value

    # Owner Transfers
    assert cif.hasAddressCurrentTrophy(accounts[2])
    tx = gov_trophy.passTrophy(
        "Tournament 2",
        "0xffff",
        [accounts[3], accounts[1]],
        ["Pascal", "Miguel"],
        {'from': accounts[2]}
    )
    assert "TrophyPassed" in tx.events
    assert cif.currentTrophyId() == 2

    # Execute Vote but trophy is already passed
    with brownie.reverts("Gov: trophy has been passed already"):
        gov_trophy.confirmTransaction(pass_id, {'from': accounts[0]})
    assert cif.currentTrophyId() == 2


def test_pass_trophy_reverts(gov_trophy, accounts):
    with brownie.reverts("Gov: caller is not a member"):
        gov_trophy.passTrophy(
            "Tournament 1",
            "0xa1b2",
            [accounts[0], accounts[8]],
            ["Daniel", "Markus"],
            {'from': accounts[8]}
        )

    with brownie.reverts("Gov: not same length for address- and name arrays"):
        gov_trophy.passTrophy(
            "Tournament 1",
            "0xabc",
            [accounts[0], accounts[1]],
            ["Jonas", "Daniel", "Hannes"],
            {'from': accounts[1]}
        )
