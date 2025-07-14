# Date Calculation Logic

## Parameters:
- **Frequency of Route**: Number of days between scheduled routes.
- **Days of Transit**: Estimated days for transit.
- **Holidays**: List of holidays to exclude from calculation.

## Formula:
`Date of Collection = Current Date + Frequency of Route + Days of Transit - Holidays`

## Example:
If today is 2023-10-01, frequency of route is 2 days, transit is 3 days, and there is a holiday on 2023-10-03:

`Date of Collection = 2023-10-01 + 2 + 3 - 1 (holiday) = 2023-10-05`