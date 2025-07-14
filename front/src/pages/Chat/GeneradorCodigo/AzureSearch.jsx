import { SearchClient, AzureKeyCredential } from "@azure/search-documents";

const apiKey = "YdBHzUf4al4bPNDgDOLLc9XDnPaxucfrBU47RQbXtRAzSeCujuVS";
const searchServiceName = "azuresearhdemobside";
const indexName = "azureblob-indexer-bside";

// Crear instancia del cliente de búsqueda
const searchClient = new SearchClient(
  `https://${searchServiceName}.search.windows.net`,
  indexName,
  new AzureKeyCredential(apiKey)
);

export const searchAzureDocuments = async (query) => {
  if (!query) return [];

  try {
    // Ejecutar la búsqueda con el cliente del SDK
    const searchResults = await searchClient.search(query, {
      select: ["content", "metadata_storage_name", "metadata_storage_path"],
      queryType: "semantic", // Habilita búsqueda semántica
    });

    // Extraer y devolver los resultados
    const documents = [];
    for await (const result of searchResults.results) {
      documents.push(result.document);
    }

    return documents; // Retorna los documentos encontrados

  } catch (error) {
    console.error("Error en la búsqueda de Azure Search:", error);
    return []; // Retorna un array vacío en caso de error
  }
};