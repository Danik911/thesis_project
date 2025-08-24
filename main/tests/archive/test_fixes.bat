@echo off
echo Testing Cross-Validation Fixes for GAMP-5 System
echo =================================================
echo.

REM Test 1: Check if URS-001 is now correctly categorized as Category 3
echo Test 1: GAMP Categorization Fix
echo --------------------------------
echo Testing URS-001 (Environmental Monitoring System) - Expected: Category 3
echo.

cd /d "C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main"

REM Use the URS-001 content from testing_data.md
echo Running categorization test...
python -c "
from src.agents.categorization.agent import categorize_urs_document

# URS-001 content (shortened for test)
urs_content = '''
Environmental Monitoring System to monitor critical storage areas for temperature-sensitive pharmaceutical products.
The system shall use vendor-supplied software without modification.
All data shall be stored in the vendor's standard database format.
Standard reports provided by vendor shall be used for batch release.
Electronic signatures shall use vendor's built-in functionality.
Data shall be retained for 7 years using vendor's archival feature.
'''

result = categorize_urs_document(
    urs_content=urs_content,
    document_name='URS-001-EMS-Test',
    verbose=True
)

print(f'\\n✅ CATEGORIZATION RESULT:')
print(f'   Category: {result.gamp_category.value}')
print(f'   Confidence: {result.confidence_score:.1%}')
print(f'   Expected: Category 3')
print(f'   Status: {\"PASS\" if result.gamp_category.value == 3 and result.confidence_score > 0.85 else \"FAIL\"}')
"

echo.
echo Test 2: Context Provider Callback Fix  
echo -------------------------------------
echo Testing embedding operations for cross-validation compatibility...
echo.

python -c "
import asyncio
from src.agents.parallel.context_provider import create_context_provider_agent

async def test_embedding():
    try:
        agent = create_context_provider_agent(verbose=True)
        print('✅ Context Provider Agent created successfully')
        print('✅ Embedding model initialized without callback conflicts')
        return True
    except Exception as e:
        print(f'❌ Context Provider test failed: {e}')
        return False

result = asyncio.run(test_embedding())
print(f'Status: {\"PASS\" if result else \"FAIL\"}')
"

echo.
echo Test 3: Phoenix Connectivity
echo ----------------------------
echo Checking if Phoenix UI is accessible...

curl -f http://localhost:6006 >nul 2>&1
if errorlevel 1 (
    echo ❌ Phoenix UI not accessible at http://localhost:6006
    echo 💡 Run launch_phoenix.bat to start Phoenix server
    echo Status: FAIL
) else (
    echo ✅ Phoenix UI accessible at http://localhost:6006
    echo Status: PASS
)

echo.
echo =================================================
echo Cross-validation fix testing complete!
echo.
echo Next steps:
echo 1. If all tests PASS, run full cross-validation test
echo 2. If categorization FAIL, check pattern matching logs
echo 3. If Phoenix FAIL, run launch_phoenix.bat first
echo.
pause