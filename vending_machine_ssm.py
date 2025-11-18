"""
TPRG2131 – Project 1 – Vending Machine
Student: Sachkerat Singh Matharoo
ID: 100996938
Date -17-11-2025
File: vending_machine_ssm.py
"""

import FreeSimpleGUI as sg
from time import sleep

# Raspberry Pi Hardware Detection

hardware_present = False
try:
    from gpiozero import Button, Servo
    servo = Servo(17)      # GPIO 17 = servo output
    key1 = Button(5)       # GPIO 5 = RETURN physical button
    hardware_present = True
except ModuleNotFoundError:
    print("Running in software-only mode or Pi hardware unavailable.")

TESTING = False
def log(s):
    if TESTING:
        print(s)

#VENDING MACHINE CLASS

class VendingMachine(object):
    """
    Main vending machine controller.
    Handles:
    - state transitions
    - coin tracking
    - product prices
    """

    # Product:  name label, price (in cents)
    PRODUCTS = {
        "chips": ("CHIPS", 150),
        "gum": ("GUM", 25),
        "drink": ("DRINK", 200),
        "candy": ("CANDY", 100),
        "surprise": ("SURPRISE", 50)
    }

    # Coin name: label, value (in cents)
    COINS = {
        "5": ("5¢", 5),
        "10": ("10¢", 10),
        "25": ("25¢", 25),
        "loonie": ("$1.00", 100),
        "toonie": ("$2.00", 200)
    }

    def __init__(self):
        self.state = None
        self.states = {}
        self.event = ""
        self.amount = 0          # amount user has inserted
        self.change_due = 0      # change to return

        # Sorted coin values (largest to smallest)
        vals = [v[1] for v in self.COINS.values()]
        self.coin_values = sorted(vals, reverse=True)

    # Add a state object into the machine
    def add_state(self, state):
        self.states[state.name] = state

    # Jump to another state
    def go_to_state(self, state_name):
        if self.state:
            self.state.on_exit(self)
        self.state = self.states[state_name]
        self.state.on_entry(self)

    # Update current state logic
    def update(self):
        if self.state:
            self.state.update(self)

    # Add a coin value
    def add_coin(self, c):
        self.amount += self.COINS[c][1]

    # Raspberry Pi physical button
    def button_action(self):
        self.event = "RETURN"
        self.update()

    # OPTIONAL CHALLENGE:
    # Update GUI Text showing the amount
    def update_gui_amount(self, window):
        window["-AMOUNT-"].update(f"Amount Inserted: ${self.amount/100:.2f}")

#                       BASE STATE CLASS
class State(object):
    _NAME = ""
    @property
    def name(self):
        return self._NAME
    def on_entry(self, machine): pass
    def on_exit(self, machine): pass
    def update(self, machine): pass

#                      STATE: WAITING
class WaitingState(State):
    _NAME = "waiting"

    def on_entry(self, machine):
        # Reset amounts whenever entering waiting state
        machine.amount = 0
        machine.change_due = 0

    def update(self, machine):
        # If a coin is inserted → go to add_coins state
        if machine.event in machine.COINS:
            machine.add_coin(machine.event)
            machine.go_to_state("add_coins")

#                    STATE: ADD COINS
class AddCoinsState(State):
    _NAME = "add_coins"

    def update(self, machine):

        # RETURN pressed → give back all coins
        if machine.event == "RETURN":
            machine.change_due = machine.amount
            machine.amount = 0
            machine.go_to_state("count_change")

        # Add additional coin
        elif machine.event in machine.COINS:
            machine.add_coin(machine.event)

        # Select a product
        elif machine.event in machine.PRODUCTS:
            price = machine.PRODUCTS[machine.event][1]

            # If enough money inserted → deliver
            if machine.amount >= price:
                machine.go_to_state("deliver_product")

        # Ignore other events
        else:
            pass

#                  STATE: DELIVER PRODUCT

class DeliverProductState(State):
    _NAME = "deliver_product"

    def on_entry(self, machine):

        price = machine.PRODUCTS[machine.event][1]

        # Calculate change
        machine.change_due = machine.amount - price
        machine.amount = 0

        print("Dispensing:", machine.PRODUCTS[machine.event][0])

        # Move servo only on Raspberry Pi
        if hardware_present:
            servo.mid()
            sleep(0.4)
            servo.min()
            sleep(0.4)
            servo.max()
            sleep(0.4)

        # After product delivery, return change or reset
        if machine.change_due > 0:
            machine.go_to_state("count_change")
        else:
            machine.go_to_state("waiting")

#                     STATE: COUNT CHANGE
class CountChangeState(State):
    _NAME = "count_change"

    def on_entry(self, machine):
        print(f"Change due: {machine.change_due} cents")

    def update(self, machine):
        # Return coins from largest → smallest
        for coin in machine.coin_values:
            while machine.change_due >= coin:
                print(f"Returning {coin}¢")
                machine.change_due -= coin

        # When done → return to waiting
        if machine.change_due == 0:
            machine.go_to_state("waiting")

#                         MAIN PROGRAM
if __name__ == "__main__":

    sg.theme("BluePurple")

    # GUI element that shows total amount inserted
    amount_display = sg.Text("Amount Inserted: $0.00",
                             font=("Helvetica", 20),
                             key="-AMOUNT-")

    # Build COIN panel
    coin_col = [
        [sg.Text("ENTER COINS", font=("Helvetica", 24))],
        [amount_display]
    ]
    for c in VendingMachine.COINS:
        coin_col.append([sg.Button(c, font=("Helvetica", 18))])

    # Build PRODUCT panel with PRICES
    prod_col = [
        [sg.Text("SELECT ITEM", font=("Helvetica", 24))]
    ]
    for key, item in VendingMachine.PRODUCTS.items():
        label = f"{item[0]} — ${item[1]/100:.2f}"
        prod_col.append([
            sg.Button(key, font=("Helvetica", 18)),
            sg.Text(label, font=("Helvetica", 16))
        ])

    layout = [
        [sg.Column(coin_col), sg.VSeparator(), sg.Column(prod_col)],
        [sg.Button("RETURN", font=("Helvetica", 12))]
    ]

    window = sg.Window("Vending Machine", layout)

    # Initialize machine + states
    vending = VendingMachine()
    vending.add_state(WaitingState())
    vending.add_state(AddCoinsState())
    vending.add_state(DeliverProductState())
    vending.add_state(CountChangeState())
    vending.go_to_state("waiting")

    # Pi hardware button → RETURN
    if hardware_present:
        key1.when_pressed = vending.button_action

    # MAIN EVENT LOOP
    while True:
        event, values = window.read(timeout=10)

        if event in (sg.WIN_CLOSED, "Exit"):
            break

        # Pass event into state machine
        vending.event = event
        vending.update()

        # Update GUI amount display (optional challenge feature)
        vending.update_gui_amount(window)

    window.close()
    print("Normal exit")
