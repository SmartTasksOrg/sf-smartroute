// Flowise custom node for SmartRoute (IAIso governance).
// Copy this folder into Flowise's components/nodes/ (or load as a custom tool).
// It shells out to the shipped adapter.py, so smartroute must be importable
// (install SmartRoute from a clone: python -m pip install . ; it is not on PyPI yet)
// or PYTHONPATH set to the repo src/.
const path = require('path');
const { spawnSync } = require('child_process');

class SmartRoute_Node {
  constructor() {
    this.label = 'SmartRoute';
    this.name = 'smartroute_gate';
    this.version = 1.0;
    this.type = 'SmartRoute';
    this.category = 'SmartTasks / IAIso Governance';
    this.description = "Gate one agent tool-access request: return an allow/block decision with a 0..1 trust score and the ROUTE-* signals that moved it.";
    this.baseClasses = [this.type, 'Tool'];
    this.inputs = [
      { label: 'Input (request)', name: 'input', type: 'string' },
      { label: 'Python', name: 'python', type: 'string', default: 'python3', optional: true },
    ];
  }

  async init(nodeData) {
    const input = (nodeData.inputs && nodeData.inputs.input) || '';
    const py = (nodeData.inputs && nodeData.inputs.python) || 'python3';
    const adapter = path.join(__dirname, '..', 'adapter.py');
    const res = spawnSync(py, [adapter, '--file', input], { encoding: 'utf8' });
    if (res.status !== 0) throw new Error(res.stderr || 'SmartRoute adapter failed');
    return JSON.parse(res.stdout);
  }
}

module.exports = { nodeClass: SmartRoute_Node };
