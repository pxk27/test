import m5
from m5.objects.ReplacementPolicies import (
    LRURP,
    SimObjectUnitTester,
)
from m5.objects.Root import Root

# , GoodByeSimObject


root = Root(full_system=False)
root.unit_tester = SimObjectUnitTester(num_entries=3)
root.unit_tester.replacement_policy = LRURP()
root.unit_tester.name = "LRU"
# root.unit_tester.goodbye_object = GoodByeSimObject()

m5.instantiate()
exit_event = m5.simulate()

print(f"Exited simulation because: {exit_event.getCause()}")
