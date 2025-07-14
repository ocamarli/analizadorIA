// Example code for handling errors in SEPOMEX API connection
function fetchSEPOMEXData() {
    try {
        const response = await fetch('https://sepomex.api/catalog');
        if (!response.ok) {
            throw new Error('Failed to fetch data from SEPOMEX');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching SEPOMEX data:', error);
        alert('Unable to connect to SEPOMEX. Please try again later.');
    }
}