// Example code for handling SEPOMEX catalog errors
function handleSEPOMEXError() {
    try {
        // Fetch catalog data
        let catalog = fetchCatalog();
        if (!catalog) {
            throw new Error('Catalog not available');
        }
    } catch (error) {
        console.error(error.message);
        alert('Error fetching catalog. Please enter data manually.');
    }
}