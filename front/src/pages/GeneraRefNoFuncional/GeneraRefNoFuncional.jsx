import React, { useState, useRef } from 'react';
import {
  Box, Button, Typography, Paper, CircularProgress,
  TextField, Snackbar, Alert, Grid
} from '@mui/material';
import { 
  Upload as UploadIcon, 
  Download as DownloadIcon,
  Send as SendIcon
} from '@mui/icons-material';

const GeneraRefNoFuncional= () => {
  const [files, setFiles] = useState([]);
  const [additionalText, setAdditionalText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [response, setResponse] = useState('');
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  
  const fileInputRef = useRef(null);
  
  // Manejo de archivos
  const handleFileChange = (event) => {
    const selectedFiles = Array.from(event.target.files);
    const validFiles = selectedFiles.filter(file => 
      file.type === 'application/pdf' || 
      file.name.toLowerCase().endsWith('.md') ||
      file.name.toLowerCase().endsWith('.markdown')
    );
    
    if (validFiles.length !== selectedFiles.length) {
      showNotification('Solo archivos PDF y Markdown', 'warning');
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
      file.name.toLowerCase().endsWith('.markdown')
    );
    
    setFiles(validFiles);
  };
  
  const handleDragOver = (event) => {
    event.preventDefault();
    event.stopPropagation();
  };
  
  // Generar DEF requerimientos funcionales
  const generateDef = async () => {
    // Validar que haya al menos archivos o texto
    if (files.length === 0 && !additionalText.trim()) {
      showNotification('Selecciona archivos o ingresa texto adicional', 'warning');
      return;
    }
    
    setIsProcessing(true);
    setResponse('');
    
    try {
      const formData = new FormData();
      
      // Agregar archivos si existen
      files.forEach(file => {
        formData.append('files', file);
      });
      
      // Agregar texto adicional
      formData.append('additional_text', additionalText.trim());
      
      const apiResponse = await fetch('http://127.0.0.1:5000/api/generar-def-requerimientos', {
        method: 'POST',
        body: formData,
      });
      
      if (!apiResponse.ok) {
        const errorData = await apiResponse.json();
        throw new Error(errorData.error || 'Error en el servidor');
      }
      
      const result = await apiResponse.json();
      setResponse(result.respuesta);
      showNotification('¡Documento DEF generado!', 'success');
      
    } catch (error) {
      console.error('Error:', error);
      showNotification(`Error: ${error.message}`, 'error');
    } finally {
      setIsProcessing(false);
    }
  };
  
  // Descargar respuesta como archivo
  const downloadResponse = () => {
    if (!response) {
      showNotification('No hay contenido para descargar', 'warning');
      return;
    }
    
    const blob = new Blob([response], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `DEF_Requerimientos_${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showNotification('Archivo descargado', 'success');
  };
  
  const showNotification = (message, severity = 'info') => {
    setNotification({
      open: true,
      message,
      severity
    });
  };
  
  const handleCloseNotification = () => {
    setNotification(prev => ({ ...prev, open: false }));
  };
  
  return (
    <Box sx={{ p: 3, maxWidth: 800, margin: '0 auto' }}>
      <Typography variant="h4" gutterBottom align="center">
        Refinamientos No Funcionales
      </Typography>
      
      <Grid container spacing={3}>
        {/* Carga de archivos */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Documentos de Análisis de Negocio
            </Typography>
            
            <Paper
              elevation={0}
              sx={{
                p: 4,
                border: '2px dashed #ccc',
                textAlign: 'center',
                cursor: 'pointer',
                mb: 2,
                '&:hover': { borderColor: 'primary.main' }
              }}
              onClick={() => fileInputRef.current.click()}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                style={{ display: 'none' }}
                multiple
                accept=".pdf,.md,.markdown"
              />
              <UploadIcon sx={{ fontSize: 40, color: 'text.secondary', mb: 1 }} />
              <Typography variant="body1" gutterBottom>
                Arrastra archivos o haz clic para seleccionar
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Formatos: PDF, Markdown (.md)
              </Typography>
            </Paper>
            
            {files.length > 0 && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Archivos seleccionados:
                </Typography>
                {files.map((file, index) => (
                  <Typography key={index} variant="body2" sx={{ ml: 2 }}>
                    • {file.name}
                  </Typography>
                ))}
              </Box>
            )}
          </Paper>
        </Grid>
        
        {/* Caja de texto adicional */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Información Adicional (Opcional)
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Puedes agregar contexto adicional, requerimientos específicos, o cualquier información que complemente los documentos subidos.
            </Typography>
            
            <TextField
              fullWidth
              multiline
              rows={6}
              variant="outlined"
              placeholder="Ejemplo: 
- El sistema debe manejar 1000 usuarios concurrentes
- Integración con API de pagos requerida
- Interfaz responsive para móviles
- Reportes en tiempo real necesarios..."
              value={additionalText}
              onChange={(e) => setAdditionalText(e.target.value)}
              sx={{
                '& .MuiInputBase-input': {
                  fontFamily: 'monospace',
                  fontSize: '0.875rem'
                }
              }}
            />
            
            {additionalText.trim() && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Caracteres: {additionalText.length}
              </Typography>
            )}
          </Paper>
        </Grid>
        
        {/* Botón generar */}
        <Grid item xs={12}>
          <Button
            variant="contained"
            size="large"
            fullWidth
            onClick={generateDef}
            disabled={isProcessing || (files.length === 0 && !additionalText.trim())}
            startIcon={isProcessing ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
            sx={{ py: 1.5 }}
          >
            {isProcessing ? 'Generando...' : 'Generar Documento DEF'}
          </Button>
        </Grid>
        
        {/* Respuesta */}
        {response && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  Documento DEF Generado
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={downloadResponse}
                >
                  Descargar
                </Button>
              </Box>
              
              <TextField
                fullWidth
                multiline
                rows={20}
                value={response}
                variant="outlined"
                InputProps={{
                  readOnly: true,
                  style: { 
                    fontFamily: 'monospace', 
                    fontSize: '0.875rem',
                    whiteSpace: 'pre-wrap'
                  }
                }}
              />
            </Paper>
          </Grid>
        )}
      </Grid>
      
      {/* Notificaciones */}
      <Snackbar
        open={notification.open}
        autoHideDuration={4000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseNotification} severity={notification.severity}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default GeneraRefNoFuncional