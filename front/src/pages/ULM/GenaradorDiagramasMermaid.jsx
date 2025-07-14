import React, { useState, useRef, useEffect } from 'react';
import mermaid from 'mermaid';

const GeneradorDiagramasMermaid = () => {
  const [selectedDiagram, setSelectedDiagram] = useState('sequence');
  const [files, setFiles] = useState([]);
  const [additionalText, setAdditionalText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [mermaidResult, setMermaidResult] = useState('');
  const [mermaidError, setMermaidError] = useState('');
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  
  const fileInputRef = useRef(null);
  const mermaidRef = useRef(null);
  
  // Configurar Mermaid
  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      securityLevel: 'loose',
      fontFamily: 'Arial, sans-serif'
    });
  }, []);

  // Renderizar diagrama Mermaid
  useEffect(() => {
    if (mermaidResult && mermaidRef.current) {
      const renderDiagram = async () => {
        try {
          setMermaidError('');
          // Limpiar el contenedor
          mermaidRef.current.innerHTML = '';
          
          // Generar ID único para el diagrama
          const diagramId = `mermaid-${Date.now()}`;
          
          // Validar y renderizar
          const isValid = await mermaid.parse(mermaidResult);
          if (isValid) {
            const { svg } = await mermaid.render(diagramId, mermaidResult);
            mermaidRef.current.innerHTML = svg;
          }
        } catch (error) {
          console.error('Error renderizando Mermaid:', error);
          setMermaidError(`Error renderizando el diagrama: ${error.message}`);
          mermaidRef.current.innerHTML = `
            <div style="padding: 20px; background: #fee; border: 1px solid #fcc; border-radius: 4px; color: #c00;">
              <strong>Error de Sintaxis:</strong><br/>
              ${error.message}
            </div>
          `;
        }
      };
      
      renderDiagram();
    }
  }, [mermaidResult]);
  
