export const formatearFecha = (fecha) => {
    const opciones = { year: 'numeric', month: '2-digit', day: '2-digit' };
    return new Date(fecha).toLocaleDateString('es-MX', opciones);

  };
  export const filtrarColumnasPorPermisos = (columns, usuario) => {
    // Obtén las llaves de los permisos que están en true
    const permissionsArray = Object.keys(usuario.permisos).filter(key => usuario.permisos[key] === true);
  console.log("per",permissionsArray)
    return columns.filter(column =>
      !column.permisosRequeridos ||
      column.permisosRequeridos.some(permiso => permissionsArray.includes(permiso))
    );
  };
  export const handleOnChangeInputTexto = (event) => {
    // Expresión regular que permite letras (mayúsculas y minúsculas) y espacios en blanco
    const regex = /^[A-Za-z\s]*$/;
    const inputValue = event.target.value;
  
    // Validar si el texto ingresado cumple con la expresión regular
    if (regex.test(inputValue)) {
      // Si cumple, convertir a mayúsculas y establecer en el campo de texto
      event.target.value = inputValue.toUpperCase();
    } else {
      // Si no cumple, eliminar el último caracter ingresado
      event.target.value = inputValue.slice(0, -1);
    }
  };
  export const handleOnChangeInputIdPlantilla = (event) => {
    // Expresión regular que permite cuatro dígitos donde el primer dígito no puede ser cero
    const regex = /^[1-9]\d{0,6}$/;
    const inputValue = event.target.value;
  console.log("onChange")
    // Validar si el texto ingresado cumple con la expresión regular
    if (regex.test(inputValue)) {
      // Si cumple, establecer el valor en el campo de texto
      event.target.value = inputValue;
    } else {
      // Si no cumple, eliminar el último caracter ingresado
      event.target.value = inputValue.slice(0, -1);
    }
  };
  export const handleOnChangeInputIds = (event) => {
    // Expresión regular que permite cuatro dígitos donde el primer dígito no puede ser cero
    const regex = /^[1-9]\d{0,6}$/;
    const inputValue = event.target.value;
  console.log("onChange")
    // Validar si el texto ingresado cumple con la expresión regular
    if (regex.test(inputValue)) {
      // Si cumple, establecer el valor en el campo de texto
      event.target.value = inputValue;
    } else {
      // Si no cumple, eliminar el último caracter ingresado
      event.target.value = inputValue.slice(0, -1);
    }
  };  
  export const handleOnChangeInputTextoNumero = (event) => {
    // Expresión regular que permite letras, números, espacios, guiones bajos y guiones medios
    const regex = /^[A-Za-zñÑáéíóúÁÉÍÓÚ0-9\s_-]*$/;
    const inputValue = event.target.value;
  
    // Validar si el texto ingresado cumple con la expresión regular
    if (regex.test(inputValue)) {
      // Si cumple, eliminar los espacios en blanco al principio y convertir a mayúsculas
      event.target.value = inputValue.replace(/^\s+/, '').toUpperCase();
    } else {
      // Si no cumple, eliminar el último carácter ingresado
      event.target.value = inputValue.slice(0, -1);
    }
  };
  export const handleOnChangeInputTextoNumeroMinusculas = (event) => {
    // Expresión regular que permite letras, números, espacios, guiones bajos y guiones medios
    const regex = /^[A-Za-zñÑáéíóúÁÉÍÓÚ0-9\s_-]*$/;
    const inputValue = event.target.value;
  
    // Validar si el texto ingresado cumple con la expresión regular
    if (regex.test(inputValue)) {
      // Si cumple, eliminar los espacios en blanco al principio y convertir a mayúsculas
      event.target.value = inputValue.replace(/^\s+/, '');
    } else {
      // Si no cumple, eliminar el último carácter ingresado
      event.target.value = inputValue.slice(0, -1);
    }
  };
  export const handleOnChangeInputParametros = (event) => {
    // Expresión regular que permite letras (mayúsculas y minúsculas) y espacios en blanco
    const regex = /^\d{0,3}$/;
    const inputValue = event.target.value;
  
    // Validar si el texto ingresado cumple con la expresión regular
    if (regex.test(inputValue)) {
      // Si cumple, convertir a mayúsculas y establecer en el campo de texto
      event.target.value = inputValue.toUpperCase();
    } else {
      // Si no cumple, eliminar el último caracter ingresado
      event.target.value = inputValue.slice(0, -1);
    }
  };
  