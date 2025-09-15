# Tests

This directory contains test scripts for the ShortFactory LangChain project.

## Test Files

### `test_script_generation.py`
Main test script that validates all core functionality:

- ✅ Environment setup (API keys)
- ✅ Module imports
- ✅ LLM initialization
- ✅ Prompt template creation
- ✅ Prompt formatting
- ✅ Simple LLM responses
- ✅ Video script generation
- ✅ File saving functionality
- ✅ Context clearing

### `run_tests.py`
Simple test runner script that executes all tests and provides exit codes.

## Running Tests

### Method 1: Direct execution
```bash
cd /path/to/ShortFactoryLangChain
source venv/bin/activate
python tests/test_script_generation.py
```

### Method 2: Using the test runner
```bash
cd /path/to/ShortFactoryLangChain
source venv/bin/activate
python tests/run_tests.py
```

### Method 3: Make it executable and run
```bash
cd /path/to/ShortFactoryLangChain
chmod +x tests/test_script_generation.py
./tests/test_script_generation.py
```

## Test Results

When all tests pass, you should see:
```
🎉 All tests passed! The system is working correctly.
Total: 9/9 tests passed
```

## Prerequisites

1. Virtual environment activated
2. `.env` file with `GEMINI_API_KEY` set
3. All dependencies installed (`pip install -r requirements.txt`)
4. Project installed in development mode (`pip install -e .`)

## Troubleshooting

### Common Issues

1. **ImportError**: Make sure the project is installed with `pip install -e .`
2. **API Key Error**: Check that `GEMINI_API_KEY` is set in `.env` file
3. **Module Not Found**: Ensure virtual environment is activated

### Test Output

The tests provide detailed output for each step:
- 🧪 Test name
- ✅ Success indicators
- ❌ Failure indicators
- 📄 Response previews
- 📊 Final summary

## Adding New Tests

To add new tests, follow the pattern:

```python
def test_your_new_feature():
    """Test description"""
    print("🧪 Testing your new feature...")
    
    try:
        # Your test code here
        result = your_function()
        
        if result:
            print("✅ Your test passed")
            return True
        else:
            print("❌ Your test failed")
            return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
```

Then add it to the `run_all_tests()` function.
