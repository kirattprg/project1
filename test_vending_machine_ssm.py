"""
TPRG2131 – Project 1 – Vending Machine
PyTest Script
Student: Sachkerat Singh Matharoo
ID: 100996938
"""

from vending_machine_ssm import (
    VendingMachine,
    WaitingState,
    AddCoinsState,
    DeliverProductState,
    CountChangeState
)

def test_VendingMachine():

    # Build and initialize machine
    v = VendingMachine()
    v.add_state(WaitingState())
    v.add_state(AddCoinsState())
    v.add_state(DeliverProductState())
    v.add_state(CountChangeState())
    v.go_to_state("waiting")

    # Ensure starting state
    assert v.state.name == "waiting"
    assert v.amount == 0

    # Insert 10 cents
    v.event = "10"
    v.update()
    assert v.state.name == "add_coins"
    assert v.amount == 10

    # Add another 10 cents
    v.event = "10"
    v.update()
    assert v.amount == 20

    # Try selecting gum (cost 25) → should NOT dispense
    v.event = "gum"
    v.update()
    assert v.state.name == "add_coins"
    assert v.amount == 20

    # Insert 25-cent coin
    v.event = "25"
    v.update()
    assert v.amount == 45

    # Now gum should dispense
    v.event = "gum"
    v.update()
    assert v.state.name == "deliver_product"

    # Deliver → should move to count_change
    v.update()
    assert v.state.name == "count_change"

    # Change due should be 20 cents (45 - 25)
    assert v.change_due == 20

    # Return change
    v.update()
    assert v.change_due == 0
    assert v.state.name == "waiting"


def test_return_button():

    v = VendingMachine()
    v.add_state(WaitingState())
    v.add_state(AddCoinsState())
    v.add_state(DeliverProductState())
    v.add_state(CountChangeState())
    v.go_to_state("waiting")

    # Insert $2 (toonie)
    v.event = "toonie"
    v.update()
    assert v.state.name == "add_coins"
    assert v.amount == 200

    # Press RETURN
    v.event = "RETURN"
    v.update()
    assert v.state.name == "count_change"
    assert v.change_due == 200

    # Machine returns coins
    v.update()
    assert v.change_due == 0
    assert v.state.name == "waiting"
