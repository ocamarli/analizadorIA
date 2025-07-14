# Date Calculation Logic

## Rules for Date Calculation:
1. Exclude Sundays and public holidays.
2. Add extra days for zones with restricted access.
3. Use the following formula:
   `Date of Return + Frequency of Route + Transit Days + Offset Days`

## Example:
- Return Date: 2023-10-01
- Frequency of Route: 2 days
- Transit Days: 3 days
- Offset Days: 1 day
- Public Holiday: 2023-10-02

**Calculated Date:** 2023-10-07