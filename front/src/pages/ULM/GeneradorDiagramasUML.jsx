import React, { useState, useRef } from 'react';

const GeneradorDiagramasUML = () => {
  const [selectedDiagram, setSelectedDiagram] = useState('sequence');
  const [files, setFiles] = useState([]);
  const [additionalText, setAdditionalText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [xmlResult, setXmlResult] = useState('');
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  
  const fileInputRef = useRef(null);
  
  const diagramTypes = {
    sequence: {
      name: 'Diagrama de Secuencia',
    endpoint: 'diagramaSecuencia',
      description: 'Muestra la interacción entre objetos a lo largo del tiempo',
      placeholder: `Ejemplo:
- Sistema de E-commerce - Proceso de Compra Online
- Actores: Usuario, Frontend React, API Gateway, Servicios
- Flujo: Login → Búsqueda → Carrito → Pago → Confirmación
- Tecnologías: React.js, Node.js, PostgreSQL, Redis, Stripe
- Validaciones: JWT, Stock, Pagos, Timeouts
- Manejo de errores: Pago rechazado, Stock insuficiente`
    },
    class: {
      name: 'Diagrama de Clases',
    endpoint: 'diagramaClases', 
      description: 'Representa la estructura estática del sistema',
      placeholder: `Ejemplo:
- Sistema de Gestión Escolar
- Clases: Estudiante, Profesor, Curso, Calificacion
- Atributos: id, nombre, email, especialidad
- Métodos: matricular(), asignarCalificacion(), crearCurso()
- Relaciones: Herencia, Composición, Agregación
- Tecnologías: Java Spring Boot, JPA, PostgreSQL`
    },
    usecase: {
      name: 'Casos de Uso',
    endpoint: 'diagramaCasosUso',
      description: 'Define funcionalidades desde la perspectiva del usuario',
      placeholder: `Ejemplo:
- Sistema de Reservas de Hotel
- Actores: Cliente, Recepcionista, Administrador, Sistema de Pagos
- Casos de Uso: Buscar habitaciones, Hacer reserva, Check-in
- Relaciones: include, extend, generalización
- Sistema: Hotel Management System`
    }
  };

  // Estilos MUI-like
  const styles = {
    container: {
      padding: '24px',
      maxWidth: '800px',
      margin: '0 auto',
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif'
    },
    paper: {
      backgroundColor: 'white',
      padding: '24px',
      borderRadius: '8px',
      boxShadow: '0px 2px 1px -1px rgba(0,0,0,0.2), 0px 1px 1px 0px rgba(0,0,0,0.14), 0px 1px 3px 0px rgba(0,0,0,0.12)',
      marginBottom: '24px'
    },
    h4: {
      fontSize: '2.125rem',
      fontWeight: 400,
      lineHeight: 1.235,
      margin: '0 0 32px 0',
      textAlign: 'center'
    },
    h6: {
      fontSize: '1.25rem',
      fontWeight: 500,
      lineHeight: 1.6,
      margin: '0 0 16px 0'
    },
    formControl: {
      width: '100%',
      marginBottom: '16px'
    },
    select: {
      width: '100%',
      padding: '16.5px 14px',
      borderRadius: '4px',
      border: '1px solid rgba(0, 0, 0, 0.23)',
      fontSize: '16px',
      fontFamily: 'inherit',
      backgroundColor: 'white'
    },
    uploadArea: {
      padding: '32px',
      border: '2px dashed #ccc',
      borderRadius: '4px',
      textAlign: 'center',
      cursor: 'pointer',
      marginBottom: '16px',
      transition: 'border-color 0.2s'
    },
    uploadAreaHover: {
      borderColor: '#1976d2'
    },
    textField: {
      width: '100%',
      padding: '12px',
      borderRadius: '4px',
      border: '1px solid rgba(0, 0, 0, 0.23)',
      fontFamily: 'monospace',
      fontSize: '14px',
      resize: 'vertical',
      minHeight: '120px'
    },
    button: {
      backgroundColor: '#1976d2',
      color: 'white',
      border: 'none',
      borderRadius: '4px',
      padding: '12px 24px',
      fontSize: '16px',
      fontWeight: 500,
      cursor: 'pointer',
      display: 'inline-flex',
      alignItems: 'center',
      gap: '8px',
      width: '100%',
      justifyContent: 'center',
      minHeight: '48px'
    },
    buttonDisabled: {
      backgroundColor: '#ccc',
      cursor: 'not-allowed'
    },
    buttonOutlined: {
      backgroundColor: 'transparent',
      color: '#1976d2',
      border: '1px solid rgba(25, 118, 210, 0.5)'
    },
    chip: {
      display: 'inline-flex',
      alignItems: 'center',
      padding: '4px 12px',
      backgroundColor: '#e0e0e0',
      borderRadius: '16px',
      fontSize: '13px',
      margin: '2px'
    },
    notification: {
      position: 'fixed',
      bottom: '20px',
      right: '20px',
      padding: '12px 16px',
      borderRadius: '4px',
      color: 'white',
      zIndex: 1000,
      boxShadow: '0px 3px 5px -1px rgba(0,0,0,0.2)'
    }
  };

  const getNotificationColor = (severity) => {
    switch (severity) {
      case 'success': return '#4caf50';
      case 'warning': return '#ff9800';
      case 'error': return '#f44336';
      default: return '#2196f3';
    }
  };

  // Funciones de manejo - IGUALES AL ORIGINAL
  const handleFileChange = (event) => {
    const selectedFiles = Array.from(event.target.files);
    const validFiles = selectedFiles.filter(file => 
      file.type === 'application/pdf' || 
      file.name.toLowerCase().endsWith('.md') ||
      file.name.toLowerCase().endsWith('.markdown') ||
      file.name.toLowerCase().endsWith('.txt')
    );
    
    if (validFiles.length !== selectedFiles.length) {
      showNotification('Solo archivos PDF, Markdown y TXT', 'warning');
    }
    
    setFiles(validFiles);
  };
  
  const handleDrop = (event) => {
    event.preventDefault();
    event.stopPropagation();
    
    const droppedFiles = Array.from(event.dataTransfer.files);
    const validFiles = droppedFiles.filter(file => 
      file.type === 'application/pdf' || 
      file.name.toLowerCase().endsWith('.md') ||
      file.name.toLowerCase().endsWith('.markdown') ||
      file.name.toLowerCase().endsWith('.txt')
    );
    
    setFiles(validFiles);
  };
  
  const handleDragOver = (event) => {
    event.preventDefault();
    event.stopPropagation();
  };
  
  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
    showNotification('Archivo removido', 'info');
  };
  
  const generateDiagram = async () => {
    if (files.length === 0 && !additionalText.trim()) {
      showNotification('Selecciona archivos o ingresa información adicional', 'warning');
      return;
    }
    
    setIsProcessing(true);
    setXmlResult('');
    
    try {
      const formData = new FormData();
      files.forEach(file => formData.append('files', file));
      formData.append('additional_text', additionalText.trim());
      
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:5000';
      const endpoint_url = `${API_BASE_URL}/api/${diagramTypes[selectedDiagram].endpoint}/generate`;
      
      console.log('Llamando a:', endpoint_url);
      
      const apiResponse = await fetch(endpoint_url, {
        method: 'POST',
        body: formData,
      });
      
      if (!apiResponse.ok) {
        const errorData = await apiResponse.json();
        throw new Error(errorData.error || 'Error en el servidor');
      }
      
      const result = await apiResponse.json();
      
      if (result.success) {
        setXmlResult(result.xml_content);
        showNotification(`¡${diagramTypes[selectedDiagram].name} generado!`, 'success');
      } else {
        throw new Error(result.error || 'Error al generar el diagrama');
      }
      
    } catch (error) {
      console.error('Error:', error);
      showNotification(`Error: ${error.message}`, 'error');
    } finally {
      setIsProcessing(false);
    }
  };
  
  const downloadXML = () => {
    if (!xmlResult) {
      showNotification('No hay contenido para descargar', 'warning');
      return;
    }
    
    const blob = new Blob([xmlResult], { type: 'application/xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `diagrama_${selectedDiagram}_${new Date().toISOString().split('T')[0]}.xml`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showNotification('Archivo XML descargado', 'success');
  };
  
  const openInDrawIO = () => {
    if (!xmlResult) {
      showNotification('No hay contenido XML para abrir', 'warning');
      return;
    }
    
    const encodedXml = encodeURIComponent(xmlResult);
    const drawioUrl = `https://app.diagrams.net/?xml=${encodedXml}`;
    window.open(drawioUrl, '_blank');
    showNotification('Abriendo diagrama en Draw.io', 'success');
  };
  
  const showNotification = (message, severity = 'info') => {
    setNotification({ open: true, message, severity });
    setTimeout(() => {
      setNotification(prev => ({ ...prev, open: false }));
    }, 4000);
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.h4}>
        Generador de Diagramas UML
      </h1>
      
      {/* Selector de Tipo de Diagrama */}
      <div style={styles.paper}>
        <h2 style={styles.h6}>Tipo de Diagrama</h2>
        
        <div style={styles.formControl}>
          <select
            value={selectedDiagram}
            onChange={(e) => setSelectedDiagram(e.target.value)}
            style={styles.select}
          >
            {Object.entries(diagramTypes).map(([key, diagram]) => (
              <option key={key} value={key}>
                {diagram.name} - {diagram.description}
              </option>
            ))}
          </select>
        </div>
        
        <p style={{ color: '#666', fontSize: '14px', margin: '0' }}>
          Endpoint: /api/{diagramTypes[selectedDiagram].endpoint}/generate
        </p>
      </div>
      
      {/* Carga de archivos */}
      <div style={styles.paper}>
        <h2 style={styles.h6}>Archivos de Especificación</h2>
        
        <div
          style={styles.uploadArea}
          onClick={() => fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onMouseEnter={(e) => e.target.style.borderColor = '#1976d2'}
          onMouseLeave={(e) => e.target.style.borderColor = '#ccc'}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            style={{ display: 'none' }}
            multiple
            accept=".pdf,.md,.markdown,.txt"
          />
          <div style={{ fontSize: '40px', color: '#999', marginBottom: '8px' }}>📁</div>
          <p style={{ margin: '0 0 8px 0', fontSize: '16px' }}>
            Arrastra archivos o haz clic para seleccionar
          </p>
          <p style={{ color: '#666', fontSize: '14px', margin: '0' }}>
            Formatos: PDF, Markdown (.md), Texto (.txt)
          </p>
        </div>
        
        {files.length > 0 && (
          <div>
            <h3 style={{ fontSize: '14px', fontWeight: 500, marginBottom: '8px' }}>
              Archivos seleccionados:
            </h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
              {files.map((file, index) => (
                <span key={index} style={styles.chip}>
                  {file.name}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(index);
                    }}
                    style={{
                      marginLeft: '8px',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      color: '#666'
                    }}
                  >
                    ✕
                  </button>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
      
      {/* Caja de texto adicional */}
      <div style={styles.paper}>
        <h2 style={styles.h6}>Información Técnica Adicional (Opcional)</h2>
        <p style={{ color: '#666', fontSize: '14px', marginBottom: '16px' }}>
          Agrega detalles técnicos específicos, arquitectura, tecnologías, o cualquier información que complemente las especificaciones del diagrama.
        </p>
        
        <textarea
          value={additionalText}
          onChange={(e) => setAdditionalText(e.target.value)}
          placeholder={diagramTypes[selectedDiagram].placeholder}
          style={styles.textField}
          rows={6}
        />
        
        {additionalText.trim() && (
          <p style={{ color: '#666', fontSize: '12px', margin: '8px 0 0 0' }}>
            Caracteres: {additionalText.length}
          </p>
        )}
      </div>
      
      {/* Botón generar */}
      <div style={styles.paper}>
        <button
          onClick={generateDiagram}
          disabled={isProcessing || (files.length === 0 && !additionalText.trim())}
          style={{
            ...styles.button,
            ...(isProcessing || (files.length === 0 && !additionalText.trim()) ? styles.buttonDisabled : {})
          }}
        >
          {isProcessing && <span>⏳</span>}
          {isProcessing ? 'Generando...' : `Generar ${diagramTypes[selectedDiagram].name}`}
        </button>
      </div>
      
      {/* Resultado XML */}
      {xmlResult && (
        <div style={styles.paper}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={styles.h6}>
              XML Generado - {diagramTypes[selectedDiagram].name}
            </h2>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={openInDrawIO}
                style={{ ...styles.button, ...styles.buttonOutlined, width: 'auto' }}
              >
                🔗 Abrir en Draw.io
              </button>
              <button
                onClick={downloadXML}
                style={{ ...styles.button, ...styles.buttonOutlined, width: 'auto' }}
              >
                💾 Descargar
              </button>
            </div>
          </div>
          
          <textarea
            value={xmlResult}
            readOnly
            style={{
              ...styles.textField,
              minHeight: '400px',
              backgroundColor: '#f9f9f9'
            }}
          />
        </div>
      )}
      
      {/* Notificaciones */}
      {notification.open && (
        <div style={{
          ...styles.notification,
          backgroundColor: getNotificationColor(notification.severity)
        }}>
          {notification.message}
        </div>
      )}
    </div>
  );
};

export default GeneradorDiagramasUML;