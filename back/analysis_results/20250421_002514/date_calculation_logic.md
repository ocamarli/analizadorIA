# Date Calculation Logic

## Formula
- Next day from the date of return
- Frequency of route
- Days of transit
- Offset days
- Sundays
- Holidays

## Exception Handling
- If holidays are not registered, use default holiday list.
- If route frequency changes, recalculate based on new frequency.

## Example
```javascript
function calculatePickupDate(returnDate, routeFrequency, transitDays, offsetDays) {
    const pickupDate = new Date(returnDate);
    pickupDate.setDate(pickupDate.getDate() + routeFrequency + transitDays + offsetDays);
    return pickupDate;
}
```