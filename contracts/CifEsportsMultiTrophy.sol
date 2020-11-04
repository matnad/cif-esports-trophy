//SPDX-License-Identifier: MIT
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract CifEsportsMultiTrophy is ERC721, Ownable  {
    using Counters for Counters.Counter;
    Counters.Counter private _trophyIds;
    Counters.Counter private _winnerIds;

    event TrophyPassed(uint256 indexed trophyId, bytes32 infoHash);

    struct Trophy {
        string tournament;
        bytes32 infoHash;
        uint256 timeReceived;
        uint256[] winnerIds;
    }
    mapping(uint256 => Trophy) public trophies;

    struct Winner {
        uint256 trophyId;
        string name;
    }
    mapping(uint256 => Winner) public winners;

    constructor() public ERC721("CIF ESports Trophy", "CIF") {
    }

    function setBaseURI(string memory baseURI_) public onlyOwner {
        _setBaseURI(baseURI_);
    }

    function setTokenURI(uint256 tokenId, string memory _tokenURI) public onlyOwner {
        _setTokenURI(tokenId, _tokenURI);
    }

    function passTrophy(
        string memory _tournament,
        bytes32 _infoHash,
        address[] memory _winnerAddresses,
        string[] memory _winnerNames
    ) public onlyOwner {
        uint256 nWinners = _winnerAddresses.length;
        require(nWinners == _winnerNames.length, "Cif: not same length for address- and name arrays");

        _trophyIds.increment();
        uint256 newTrophyId = _trophyIds.current();
        uint256[] memory winnerIds = new uint256[](nWinners);

        for (uint256 i=0; i < nWinners; i++) {
            _winnerIds.increment();
            uint256 newWinnerId = _winnerIds.current();
            winners[newWinnerId] = Winner(newTrophyId, _winnerNames[i]);
            winnerIds[i] = newWinnerId;
            _safeMint(_winnerAddresses[i], newWinnerId);
        }
        trophies[newTrophyId] = Trophy(_tournament, _infoHash, block.timestamp, winnerIds);
        emit TrophyPassed(newTrophyId, _infoHash);
    }

    function getInfoByTrophyId(uint256 _trophyId) public view returns (
        string memory tournament,
        uint256 trophyId,
        bytes32 infoHash,
        string[] memory winners_,
        uint256[] memory tokenIds,
        uint256 timeReceived,
        uint256 timePassedOn
    ) {
        require(_trophyId > 0 && _trophyId <= _trophyIds.current(), "Cif: trophy does not exist");
        Trophy storage trophy = trophies[_trophyId];
        winners_ = new string[](trophy.winnerIds.length);
        for (uint256 i = 0; i < trophy.winnerIds.length; i++) {
            winners_[i] = winners[trophy.winnerIds[i]].name;
        }
        if (_trophyId < _trophyIds.current()) {
            timePassedOn = trophies[_trophyId + 1].timeReceived;
        }
        return (trophy.tournament, _trophyId, trophy.infoHash, winners_, trophy.winnerIds, trophy.timeReceived, timePassedOn);
    }

    function getInfoByTokenId(uint256 _tokenId) external view returns (
        string memory tournament,
        uint256 trophyId,
        bytes32 infoHash,
        string[] memory winners_,
        uint256[] memory tokenIds,
        uint256 timeReceived,
        uint256 timePassedOn
    ) {
        require(_exists(_tokenId), "Cif: token does not exist");
        return getInfoByTrophyId(winners[_tokenId].trophyId);
    }

    function currentTrophy() external view returns (
        string memory tournament,
        uint256 trophyId,
        bytes32 infoHash,
        string[] memory winners_,
        uint256[] memory tokenIds,
        uint256 timeReceived,
        uint256 timePassedOn
    ) {
        return getInfoByTrophyId(_trophyIds.current());
    }

    function currentTrophyId() public view returns (uint256 trophyId) {
        return _trophyIds.current();
    }

    function hasAddressCurrentTrophy(address _holder) public view returns (bool ownsCurrent) {
        Trophy storage trophy = trophies[_trophyIds.current()];
        for (uint256 i=0; i<trophy.winnerIds.length; i++) {
            if (_holder == ownerOf(trophy.winnerIds[i])) {
                return true;
            }
        }
        return false;
    }
}
