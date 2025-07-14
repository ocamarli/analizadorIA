// Validación de entrada para evitar caracteres no numéricos
function validateInput(input) {
    const validCharacters = /^[0-9.+\-*/]+$/;
    return validCharacters.test(input);
}

console.log(validateInput('123+')); // true
console.log(validateInput('abc')); // false