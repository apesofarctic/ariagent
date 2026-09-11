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


# Real-data (analyse-only) mode: nothing executes. Each tool becomes a prepared
# instruction + mock deep link the user completes in their own bank app.
_PREPARED = {
    "shift_debit_date": ("Instruction prepared: move the '{debit}' debit to after {to_after}. "
                         "Open your bank app to approve.", "bankapp://payments/mandates"),
    "cancel_subscription": ("Instruction prepared: cancel the mandate for {merchant}. "
                            "Open your bank app to approve.", "bankapp://payments/mandates"),
    "start_sip": ("Instruction prepared: set up a Rs{amount}/month SIP with your bank's "
                  "licensed partner. Open your bank app to review suitability and approve.",
                  "bankapp://invest/sip"),
    "open_goal": ("Instruction prepared: open a savings goal '{name}'. "
                  "Open your bank app to approve.", "bankapp://goals/new"),
    "noop": ("Nothing to do.", ""),
}


def prepare(tool: str, args: dict) -> tuple[str, str]:
    template, link = _PREPARED.get(tool, (f"Unknown tool {tool}", ""))
    try:
        return template.format(**args), link
    except KeyError:
        return template, link
