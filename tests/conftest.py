#!/usr/bin/python3

import pytest


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    pass


@pytest.fixture(scope="module")
def deployer(accounts):
    yield accounts.add("0xa44fc21071fc5d66aa2a23f9ec0cb1efcaadfa5a9241cdf6b1613ee530e50fce")


@pytest.fixture(scope="module")
def gov_deployer(accounts):
    yield accounts.add("0xba4fb6a0a6d3d31cccff14edbc5434a649c1ac1e0c83733969065ebd88b3b6e4")


@pytest.fixture(scope="module")
def cif(CifEsportsMultiTrophy, deployer):
    cif = deployer.deploy(CifEsportsMultiTrophy)
    yield cif


@pytest.fixture(scope="module")
def gov(CifGovernance, cif, gov_deployer, accounts):
    gov = gov_deployer.deploy(CifGovernance, cif, 50, accounts[:4])
    yield gov
