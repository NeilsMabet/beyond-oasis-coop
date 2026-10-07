"""Erase a wrongly predicted attack/jump and compare every serialized byte."""
import json
from probe import Core, ROOT
from verify import ROM, boot

c = Core(ROM)
c.capture = False
boot(c)
c.run(60)
checkpoint = c.state()
c.run(60)
expected = c.state()
c.restore(checkpoint)
c.run(8, [0], [8])
c.run(12)
c.restore(checkpoint)
c.run(60)
actual = c.state()
result = {'erased_attack_and_jump': actual == expected,
          'comparison': 'all serialized bytes, no pointer normalization'}
(ROOT / 'rollback-regression.json').write_text(json.dumps(result, indent=2))
print(result)
assert result['erased_attack_and_jump']
