from datetime import datetime, timedelta
from .base import BaseTool # Removed Dict, Any import as it's not used for casting here

class DateCalculator(BaseTool):
    def __init__(self):
        super().__init__(
            name="calculate_date",
            description="Calculate dates by adding or subtracting days/months/years from a given date",
            parameters={ # type: ignore
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

    def execute(self, **kwargs: any) -> str: # type: ignore
        operation = kwargs.get('operation')
        amount_arg = kwargs.get('amount')
        unit = kwargs.get('unit')
        date_arg = kwargs.get('date')

        if not isinstance(operation, str) or not operation:
            raise ValueError("Missing or invalid 'operation' (string) argument for DateCalculator.")
        if amount_arg is None:
            raise ValueError("Missing 'amount' argument for DateCalculator.")
        # amount_arg will be converted to int in the try block
        if not isinstance(unit, str) or not unit:
            raise ValueError("Missing or invalid 'unit' (string) argument for DateCalculator.")
        if not isinstance(date_arg, str) or not date_arg:
            raise ValueError("Missing or invalid 'date' (string) argument for DateCalculator.")

        try:
            # Convert amount to integer
            amount = int(str(amount_arg))
            
            if date_arg.lower() == 'today': # date_arg is now confirmed str
                base_date = datetime.now().date()
            else:
                base_date = datetime.strptime(date_arg, '%Y-%m-%d').date()

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
            else:
                raise ValueError(f"Invalid unit: {unit}")

            return result_date.strftime('%Y-%m-%d')
        except Exception as e:
            raise ValueError(f"Failed to calculate date: {str(e)}")

class DateDifference(BaseTool):
    def __init__(self):
        super().__init__(
            name="date_difference",
            description="Calculate the difference between two dates in days",
            parameters={ # type: ignore
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

    def execute(self, **kwargs: any) -> int: # type: ignore
        date1_arg = kwargs.get('date1')
        date2_arg = kwargs.get('date2')

        if not isinstance(date1_arg, str) or not date1_arg:
            raise ValueError("Missing or invalid 'date1' (string) argument for DateDifference.")
        if not isinstance(date2_arg, str) or not date2_arg:
            raise ValueError("Missing or invalid 'date2' (string) argument for DateDifference.")

        try:
            d1 = datetime.now() if date1_arg.lower() == 'today' else datetime.strptime(date1_arg, '%Y-%m-%d') # date1_arg is confirmed str
            d2 = datetime.now() if date2_arg.lower() == 'today' else datetime.strptime(date2_arg, '%Y-%m-%d') # date2_arg is confirmed str
            return abs((d2 - d1).days)
        except Exception as e:
            raise ValueError(f"Failed to calculate date difference: {str(e)}")

class GetCurrentDate(BaseTool):
    def __init__(self):
        super().__init__(
            name="get_current_date",
            description="Get the current date",
            parameters={ # type: ignore
                'type': 'object',
                'properties': {}
            }
        )

    def execute(self, **kwargs: any) -> str: # type: ignore
        try:
            return datetime.now().strftime('%Y-%m-%d')
        except Exception as e:
            raise ValueError(f"Failed to get current date: {str(e)}")

class GetCurrentTime(BaseTool):
    def __init__(self):
        super().__init__(
            name="get_current_time",
            description="Get the current time",
            parameters={ # type: ignore
                'type': 'object',
                'properties': {}
            }
        )

    def execute(self, **kwargs: any) -> str: # type: ignore
        try:
            return datetime.now().strftime('%H:%M:%S')
        except Exception as e:
            raise ValueError(f"Failed to get current time: {str(e)}")

class GetCurrentDayName(BaseTool):
    def __init__(self):
        super().__init__(
            name="get_current_day_name",
            description="Get the name of the current day (e.g., Monday, Tuesday).",
            parameters={ # type: ignore
                'type': 'object',
                'properties': {}
            }
        )

    def execute(self, **kwargs: any) -> str: # type: ignore
        try:
            return datetime.now().strftime('%A')
        except Exception as e:
            raise ValueError(f"Failed to get current day name: {str(e)}")
