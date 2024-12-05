from datetime import datetime, timedelta
from .base import BaseTool

class DateCalculator(BaseTool):
    def __init__(self):
        super().__init__(
            name="calculate_date",
            description="Calculate dates by adding or subtracting days/months/years from a given date",
            parameters={
                'type': 'object',
                'required': ['operation', 'amount', 'unit', 'date'],
                'properties': {
                    'operation': {
                        'type': 'string',
                        'enum': ['add', 'subtract'],
                        'description': 'Whether to add or subtract time'
                    },
                    'amount': {
                        'type': 'integer',
                        'description': 'Amount of time to add/subtract'
                    },
                    'unit': {
                        'type': 'string',
                        'enum': ['days', 'months', 'years'],
                        'description': 'Unit of time to add/subtract'
                    },
                    'date': {
                        'type': 'string',
                        'description': 'Date in YYYY-MM-DD format. Use "today" for current date'
                    }
                }
            }
        )

    def execute(self, operation: str, amount: int, unit: str, date: str) -> str:
        try:
            # Convert amount to integer
            amount = int(str(amount))
            
            if date.lower() == 'today':
                base_date = datetime.now().date()
            else:
                base_date = datetime.strptime(date, '%Y-%m-%d').date()

            if unit == 'days':
                delta = timedelta(days=amount)
                if operation == 'add':
                    result_date = base_date + delta
                else:
                    result_date = base_date - delta
            elif unit == 'months':
                # Add/subtract months by manipulating the date components
                year = base_date.year
                month = base_date.month + (amount if operation == 'add' else -amount)
                year += month // 12
                month = month % 12
                if month == 0:
                    month = 12
                    year -= 1
                day = min(base_date.day, [31,29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,31,30,31,30,31,31,30,31,30,31][month-1])
                result_date = base_date.replace(year=year, month=month, day=day)
            elif unit == 'years':
                result_date = base_date.replace(year=base_date.year + (amount if operation == 'add' else -amount))

            return result_date.strftime('%Y-%m-%d')
        except Exception as e:
            raise ValueError(f"Failed to calculate date: {str(e)}")

class DateDifference(BaseTool):
    def __init__(self):
        super().__init__(
            name="date_difference",
            description="Calculate the difference between two dates in days",
            parameters={
                'type': 'object',
                'required': ['date1', 'date2'],
                'properties': {
                    'date1': {
                        'type': 'string',
                        'description': 'First date in YYYY-MM-DD format. Use "today" for current date'
                    },
                    'date2': {
                        'type': 'string',
                        'description': 'Second date in YYYY-MM-DD format. Use "today" for current date'
                    }
                }
            }
        )

    def execute(self, date1: str, date2: str) -> int:
        try:
            d1 = datetime.now() if date1.lower() == 'today' else datetime.strptime(date1, '%Y-%m-%d')
            d2 = datetime.now() if date2.lower() == 'today' else datetime.strptime(date2, '%Y-%m-%d')
            return abs((d2 - d1).days)
        except Exception as e:
            raise ValueError(f"Failed to calculate date difference: {str(e)}")