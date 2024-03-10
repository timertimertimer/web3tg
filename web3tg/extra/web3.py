from web3db.models import Profile


def get_evm_address(profile: Profile) -> str:
    return profile.evm_address


def get_aptos_address(profile: Profile) -> str:
    return profile.aptos_address


def get_solana_address(profile: Profile) -> str:
    return profile.solana_address
