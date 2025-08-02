# Debug Plan: Phoenix API Issues

## Root Cause Analysis
**Problem**: Phoenix server running but API layer broken, preventing trace data access
**Impact**: Cannot access 20 stored traces (2.6GB database), monitoring completely broken
**Symptoms**: 
- Phoenix monitoring script times out after 5 seconds
- GraphQL queries fail with "unexpected error occurred"
- Server responds but API layer broken

## Solution Steps
1. **Server Health Check**
   - Verify Phoenix server process status
   - Test basic HTTP connectivity to localhost:6006
   - Check Phoenix server logs for errors

2. **API Endpoint Testing**
   - Test Phoenix web UI accessibility
   - Test GraphQL endpoint directly
   - Test different Phoenix client configurations

3. **Client Connection Testing**
   - Test basic Phoenix client instantiation
   - Try different timeout settings
   - Test direct database access if possible

4. **Database Investigation**
   - Check Phoenix database integrity
   - Verify database permissions
   - Check for corruption or locking issues

5. **Alternative Access Methods**
   - Try different Phoenix client versions
   - Test programmatic access alternatives
   - Check if Phoenix CLI tools work

## Risk Assessment
- **Low Risk**: Testing connections and reading logs
- **Medium Risk**: Modifying Phoenix client settings
- **High Risk**: Direct database manipulation (avoid unless necessary)

## Compliance Validation
- Ensure trace data integrity maintained
- Document all diagnostic steps for audit trail
- Preserve existing database during debugging

## Iteration Log
### Iteration 1: Root Cause Analysis - COMPLETED ✅
**Findings from comprehensive diagnostic (20250802_162308):**
- ✅ Phoenix server running (HTTP 200, version 11.10.1)
- ✅ GraphQL endpoint accessible (schema introspection works)
- ❌ **CRITICAL**: GraphQL data queries fail with "an unexpected error occurred"
- ✅ OTLP trace export successful (2 traces generated and exported)
- ❌ **CRITICAL**: Traces not retrievable via GraphQL despite successful export
- ✅ 2.6GB database exists but GraphQL cannot access data

**Root Cause Identified**: GraphQL API layer is broken - server accepts queries but data access fails

### Iteration 2: Comprehensive Fix Implementation - READY ✅
**Created targeted fix scripts:**
- `test_phoenix_client_bypass.py` - Direct client testing (bypasses GraphQL)
- `fix_phoenix_graphql_issue.py` - Multi-strategy automated fix
- `test_phoenix_connectivity.py` - Comprehensive connectivity testing

**Fix Strategies (in priority order):**
1. **Direct Phoenix Client Bypass** - Use `px.Client().get_spans_dataframe()` to bypass broken GraphQL
2. **Phoenix Server Restart** - Clean restart to clear GraphQL layer issues
3. **Database Reset with Backup** - Reset Phoenix DB while preserving data
4. **Alternative Launch Methods** - Try different Phoenix startup approaches
5. **Environment Reset** - Clean Phoenix environment variables

**Next Steps for User:**
1. Run `uv run python main/fix_phoenix_graphql_issue.py` to attempt automated fixes
2. If automated fixes fail, use manual instructions provided by the script
3. Use `uv run python main/test_phoenix_client_bypass.py` as workaround if needed

### Iteration 3: Post-Fix Validation
- Target: Verify trace data accessibility and monitoring script functionality