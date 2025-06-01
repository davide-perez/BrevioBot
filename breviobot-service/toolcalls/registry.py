TOOL_REGISTRY = {}

def register_tool(name):
    def decorator(func):
        TOOL_REGISTRY[name] = func
        return func
    return decorator

# Esempio di funzione da registrare (da implementare altrove)
# @register_tool("get_google_calendar_events")
# def get_google_calendar_events(start_date: str, end_date: str):
#     ...

def dispatch_tool_call(tool_name, parameters):
    func = TOOL_REGISTRY.get(tool_name)
    if not func:
        raise ValueError(f"Tool '{tool_name}' non supportato")
    return func(**parameters)
