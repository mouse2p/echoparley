from echoparley.cascade import ScriptedCascade, compare_paths

cascade = ScriptedCascade(lambda _: "hello", lambda value: value.upper(), lambda _: "units")
result = cascade.run("synthetic-audio")
print(compare_paths(result, direct_delay_ms=220, direct_units=(1, 2, 3)))
