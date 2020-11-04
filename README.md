# CIF E-Sports NFT 

Repository for the CIF E-Sports Trophy and Governance contracts.

## Trophy Contract

ERC721 compliant Non-Fungible Token Contract to track the E-Sports Trophy for the Center of Innovative Finance, University of Basel.

Each concluded tournament creates a new Trophy.
All winners of the tournament receive an ERC721 token with their name on it and a reference to the Trophy.

The Trophy stores:
* Tournament Name
* Hash for tournament details and results located at `tokenURI(_tokenId)`
* Timestamp when the trophy was received
* Tokens of the winners

## Governance Contract

Governance Contract for the CIF E-Sports Trophy. Works as a multisig with flexible quorum for the following, limited action space: 
* Add Member
* Remove Member
* Replace Member
* Change Quorum

When set as the owner of the CIF E-Sports Trophy contract, supports the following actions on the Trophy contract with the same multisig requirements:
* Pass Trophy
* Set Base URI
* Transfer Ownership

The Trophy can be passed without a quorum vote if the following conditions are met:
1. The transaction sender must be a governance member
2. The transaction sender must own a token of the current trophy
3. The transaction sender cannot be a winner of the next trophy
4. All winners of the next trophy must be governance members

## Addresses
Deployed on Main Net and Ropsten.
CIF Trophy: 0xC1f000000234AF1E3770eB17fA0C837E703f9b29
CIF Governance: 0xC1FffFff65E7521597195FE011dd96a044761315

## Tests
To run tests clone repo, create new python 3.7+ virtual environment, then:
```
pip install eth-brownie
brownie test -n auto
```