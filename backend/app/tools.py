def shift_debit_date(debit, to_after, **_): return f"Scheduled '{debit}' to debit after {to_after}."
def cancel_subscription(merchant, **_):     return f"Cancelled subscription with {merchant}."
def start_sip(amount, **_):                 return f"Started SIP of Rs{amount}/month."
def open_goal(name, **_):                   return f"Opened goal '{name}'."
def noop(**_):                              return "No action."

TOOLS = {
    "shift_debit_date": shift_debit_date,
    "cancel_subscription": cancel_subscription,
    "start_sip": start_sip,
    "open_goal": open_goal,
    "noop": noop,
}


def execute(tool: str, args: dict) -> str:
    fn = TOOLS.get(tool)
    return fn(**args) if fn else f"Unknown tool {tool}"
