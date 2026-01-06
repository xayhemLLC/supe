# MCP Integration with Supe

## What is MCP?

**Model Context Protocol (MCP)** is Anthropic's standard for connecting Claude to external tools and data sources. It enables:
- External tool access
- Real-time data fetching
- Custom integrations
- Persistent connections

## How MCP Fits with Supe

### Current Supe Architecture
```
Supe (Reasoning System)
├── Problem Classification
├── Capability Registry
├── Strategy Synthesis
├── Execution Engine
└── Learning Loop
```

### With MCP Integration
```
Supe (Reasoning System)
├── Problem Classification
├── Capability Registry
│   ├── Built-in (algebraic, pattern, etc.)
│   └── MCP Tools (via protocol)  ← NEW
├── Strategy Synthesis
├── Execution Engine
│   └── MCP Tool Executor  ← NEW
└── Learning Loop
```

## MCP as Capability Provider

### Concept: MCP Tools as Reasoning Capabilities

Instead of hardcoding all reasoning capabilities, expose them via MCP:

```python
# Example: MCP-provided calculator capability
{
  "name": "calculator",
  "description": "Perform arithmetic operations",
  "input_schema": {
    "expression": "string"
  }
}

# Supe treats this as a reasoning capability:
calculator_capability = ReasoningCapability(
    name="calculator",
    pattern=ReasoningPattern.ARITHMETIC,
    domains={ProblemDomain.ALGEBRA},
    implementation=MCPToolWrapper("calculator"),
    confidence=1.0
)
```

### Benefits

1. **Extensibility**: Add new capabilities without modifying supe
2. **Specialization**: External tools for specific domains
3. **Real-time Data**: Access live data sources
4. **Tool Ecosystem**: Leverage existing MCP tools

## Implementation Approaches

### Approach 1: MCP Tools as Capabilities

**Wrap MCP tools as reasoning capabilities**:

```python
class MCPToolWrapper:
    """Wraps an MCP tool as a reasoning capability."""

    def __init__(self, tool_name: str, mcp_client):
        self.tool_name = tool_name
        self.client = mcp_client

    def execute(self, problem_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP tool."""
        # Prepare tool input from problem and context
        tool_input = self._prepare_input(problem_text, context)

        # Call MCP tool
        result = self.client.call_tool(self.tool_name, tool_input)

        # Format result
        return {
            "success": True,
            "result": result,
            "source": "mcp_tool",
        }
```

### Approach 2: MCP for External Knowledge

**Use MCP to fetch knowledge during reasoning**:

```python
class MCPKnowledgeProvider:
    """Fetch external knowledge via MCP."""

    def __init__(self, mcp_client):
        self.client = mcp_client

    def query_knowledge(self, query: str) -> str:
        """Query external knowledge base."""
        return self.client.call_tool("knowledge_search", {"query": query})

# In algebraic capability:
def execute(self, problem_text: str, context: Dict[str, Any]):
    # Check if we need external knowledge
    if self._is_advanced_problem(problem_text):
        # Query MCP for mathematical knowledge
        knowledge = mcp_provider.query_knowledge(
            f"How to solve {problem_text}"
        )
        # Use knowledge to guide solving
```

### Approach 3: MCP for Validation

**Use MCP tools to validate reasoning results**:

```python
class MCPValidator:
    """Validate reasoning results using external tools."""

    def validate_algebraic_result(self, expression: str, result: str) -> bool:
        """Use external CAS to verify."""
        # Call MCP symbolic math tool
        verification = mcp_client.call_tool("sympy_verify", {
            "expression": expression,
            "claimed_result": result
        })
        return verification["is_correct"]
```

## Practical Use Cases

### 1. Mathematical Computation

**Current**: Supe implements basic factorization
**With MCP**: Access SymPy, Wolfram Alpha, etc.

```python
# MCP tool: sympy_server
{
  "name": "sympy_factor",
  "description": "Factor polynomial using SymPy",
  "input_schema": {
    "polynomial": "string"
  }
}

# Supe uses it as fallback:
def factor_polynomial(self, poly: str):
    # Try built-in factorization
    result = self._factor_quadratic(poly)

    if not result["success"]:
        # Fallback to MCP tool
        result = mcp_client.call_tool("sympy_factor", {"polynomial": poly})

    return result
```

### 2. Real-World Data

**Use Case**: Reasoning about current events, prices, weather

```python
# Problem: "What's the best route from SF to LA today?"
# Supe needs real-time traffic data

traffic_data = mcp_client.call_tool("google_maps", {
    "from": "SF",
    "to": "LA"
})

# Use in reasoning
route = spatial_reasoner.find_optimal_route(
    start="SF",
    end="LA",
    traffic=traffic_data
)
```

### 3. Document Analysis

**Use Case**: Reason about documents, codebases

```python
# Problem: "What does the authentication module do?"

code_context = mcp_client.call_tool("codebase_search", {
    "query": "authentication"
})

# Reason about the code
analysis = code_reasoner.analyze_module(code_context)
```

### 4. Domain Expertise

**Use Case**: Access specialized knowledge

