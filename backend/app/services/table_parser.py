"""
Table parsing service for extracting and classifying tables from PDFs
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
import re


class TableParser:
    """Parse and classify tables extracted from PDF documents"""
    
    # Keywords for table classification
    CAPITAL_CALL_KEYWORDS = [
        'capital call', 'call', 'contribution', 'drawdown', 'commitment',
        'called', 'funding', 'capital contributions'
    ]
    
    DISTRIBUTION_KEYWORDS = [
        'distribution', 'return', 'dividend', 'payment', 'proceeds',
        'distributions', 'paid out', 'returned'
    ]
    
    ADJUSTMENT_KEYWORDS = [
        'adjustment', 'rebalance', 'correction', 'recallable', 'clawback',
        'adjustments', 'reconciliation', 'true-up'
    ]
    
    def __init__(self):
        """Initialize the table parser"""
        pass
    
    def parse_table(self, table_data: List[List[str]], table_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse a table and extract structured data
        
        Args:
            table_data: Raw table data as list of lists
            table_type: Optional pre-classified table type
            
        Returns:
            Parsed and structured table data with type and rows
        """
        if not table_data or len(table_data) < 2:
            return {
                "type": "unknown",
                "rows": [],
                "headers": [],
                "error": "Table has insufficient data"
            }
        
        # Classify table type if not provided
        if not table_type:
            table_type = self.classify_table(table_data)
        
        # Extract headers (first row)
        headers = self._normalize_headers(table_data[0])
        
        # Parse rows based on table type
        parsed_rows = []
        for row_data in table_data[1:]:
            if self._is_empty_row(row_data):
                continue
                
            try:
                if table_type == "capital_call":
                    parsed_row = self._parse_capital_call_row(row_data, headers)
                elif table_type == "distribution":
                    parsed_row = self._parse_distribution_row(row_data, headers)
                elif table_type == "adjustment":
                    parsed_row = self._parse_adjustment_row(row_data, headers)
                else:
                    parsed_row = self._parse_generic_row(row_data, headers)
                
                if parsed_row:
                    parsed_rows.append(parsed_row)
            except Exception as e:
                print(f"Error parsing row {row_data}: {e}")
                continue
        
        return {
            "type": table_type,
            "headers": headers,
            "rows": parsed_rows,
            "row_count": len(parsed_rows)
        }
    
    def classify_table(self, table_data: List[List[str]]) -> str:
        """
        Classify the type of table by analyzing headers and content
        
        Args:
            table_data: Raw table data as list of lists
            
        Returns:
            Table type: 'capital_call', 'distribution', 'adjustment', or 'unknown'
        """
        if not table_data:
            return "unknown"
        
        # Combine first few rows for analysis (headers + some data)
        analysis_text = " ".join([
            " ".join([str(cell).lower() for cell in row if cell])
            for row in table_data[:3]
        ])
        
        # Adjustments have priority - check first
        # Weight adjustment keywords higher to prevent misclassification
        adjustment_score = sum(
            2 for keyword in self.ADJUSTMENT_KEYWORDS 
            if keyword in analysis_text
        )
        
        # Count keyword matches with standard weight
        capital_call_score = sum(
            1 for keyword in self.CAPITAL_CALL_KEYWORDS 
            if keyword in analysis_text
        )
        
        distribution_score = sum(
            1 for keyword in self.DISTRIBUTION_KEYWORDS 
            if keyword in analysis_text
        )
        
        # Determine table type based on highest score
        scores = {
            "adjustment": adjustment_score,
            "distribution": distribution_score,
            "capital_call": capital_call_score,
        }
        
        max_score = max(scores.values())
        
        if max_score == 0:
            return "unknown"
        
        # Return the type with highest score (adjustment checked first due to ordering)
        for table_type, score in scores.items():
            if score == max_score:
                return table_type
        
        return "unknown"
    
    def _normalize_headers(self, headers: List[str]) -> List[str]:
        """Normalize header names for consistent processing"""
        return [str(h).lower().strip() if h else "" for h in headers]
    
    def _is_empty_row(self, row: List[str]) -> bool:
        """Check if a row is empty or contains only whitespace"""
        return not any(str(cell).strip() for cell in row if cell)
    
    def _parse_capital_call_row(self, row: List[str], headers: List[str]) -> Optional[Dict[str, Any]]:
        """Parse a capital call table row"""
        # Try to extract date, amount, and description
        date_val = self._extract_date(row, headers)
        amount_val = self._extract_amount(row, headers)
        description = self._extract_description(row, headers)
        call_type = self._extract_call_type(row, headers)
        
        if not date_val or not amount_val:
            return None
        
        return {
            "call_date": date_val,
            "amount": amount_val,
            "call_type": call_type or "Regular Capital Call",
            "description": description
        }
    
    def _parse_distribution_row(self, row: List[str], headers: List[str]) -> Optional[Dict[str, Any]]:
        """Parse a distribution table row"""
        date_val = self._extract_date(row, headers)
        amount_val = self._extract_amount(row, headers)
        description = self._extract_description(row, headers)
        dist_type = self._extract_distribution_type(row, headers)
        is_recallable = self._extract_recallable_flag(row, headers)
        
        if not date_val or not amount_val:
            return None
        
        return {
            "distribution_date": date_val,
            "amount": amount_val,
            "distribution_type": dist_type or "Distribution",
            "is_recallable": is_recallable,
            "description": description
        }
    
    def _parse_adjustment_row(self, row: List[str], headers: List[str]) -> Optional[Dict[str, Any]]:
        """Parse an adjustment table row"""
        date_val = self._extract_date(row, headers)
        amount_val = self._extract_amount(row, headers)
        description = self._extract_description(row, headers)
        adj_type = self._extract_adjustment_type(row, headers)
        category = self._extract_category(row, headers)
        
        if not date_val or not amount_val:
            return None
        
        # Check if this is a contribution adjustment
        is_contribution = any(
            keyword in description.lower() 
            for keyword in ['contribution', 'capital call', 'call']
        ) if description else False
        
        return {
            "adjustment_date": date_val,
            "amount": amount_val,
            "adjustment_type": adj_type or "Adjustment",
            "category": category or "General",
            "is_contribution_adjustment": is_contribution,
            "description": description
        }
    
    def _parse_generic_row(self, row: List[str], headers: List[str]) -> Dict[str, Any]:
        """Parse a generic table row when type is unknown"""
        return {header: self._clean_cell_value(cell) for header, cell in zip(headers, row)}
    
    def _extract_date(self, row: List[str], headers: List[str]) -> Optional[str]:
        """Extract date from a table row"""
        date_keywords = ['date', 'dated', 'when', 'period', 'year', 'month']
        
        # Look for date column
        for i, header in enumerate(headers):
            if any(keyword in header for keyword in date_keywords):
                if i < len(row):
                    parsed_date = self._parse_date(row[i])
                    if parsed_date:
                        return parsed_date
        
        # If no header match, try to find date pattern in first few columns
        for cell in row[:3]:
            parsed_date = self._parse_date(cell)
            if parsed_date:
                return parsed_date
        
        return None
    
    def _extract_amount(self, row: List[str], headers: List[str]) -> Optional[Decimal]:
        """Extract amount from a table row"""
        amount_keywords = ['amount', 'value', 'sum', 'total', '$', 'usd', 'price']
        
        # Look for amount column
        for i, header in enumerate(headers):
            if any(keyword in header for keyword in amount_keywords):
                if i < len(row):
                    parsed_amount = self._parse_amount(row[i])
                    if parsed_amount:
                        return parsed_amount
        
        # If no header match, try to find amount pattern in all columns
        for cell in row:
            parsed_amount = self._parse_amount(cell)
            if parsed_amount:
                return parsed_amount
        
        return None
    
    def _extract_description(self, row: List[str], headers: List[str]) -> str:
        """Extract description from a table row"""
        desc_keywords = ['description', 'note', 'memo', 'comment', 'detail', 'purpose']
        
        # Look for description column
        for i, header in enumerate(headers):
            if any(keyword in header for keyword in desc_keywords):
                if i < len(row) and row[i]:
                    return str(row[i]).strip()
        
        # Return the longest text field as description
        longest = ""
        for cell in row:
            if cell and len(str(cell)) > len(longest) and not self._parse_amount(cell) and not self._parse_date(cell):
                longest = str(cell).strip()
        
        return longest
    
    def _extract_call_type(self, row: List[str], headers: List[str]) -> Optional[str]:
        """Extract capital call type"""
        type_keywords = ['type', 'category', 'kind', 'class']
        
        for i, header in enumerate(headers):
            if any(keyword in header for keyword in type_keywords):
                if i < len(row) and row[i]:
                    return str(row[i]).strip()
        
        return None
    
    def _extract_distribution_type(self, row: List[str], headers: List[str]) -> Optional[str]:
        """Extract distribution type"""
        type_keywords = ['type', 'category', 'kind', 'class']
        
        for i, header in enumerate(headers):
            if any(keyword in header for keyword in type_keywords):
                if i < len(row) and row[i]:
                    return str(row[i]).strip()
        
        return None
    
    def _extract_adjustment_type(self, row: List[str], headers: List[str]) -> Optional[str]:
        """Extract adjustment type"""
        type_keywords = ['type', 'category', 'kind', 'class']
        
        for i, header in enumerate(headers):
            if any(keyword in header for keyword in type_keywords):
                if i < len(row) and row[i]:
                    return str(row[i]).strip()
        
        return None
    
    def _extract_category(self, row: List[str], headers: List[str]) -> Optional[str]:
        """Extract category from adjustment row"""
        cat_keywords = ['category', 'classification']
        
        for i, header in enumerate(headers):
            if any(keyword in header for keyword in cat_keywords):
                if i < len(row) and row[i]:
                    return str(row[i]).strip()
        
        return None
    
    def _extract_recallable_flag(self, row: List[str], headers: List[str]) -> bool:
        """Extract recallable flag from distribution row"""
        recallable_keywords = ['recallable', 'recall', 'clawback']
        
        # Check headers
        for i, header in enumerate(headers):
            if any(keyword in header for keyword in recallable_keywords):
                if i < len(row):
                    cell_value = str(row[i]).lower().strip()
                    return cell_value in ['yes', 'true', '1', 'y', 't']
        
        # Check all cells for recallable indicator
        for cell in row:
            cell_str = str(cell).lower()
            if 'recallable' in cell_str or 'recall' in cell_str:
                return True
        
        return False
    
    def _parse_date(self, value: Any) -> Optional[str]:
        """Parse various date formats into ISO format (YYYY-MM-DD)"""
        if not value:
            return None
        
        date_str = str(value).strip()
        
        # Common date patterns
        date_patterns = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2024-01-15
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 01/15/2024 or 15/01/2024
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # 01-15-2024
            r'(\d{4})/(\d{1,2})/(\d{1,2})',  # 2024/01/15
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    groups = match.groups()
                    if len(groups[0]) == 4:  # Year first
                        year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                    else:  # Month/day first
                        # Try both MM/DD/YYYY and DD/MM/YYYY
                        if int(groups[0]) > 12:  # Must be day
                            day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                        else:
                            month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                    
                    # Validate
                    date_obj = datetime(year, month, day)
                    return date_obj.strftime('%Y-%m-%d')
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _parse_amount(self, value: Any) -> Optional[Decimal]:
        """Parse various amount formats into Decimal"""
        if not value:
            return None
        
        amount_str = str(value).strip()
        
        # Reject abbreviated forms (M, K, B, etc.)
        if re.search(r'\d+\.?\d*\s*[MKBmkb]', amount_str):
            return None
        
        # Remove common currency symbols and formatting
        amount_str = amount_str.replace('$', '').replace('€', '').replace('£', '')
        amount_str = amount_str.replace(',', '').replace(' ', '')
        
        # Handle parentheses for negative numbers
        is_negative = False
        if '(' in amount_str and ')' in amount_str:
            is_negative = True
            amount_str = amount_str.replace('(', '').replace(')', '')
        
        # Extract numeric value
        match = re.search(r'[\d,]+\.?\d*', amount_str)
        if match:
            try:
                amount = Decimal(match.group().replace(',', ''))
                if is_negative:
                    amount = -amount
                return amount
            except:
                return None
        
        return None
    
    def _clean_cell_value(self, value: Any) -> str:
        """Clean and normalize cell value"""
        if value is None:
            return ""
        return str(value).strip()
