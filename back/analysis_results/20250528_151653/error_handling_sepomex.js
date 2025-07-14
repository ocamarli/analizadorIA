// Example code for handling errors in SEPOMEX connection
function fetchSepomexData(postalCode) {
    try {
        const response = await fetch(`https://api.sepomex.com/postal-code/${postalCode}`);
        if (!response.ok) {
            throw new Error('Error fetching data from SEPOMEX');
        }
        return await response.json();
    } catch (error) {
        console.error('Error:', error);
        alert('Unable to fetch data from SEPOMEX. Please try again later.');
    }
}