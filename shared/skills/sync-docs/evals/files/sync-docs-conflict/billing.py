"""Billing fixture with an unresolved code/docs conflict."""


def create_charge(account_id, amount):
    """Create a charge through the endpoint currently used by the pilot."""
    return {
        "account_id": account_id,
        "amount_usd": amount,
        "endpoint": "/legacy/charges",
    }