const diagramTypes = {
  sequence: {
    name: 'Diagrama de Secuencia',
    endpoint: 'diagramaSecuenciaMermaid',
    description: 'Muestra la interacción entre objetos a lo largo del tiempo',
    placeholder: `Ejemplo:
- Sistema de E-commerce
- Proceso de Compra Online
- Actores: Usuario, Frontend React, API Gateway, Servicios
- Flujo: Login → Búsqueda → Carrito → Pago → Confirmación
- Tecnologías: React.js, Node.js, PostgreSQL, Redis, Stripe
- Validaciones: JWT, Stock, Pagos, Timeouts
- Manejo de errores: Pago rechazado, Stock insuficiente`,
    mermaidPrefix: 'sequenceDiagram'
  },
  class: {
    name: 'Diagrama de Clases',
    endpoint: 'diagramaClasesMermaid',
    description: 'Representa la estructura estática del sistema',
    placeholder: `Ejemplo:
- Sistema de Gestión Escolar
- Clases: Estudiante, Profesor, Curso, Calificacion
- Atributos: id, nombre, email, especialidad
- Métodos: matricular(), asignarCalificacion(), crearCurso()
- Relaciones: Herencia, Composición, Agregación
- Tecnologías: Java Spring Boot, JPA, PostgreSQL`,
    mermaidPrefix: 'classDiagram'
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
- Sistema: Hotel Management System`,
    mermaidPrefix: 'graph TD'
  },
  flowchart: {
    name: 'Diagrama de Flujo',
    endpoint: 'diagramaFlujoMermaid',
    description: 'Representa procesos y flujos de decisión',
    placeholder: `Ejemplo:
- Proceso de Autenticación de Usuario
- Pasos: Ingreso datos → Validación → Autenticación → Respuesta
- Decisiones: Datos válidos?, Usuario existe?, Credenciales correctas?
- Tecnologías: JWT, bcrypt, OAuth2, Redis
- Manejo de errores: Datos inválidos, Usuario no encontrado`,
    mermaidPrefix: 'flowchart TD'
  },
  er: {
    name: 'Diagrama Entidad-Relación',
    endpoint: 'diagramaER',
    description: 'Modela la estructura de una base de datos',
    placeholder: `Ejemplo:
- Base de Datos E-commerce
- Entidades: Usuario, Producto, Pedido, Categoria
- Atributos: id, nombre, precio, email, fecha_creacion
- Relaciones: Usuario-Pedido (1:N), Producto-Categoria (N:1)
- Tecnologías: PostgreSQL, MySQL, MongoDB`,
    mermaidPrefix: 'erDiagram'
  },
  impact: {
    name: 'Matriz de Impacto',
    endpoint: 'matrizImpacto',
    description: 'Mapea el impacto de historias de usuario en capas arquitectónicas',
    placeholder: `Ejemplo:
- Sistema de Gestión de Inventarios
- Historias de Usuario: HU001-Consultar Stock, HU002-Actualizar Inventario, HU003-Generar Reportes
- Capas: Interfaz → Dominio → Proxy → Repositorio
- Servicios: ConsultarStock, ActualizarInventario, GenerarReportes
- Tecnologías: React Frontend, Spring Boot, PostgreSQL
- Arquitectura: Clean Architecture, Microservicios, API Gateway
- Componentes: Controllers, Services, Repositories, DTOs`,
    mermaidPrefix: 'flowchart TD'
  },
  architecture: {
  name: 'Diagrama de Arquitectura',
  endpoint: 'diagramaArquitectura',
  description: 'Muestra la estructura y relaciones de componentes arquitectónicos',
  placeholder: `Ejemplo:
- Sistema E-commerce en Microservicios
- Capas: Frontend, Gateway, Services, Data
- Componentes: Web App, API Gateway, User Service, Product Service
- Infraestructura: Load Balancer, Redis Cache, PostgreSQL
- Cloud: AWS/Azure services, containers, databases
- Conexiones: HTTP APIs, message queues, database connections`,
  mermaidPrefix: 'architecture-beta'
},
technology: {
  name: 'Diagrama Tecnológico',
  endpoint: 'diagramaTecnologia',
  description: 'Muestra la infraestructura tecnológica detallada, servicios cloud y stack tecnológico',
  placeholder: `Ejemplo:
- Stack Tecnológico: JDK 21, SpringBoot 3.2, Angular 17, PostgreSQL 15
- Cloud Platform: GCP (GKE, Cloud SQL, Cloud Storage, Cloud Armor)
- Infraestructura: Kubernetes clusters, Load Balancers, Ingress Controllers
- Microservicios: User Management, Product Catalog, Order Processing
- Bases de Datos: PostgreSQL, Redis Cache, Cloud Spanner, BigQuery
- Seguridad: Cloud IAM, SSL/TLS, Firewall rules
- Integración: APIs REST, Pub/Sub messaging, External services
- Monitoreo: Cloud Logging, Cloud Monitoring, Distributed Tracing
- Red: VPC, Subnets, DNS, CDN
- On-Premise: Legacy systems, File servers, Mainframe connections`,
  mermaidPrefix: 'flowchart TD'
}
};
  // Estilos MUI-like (mantenemos los mismos estilos)
  const styles = {
    container: {
      padding: '24px',
      maxWidth: '1200px',
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
      textAlign: 'center',
      color: '#1976d2'
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
    buttonSuccess: {
      backgroundColor: '#4caf50',
      color: 'white'
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
    },
    previewContainer: {
      display: 'flex',
      gap: '24px',
      flexWrap: 'wrap'
    },
    codeContainer: {
      flex: '1',
      minWidth: '300px'
    },
    previewArea: {
      flex: '1',
      minWidth: '400px',
      border: '1px solid #ddd',
      borderRadius: '4px',
      padding: '16px',
      backgroundColor: '#fafafa',
      overflow: 'auto'
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

  // Funciones de manejo de archivos (mantienen la misma lógica)
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
  
  // Función principal para generar diagrama Mermaid
  const generateDiagram = async () => {
    if (files.length === 0 && !additionalText.trim()) {
      showNotification('Selecciona archivos o ingresa información adicional', 'warning');
      return;
    }
    
    setIsProcessing(true);
    setMermaidResult('');
    
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
        setMermaidResult(result.mermaid_content);
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
  
  // Función para descargar el código Mermaid
  const downloadMermaid = () => {
    if (!mermaidResult) {
      showNotification('No hay contenido para descargar', 'warning');
      return;
    }
    
    const blob = new Blob([mermaidResult], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `diagrama_${selectedDiagram}_${new Date().toISOString().split('T')[0]}.mmd`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showNotification('Archivo Mermaid descargado', 'success');
  };
  
  // Función para abrir en Mermaid Live Editor
  const openInMermaidLive = () => {
    if (!mermaidResult) {
      showNotification('No hay contenido Mermaid para abrir', 'warning');
      return;
    }
    
    const encodedMermaid = encodeURIComponent(mermaidResult);
    const mermaidUrl = `https://mermaid.live/edit#pako:${btoa(mermaidResult)}`;
    window.open(mermaidUrl, '_blank');
    showNotification('Abriendo diagrama en Mermaid Live', 'success');
  };

  // Función para copiar al portapapeles
  const copyToClipboard = async () => {
    if (!mermaidResult) {
      showNotification('No hay contenido para copiar', 'warning');
      return;
    }
    
    try {
      await navigator.clipboard.writeText(mermaidResult);
      showNotification('Código copiado al portapapeles', 'success');
    } catch (err) {
      // Fallback para navegadores que no soportan clipboard API
      const textArea = document.createElement('textarea');
      textArea.value = mermaidResult;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      showNotification('Código copiado al portapapeles', 'success');
    }
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
        🧜‍♀️ Generador de Diagramas Mermaid
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
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <p style={{ color: '#666', fontSize: '14px', margin: '0' }}>
            Endpoint: /api/{diagramTypes[selectedDiagram].endpoint}/generate
          </p>
          <p style={{ color: '#1976d2', fontSize: '14px', margin: '0', fontWeight: 500 }}>
            Sintaxis: {diagramTypes[selectedDiagram].mermaidPrefix}
          </p>
        </div>
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
      
      {/* Resultado Mermaid */}
      {mermaidResult && (
        <div style={styles.paper}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={styles.h6}>
              Código Mermaid - {diagramTypes[selectedDiagram].name}
            </h2>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>


            </div>
          </div>
          
          <div style={styles.previewContainer}>
            <div style={styles.codeContainer}>
              <h3 style={{ fontSize: '16px', fontWeight: 500, marginBottom: '8px' }}>
                Código Mermaid:
              </h3>
              <textarea
                value={mermaidResult}
                readOnly
                style={{
                  ...styles.textField,
                  minHeight: '400px',
                  backgroundColor: '#f9f9f9',
                  fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace'
                }}
              />
            </div>
            
            <div style={styles.previewArea}>
              <h3 style={{ fontSize: '16px', fontWeight: 500, marginBottom: '16px' }}>
                Vista Previa:
              </h3>
              
              {mermaidError ? (
                <div style={{ 
                  padding: '16px',
                  backgroundColor: '#fee',
                  border: '1px solid #fcc',
                  borderRadius: '4px',
                  color: '#c00',
                  marginBottom: '16px'
                }}>
                  <strong>Error:</strong> {mermaidError}
                </div>
              ) : null}
              
              <div style={styles.mermaidContainer}>
                <div ref={mermaidRef} style={{ width: '100%', textAlign: 'center' }}>
                  {!mermaidResult ? (
                    <p style={{ color: '#666', fontStyle: 'italic' }}>
                      El diagrama se mostrará aquí una vez generado
                    </p>
                  ) : null}
                </div>
              </div>
              
              <div style={{ marginTop: '16px', display: 'flex', gap: '8px', justifyContent: 'center' }}>
                <button
                  onClick={openInMermaidLive}
                  style={{ ...styles.button, ...styles.buttonSuccess, width: 'auto' }}
                  disabled={!mermaidResult}
                >
                  🔗 Abrir mermaid.com
                </button>
                <button
                  onClick={copyToClipboard}
                  style={{ ...styles.button, ...styles.buttonOutlined, width: 'auto' }}
                  disabled={!mermaidResult}
                >
                  📋 Copiar
                </button>
                <button
                  onClick={() => {
                    if (mermaidResult) {
                      setMermaidResult('');
                      setMermaidError('');
                      showNotification('Vista previa limpiada', 'info');
                    }
                  }}
                  style={{ ...styles.button, ...styles.buttonOutlined, width: 'auto' }}
                  disabled={!mermaidResult}
                >
                  🗑️ Limpiar
                </button>

              <button
                onClick={downloadMermaid}
                style={{ ...styles.button, ...styles.buttonOutlined, width: 'auto' }}
              >
                💾 Descargar
              </button>                
              </div>
            </div>
          </div>
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

export default GeneradorDiagramasMermaid;