```python
# Problem: "Is this chemical reaction possible?"

chemistry_knowledge = mcp_client.call_tool("pubchem_query", {
    "query": "reaction feasibility",
    "reactants": ["H2", "O2"]
})

# Reason with domain knowledge
feasibility = domain_reasoner.check_feasibility(chemistry_knowledge)
```

## Architecture Design

### MCPCapabilityProvider

```python
class MCPCapabilityProvider:
    """Provides reasoning capabilities via MCP."""

    def __init__(self, mcp_client):
        self.client = mcp_client
        self.available_tools = {}
        self._discover_tools()

    def _discover_tools(self):
        """Discover available MCP tools."""
        tools = self.client.list_tools()

        for tool in tools:
            # Map tool to reasoning capability
            capability = self._tool_to_capability(tool)
            if capability:
                self.available_tools[tool["name"]] = capability

    def _tool_to_capability(self, tool: Dict) -> Optional[ReasoningCapability]:
        """Convert MCP tool to reasoning capability."""
        # Infer reasoning pattern from tool description
        pattern = self._infer_pattern(tool["description"])

        if pattern:
            return ReasoningCapability(
                name=tool["name"],
                pattern=pattern,
                domains={ProblemDomain.UNKNOWN},  # Could be inferred
                description=tool["description"],
                implementation=MCPToolWrapper(tool["name"], self.client),
            )

        return None

    def _infer_pattern(self, description: str) -> Optional[ReasoningPattern]:
        """Infer reasoning pattern from tool description."""
        # Simple keyword matching
        if "calculate" in description or "compute" in description:
            return ReasoningPattern.ARITHMETIC
        elif "search" in description or "find" in description:
            return ReasoningPattern.SYSTEMATIC_SEARCH
        # ... more mappings

        return None
```

### Integration with Meta-Solver

```python
class MetaSolver:
    def __init__(self, memory: ABMemory, mcp_client=None):
        self.memory = memory
        self.registry = CapabilityRegistry()
        self.learning_loop = LearningLoop(memory)

        # NEW: MCP integration
        if mcp_client:
            self.mcp_provider = MCPCapabilityProvider(mcp_client)
            self._register_mcp_capabilities()

    def _register_mcp_capabilities(self):
        """Register MCP tools as capabilities."""
        for tool_name, capability in self.mcp_provider.available_tools.items():
            self.registry.register(capability)
            print(f"Registered MCP tool: {tool_name}")
```

## Example: ARC-AGI with MCP

For ARC-AGI, MCP could provide:

1. **Image Processing Tools**
   ```python
   # MCP tool: opencv_server
   grid_objects = mcp_client.call_tool("detect_contours", {
       "image": arc_grid_as_image
   })
   ```

2. **Symbolic Reasoning**
   ```python
   # MCP tool: z3_solver
   solution = mcp_client.call_tool("solve_constraints", {
       "constraints": grid_constraints
   })
   ```

3. **Pattern Libraries**
   ```python
   # MCP tool: pattern_database
   similar_patterns = mcp_client.call_tool("find_similar", {
       "pattern": detected_pattern
   })
   ```

## Implementation Steps

### Step 1: Basic MCP Client
```python
# mcp_client.py
class MCPClient:
    """Basic MCP client for tool calls."""

    def __init__(self, server_url: str):
        self.server_url = server_url

    def list_tools(self) -> List[Dict]:
        """Get available tools."""
        pass

    def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Call an MCP tool."""
        pass
```

### Step 2: Capability Wrapper
```python
# mcp_wrapper.py
class MCPToolWrapper:
    """Wraps MCP tool as capability implementation."""
    # (Code shown above)
```

### Step 3: Provider Integration
```python
# capability_registry.py
class CapabilityRegistry:
    def __init__(self, mcp_client=None):
        # ... existing code ...

        if mcp_client:
            self.mcp_provider = MCPCapabilityProvider(mcp_client)
            self._load_mcp_capabilities()
```

### Step 4: Testing
```python
# Test with simple MCP tool
def test_mcp_integration():
    # Start MCP server (e.g., calculator)
    mcp_client = MCPClient("http://localhost:8080")

    # Initialize solver with MCP
    solver = MetaSolver(memory, mcp_client=mcp_client)

    # Solve problem using MCP tool
    result = solver.solve("Calculate 12345 * 67890")

    assert result["success"]
    assert "mcp_tool" in result["source"]
```

## Benefits for Supe

1. **Extensibility**: Add capabilities without code changes
2. **Specialization**: Use best-in-class tools for each domain
3. **Real-time**: Access live data and services
4. **Collaboration**: Multiple systems contribute capabilities
5. **Learning**: System learns which tools work best

## Challenges

1. **Latency**: MCP calls slower than local computation
2. **Reliability**: Depends on external services
3. **Security**: Must validate external tool outputs
4. **Cost**: Some MCP tools may have usage costs

## Conclusion

MCP integration transforms supe from a closed system to an open ecosystem:
- Built-in capabilities for core reasoning
- MCP capabilities for specialized tasks
- Best of both worlds: speed + extensibility

This positions supe as a **reasoning orchestrator** that can leverage any tool in the MCP ecosystem.
