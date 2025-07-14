// Manejo de errores persistentes
function handleError(expression) {
    try {
        const result = eval(expression);
        return result;
    } catch (error) {
        console.error('Error en la expresión:', error);
        return 'Error';
    }
}

console.log(handleError('5+')); // Error
console.log(handleError('5+5')); // 10