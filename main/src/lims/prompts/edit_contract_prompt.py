"""Edit contract documentation for the MDA chat agent.

Defines the MDAEditAction JSON schema that the LLM must use when
calling the `modify_mda` function tool. This prompt is included in the
tool definition so the LLM understands the structured edit format.

GAMP-5 Category 5: Custom pharmaceutical software component.
"""

EDIT_CONTRACT_PROMPT: str = """\
The `modify_mda` function accepts a single JSON argument representing
a structured edit action on the MDA template. The JSON must conform to
the MDAEditAction schema:

{
  "sheet": "<target sheet>",
  "action": "<edit action>",
  "target": { "<field>": "<value>", ... },
  "changes": { "<field>": <new_value>, ... },
  "reason": "<why this edit is needed>"
}

## Fields

### sheet (required, string)
Which MDA sheet to modify. Must be one of:
  - "analyses"        -- Sheet 1: top-level test method definitions
  - "components"      -- Sheet 2: individual test parameters
  - "calc_variables"  -- Sheet 6: variables for LIMS Basic calculations
  - "calculations"    -- Sheet 7: LIMS Basic calculation code

### action (required, string)
What operation to perform. Must be one of:
  - "add"     -- Add a new item to the sheet
  - "modify"  -- Modify an existing item on the sheet
  - "delete"  -- Remove an existing item from the sheet

### target (required, object)
Identifies which item to modify or delete. For "add" actions, this
contains the identifying fields of the new item.

Examples:
  - Analysis: {"name": "AND_ACS_DYE"}
  - Component: {"analysis": "AND_ACS_DYE", "component_name": "ABSORBANCE_595"}
  - CalcVariable: {"analysis": "AND_ACS_DYE", "component": "DYE_VOLUME", "name": "V_ABS"}
  - Calculation: {"analysis": "AND_ACS_DYE", "component": "DYE_VOLUME"}

### changes (optional, object)
The field values to set. For "add" actions, this is the full item data
(merged with target). For "modify" actions, only the fields that need
to change. For "delete" actions, this can be empty or omitted.

Examples:
  - Modify result_type: {"result_type": "K", "auto_calc": true}
  - Add component: {"order_number": 3, "result_type": "N", "uses_instrument": true}
  - Delete: {} (empty -- target identifies the item)

### reason (required, string)
A brief explanation of WHY this edit is needed. This is logged in the
audit trail for ALCOA+ compliance.

## Complete Examples

### Add a new component
{
  "sheet": "components",
  "action": "add",
  "target": {"analysis": "AND_ACS_DYE", "component_name": "NEW_MEASUREMENT"},
  "changes": {
    "order_number": 5,
    "result_type": "N",
    "uses_instrument": true,
    "instrument_group": "UV_VIS_SPEC",
    "units": "AU",
    "reportable": true
  },
  "reason": "Add absorbance measurement at new wavelength per reviewer request"
}

### Modify result type classification
{
  "sheet": "components",
  "action": "modify",
  "target": {"analysis": "AND_ACS_DYE_CTL", "component_name": "PETRI_DISH"},
  "changes": {
    "result_type": "K",
    "auto_calc": true,
    "list_key": null
  },
  "reason": "Petri Dish is equipment selection (INST_PICKER), not a list"
}

### Delete a component
{
  "sheet": "components",
  "action": "delete",
  "target": {"analysis": "AND_ACS_DYE", "component_name": "REDUNDANT_FIELD"},
  "changes": {},
  "reason": "Component duplicates information already captured in META analysis"
}

### Modify an analysis
{
  "sheet": "analyses",
  "action": "modify",
  "target": {"name": "AND_ACS_DYE"},
  "changes": {"description": "Updated description per lab review"},
  "reason": "Reviewer requested more specific description text"
}

## Validation Rules

After every edit, the entire MDA template is re-validated against the
Pydantic MDATemplate schema. If validation fails, the edit is rolled
back and an error message is returned. Common validation failures:

- K-type component without auto_calc=True
- L-type component without list_key
- Component referencing non-existent analysis
- K-type component without matching Calculation
- CalcVariable with reference_type=A but missing reference_analysis
- CTL/META analysis without QC_SAMPLES type

Always ensure your edits maintain cross-sheet integrity.
"""
