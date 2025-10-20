"""
Quick test script for Table Parser
Run with: python test_table_parser.py
"""
import sys
sys.path.insert(0, '/app')

from app.services.table_parser import TableParser

def test_capital_call_table():
    """Test parsing a capital call table"""
    print("\n" + "="*60)
    print("TEST 1: Capital Call Table")
    print("="*60)
    
    # Sample capital call table
    table_data = [
        ["Date", "Call Number", "Amount", "Description"],
        ["2023-01-15", "Call 1", "$5,000,000", "Initial Capital"],
        ["2023-06-20", "Call 2", "$3,000,000", "Follow-on Investment"],
        ["2024-03-10", "Call 3", "$2,000,000", "Bridge Round"]
    ]
    
    parser = TableParser()
    
    # Classify table
    table_type = parser.classify_table(table_data)
    print(f"\n✓ Table Type: {table_type}")
    
    # Parse table
    result = parser.parse_table(table_data)
    print(f"✓ Parsed {result['row_count']} rows")
    print(f"\nHeaders: {result['headers']}")
    print(f"\nParsed Rows:")
    for i, row in enumerate(result['rows'], 1):
        print(f"  {i}. Date: {row['call_date']}, Amount: ${row['amount']:,}, Type: {row['call_type']}")
    
    return result['type'] == 'capital_call' and result['row_count'] == 3


def test_distribution_table():
    """Test parsing a distribution table"""
    print("\n" + "="*60)
    print("TEST 2: Distribution Table")
    print("="*60)
    
    # Sample distribution table
    table_data = [
        ["Date", "Type", "Amount", "Recallable", "Description"],
        ["2023-12-15", "Return of Capital", "$1,500,000", "No", "Exit from Company A"],
        ["2024-06-20", "Income", "$500,000", "No", "Dividend Payment"],
        ["2024-09-10", "Return", "$2,000,000", "Yes", "Partial Exit from Company B"]
    ]
    
    parser = TableParser()
    
    # Classify table
    table_type = parser.classify_table(table_data)
    print(f"\n✓ Table Type: {table_type}")
    
    # Parse table
    result = parser.parse_table(table_data)
    print(f"✓ Parsed {result['row_count']} rows")
    print(f"\nHeaders: {result['headers']}")
    print(f"\nParsed Rows:")
    for i, row in enumerate(result['rows'], 1):
        recallable = "Yes" if row['is_recallable'] else "No"
        print(f"  {i}. Date: {row['distribution_date']}, Amount: ${row['amount']:,}, Recallable: {recallable}")
    
    return result['type'] == 'distribution' and result['row_count'] == 3


def test_adjustment_table():
    """Test parsing an adjustment table"""
    print("\n" + "="*60)
    print("TEST 3: Adjustment Table")
    print("="*60)
    
    # Sample adjustment table
    table_data = [
        ["Date", "Type", "Amount", "Description"],
        ["2024-01-15", "Recallable Distribution", "-$500,000", "Recalled distribution from Q4"],
        ["2024-03-20", "Capital Call Adjustment", "$100,000", "Fee adjustment"]
    ]
    
    parser = TableParser()
    
    # Classify table
    table_type = parser.classify_table(table_data)
    print(f"\n✓ Table Type: {table_type}")
    
    # Parse table
    result = parser.parse_table(table_data)
    print(f"✓ Parsed {result['row_count']} rows")
    print(f"\nHeaders: {result['headers']}")
    print(f"\nParsed Rows:")
    for i, row in enumerate(result['rows'], 1):
        print(f"  {i}. Date: {row['adjustment_date']}, Amount: ${row['amount']:,}, Type: {row['adjustment_type']}")
    
    return result['type'] == 'adjustment' and result['row_count'] == 2


def test_date_parsing():
    """Test various date formats"""
    print("\n" + "="*60)
    print("TEST 4: Date Format Parsing")
    print("="*60)
    
    parser = TableParser()
    
    test_dates = [
        ("2024-01-15", "2024-01-15"),
        ("01/15/2024", "2024-01-15"),
        ("15-01-2024", "2024-01-15"),
        ("2024/01/15", "2024-01-15"),
    ]
    
    all_passed = True
    for input_date, expected in test_dates:
        result = parser._parse_date(input_date)
        passed = result == expected
        status = "✓" if passed else "✗"
        print(f"{status} {input_date} -> {result} (expected: {expected})")
        all_passed = all_passed and passed
    
    return all_passed


def test_amount_parsing():
    """Test various amount formats"""
    print("\n" + "="*60)
    print("TEST 5: Amount Format Parsing")
    print("="*60)
    
    parser = TableParser()
    
    test_amounts = [
        ("$5,000,000", 5000000),
        ("5000000", 5000000),
        ("$5,000,000.00", 5000000),
        ("($500,000)", -500000),  # Negative in parentheses
        ("5.5M", None),  # Should not parse abbreviated forms
    ]
    
    all_passed = True
    for input_amount, expected in test_amounts:
        result = parser._parse_amount(input_amount)
        if expected is None:
            passed = result is None
        else:
            passed = result == expected
        status = "✓" if passed else "✗"
        print(f"{status} {input_amount} -> {result} (expected: {expected})")
        all_passed = all_passed and passed
    
    return all_passed


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TABLE PARSER TEST SUITE")
    print("="*60)
    
    tests = [
        ("Capital Call Table", test_capital_call_table),
        ("Distribution Table", test_distribution_table),
        ("Adjustment Table", test_adjustment_table),
        ("Date Parsing", test_date_parsing),
        ("Amount Parsing", test_amount_parsing),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
