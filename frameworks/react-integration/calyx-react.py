# AXIS_react.py  
"""React hooks generator for AXIS rules"""
import json

def generate_react_hook(yaml_path: str, hook_name: str = None) -> str:
    """Generate a React hook that uses AXIS rules"""
    
    engine = RuleEngine(yaml_path)
    component_name = engine.component_name
    
    if not hook_name:
        hook_name = f"use{component_name}"
    
    # Generate TypeScript hook code
    hook_code = f"""
import {{ useState, useCallback, useMemo }} from 'react';

// Generated AXIS React Hook for {component_name}
export function {hook_name}(initialState = {{}}) {{
  const [state, setState] = useState(initialState);
  
  // AXIS rules (would be loaded from server or bundled)
  const rules = {json.dumps(engine.rules, indent=2)};
  
  // Apply AXIS rules client-side
  const applyRules = useCallback((inputData, action = {{ type: 'RULE_CHECK' }}) => {{
    // This would call the actual AXIS engine
    // For now, simplified client-side version
    const newState = {{ ...inputData }};
    
    // Apply each rule
    rules.forEach(rule => {{
      if (rule.if) {{
        // Simplified condition evaluation (would use full AST in real version)
        const conditionMet = eval(rule.if.replace(/(\w+)/g, 'inputData.$1'));
        if (conditionMet && rule.then) {{
          Object.assign(newState, rule.then);
        }}
      }}
    }});
    
    return newState;
  }}, []);
  
  const updateState = useCallback((newData) => {{
    const result = applyRules(newData);
    setState(result);
    return result;
  }}, [applyRules]);
  
  const reset = useCallback(() => {{
    setState({{}});
  }}, []);
  
  return {{
    state,
    updateState,
    reset,
    applyRules,
    // Convenience getters
    errors: state.errors || [],
    isValid: !state.errors || state.errors.length === 0
  }};
}}

// Usage:
// const {{ state, updateState, errors }} = {hook_name}();
// updateState({{ age: 25, email: "test@example.com" }});
"""
    
    return hook_code

