import React, { useState, useRef, useEffect } from 'react';
import {
  Box, Button, Typography, Paper, CircularProgress,
  TextField, Snackbar, Alert, Grid, Tabs, Tab, ButtonGroup,
  Card, CardContent, CardHeader, Divider, Chip, LinearProgress,
  ToggleButton, ToggleButtonGroup, IconButton, Tooltip
} from '@mui/material';
import { 
  CloudUpload as UploadIcon, 
  Download as DownloadIcon,
  Send as SendIcon,
  Visibility as VisibilityIcon,
  Code as CodeIcon,
  ContentCopy as ContentCopyIcon,
  Refresh as RefreshIcon,
  Computer as DesktopIcon,
  Tablet as TabletIcon,
  PhoneAndroid as PhoneIcon,
  AccessTime as TimerIcon,
  Fullscreen as FullscreenIcon,
  Dashboard as DashboardIcon
} from '@mui/icons-material';

const GeneradorUx = () => {
  const [files, setFiles] = useState([]);
  const [additionalText, setAdditionalText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [htmlStructure, setHtmlStructure] = useState(null);
  const [selectedScreen, setSelectedScreen] = useState(0);
  const [deviceView, setDeviceView] = useState('desktop'); // desktop, tablet, mobile
  const [rateLimitInfo, setRateLimitInfo] = useState(null);
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  const [viewMode, setViewMode] = useState(0); // 0: preview, 1: html, 2: css
  
  const fileInputRef = useRef(null);
  const previewRef = useRef(null);
  
  // Device viewport configurations
  const deviceConfigs = {
    desktop: { width: '100%', height: '600px', label: 'Desktop' },
    tablet: { width: '768px', height: '1024px', label: 'Tablet' },
    mobile: { width: '375px', height: '667px', label: 'Mobile' }
  };
  
  // Obtener estado de rate limiting al cargar
  useEffect(() => {
    fetchRateLimitStatus();
  }, []);
  
  const fetchRateLimitStatus = async () => {
    try {
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:5000';
      const response = await fetch(`${API_BASE_URL}/api/rate-limit-status`);
      const data = await response.json();
      setRateLimitInfo(data);
    } catch (error) {
      console.error('Error fetching rate limit status:', error);
    }
  };
  
  // Manejo de archivos
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
  
  // Generar interfaces HTML/CSS
  const generateHTMLInterfaces = async () => {
    if (files.length === 0 && !additionalText.trim()) {
      showNotification('Selecciona archivos o ingresa contexto del sistema', 'warning');
      return;
    }
    
    if (rateLimitInfo && !rateLimitInfo.can_make_request) {
      showNotification(`Rate limit alcanzado. Espera ${Math.ceil(rateLimitInfo.time_until_reset / 60)} minutos`, 'error');
      return;
    }
    
    setIsProcessing(true);
    setHtmlStructure(null);
    
    try {
      const formData = new FormData();
      
      files.forEach(file => {
        formData.append('files', file);
      });
      
      formData.append('additional_text', additionalText.trim());
      
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:5000';
      const apiResponse = await fetch(`${API_BASE_URL}/api/generar-interfaces-html`, {
        method: 'POST',
        body: formData,
      });
      
      if (!apiResponse.ok) {
        const errorData = await apiResponse.json();
        throw new Error(errorData.error || 'Error en el servidor');
      }
      
      const result = await apiResponse.json();
      setHtmlStructure(result.html_structure);
      setSelectedScreen(0);
      showNotification(
        `¡${result.total_screens} pantallas HTML generadas en ${result.generation_time}s!`, 
        'success'
      );
      
      // Actualizar rate limit info
      fetchRateLimitStatus();
      
    } catch (error) {
      console.error('Error:', error);
      showNotification(`Error: ${error.message}`, 'error');
    } finally {
      setIsProcessing(false);
    }
  };
  
  // Renderizar HTML en iframe
  const renderHTMLPreview = () => {
    if (!htmlStructure || !previewRef.current) return;
    
    const screen = htmlStructure.screens[selectedScreen];
    if (!screen) return;
    
    const iframe = previewRef.current;
    const doc = iframe.contentDocument || iframe.contentWindow.document;
    
    // Crear HTML completo
    const fullHTML = `
      <!DOCTYPE html>
      <html lang="es">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>${screen.title}</title>
        <style>
          ${htmlStructure.global_styles || ''}
          ${screen.css || ''}
          
          /* Responsive preview adjustments */
          @media (max-width: 768px) {
            body { font-size: 14px; }
            .container { padding: 10px !important; }
          }
          
          @media (max-width: 480px) {
            body { font-size: 12px; }
            .container { padding: 5px !important; }
          }
        </style>
      </head>
      <body>
        ${screen.html || '<div>No HTML content</div>'}
        
        <script>
          // Prevenir navegación en el iframe
          document.addEventListener('click', function(e) {
            if (e.target.tagName === 'A') {
              e.preventDefault();
            }
          });
          
          // Simular interactividad básica
          document.addEventListener('DOMContentLoaded', function() {
            // Hover effects para botones
            const buttons = document.querySelectorAll('button, .btn, .btn-primary');
            buttons.forEach(btn => {
              btn.style.transition = 'all 0.3s ease';
              btn.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-1px)';
                this.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
              });
              btn.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = '';
              });
            });
            
            // Click simulation
            buttons.forEach(btn => {
              btn.addEventListener('click', function(e) {
                e.preventDefault();
                this.style.transform = 'scale(0.98)';
                setTimeout(() => {
                  this.style.transform = '';
                }, 150);
              });
            });
          });
        </script>
      </body>
      </html>
    `;
    
    doc.open();
    doc.write(fullHTML);
    doc.close();
  };
  
  // Effect para renderizar cuando cambie la pantalla o dispositivo
  useEffect(() => {
    if (htmlStructure) {
      setTimeout(renderHTMLPreview, 100);
    }
  }, [htmlStructure, selectedScreen, deviceView]);
  
  // Descargar código HTML completo
  const downloadHTML = () => {
    if (!htmlStructure) {
      showNotification('No hay contenido para descargar', 'warning');
      return;
    }
    
    const screen = htmlStructure.screens[selectedScreen];
    const fullHTML = `
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${screen.title}</title>
  <style>
    ${htmlStructure.global_styles || ''}
    ${screen.css || ''}
  </style>
</head>
<body>
  ${screen.html || ''}
</body>
</html>`;
    
    const blob = new Blob([fullHTML], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${screen.id || 'screen'}.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showNotification('Archivo HTML descargado', 'success');
  };
  
  // Descargar todas las pantallas como ZIP
  const downloadAllScreens = () => {
    if (!htmlStructure) {
      showNotification('No hay contenido para descargar', 'warning');
      return;
    }
    
    // Crear estructura JSON completa
    const fullStructure = {
      ...htmlStructure,
      timestamp: new Date().toISOString(),
      screens_count: htmlStructure.screens.length
    };
    
    const blob = new Blob([JSON.stringify(fullStructure, null, 2)], { 
      type: 'application/json;charset=utf-8' 
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${htmlStructure.project_name || 'Interfaces'}_Complete.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showNotification('Estructura completa descargada', 'success');
  };
  
  // Copiar código al portapapeles
  const copyToClipboard = async () => {
    if (!htmlStructure) {
      showNotification('No hay contenido para copiar', 'warning');
      return;
    }
    
    const screen = htmlStructure.screens[selectedScreen];
    let contentToCopy = '';
    
    if (viewMode === 1) { // HTML
      contentToCopy = screen.html || '';
    } else if (viewMode === 2) { // CSS
      contentToCopy = `${htmlStructure.global_styles || ''}\n\n${screen.css || ''}`;
    } else { // Estructura completa
      contentToCopy = JSON.stringify(htmlStructure, null, 2);
    }

    try {
      await navigator.clipboard.writeText(contentToCopy);
      showNotification('Código copiado al portapapeles', 'success');
    } catch (err) {
      console.error('Error al copiar:', err);
      showNotification('Error al copiar al portapapeles', 'error');
    }
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
  
  const handleViewModeChange = (event, newValue) => {
    setViewMode(newValue);
  };
  
  const handleDeviceChange = (event, newDevice) => {
    if (newDevice !== null) {
      setDeviceView(newDevice);
    }
  };
  
  return (
    <Box sx={{ p: 3, maxWidth: 1600, margin: '0 auto' }}>
      <Typography variant="h4" gutterBottom align="center">
        Generador de Interfaces HTML/CSS Responsive
      </Typography>
      
      <Typography variant="body1" align="center" color="text.secondary" sx={{ mb: 3 }}>
        Crea interfaces HTML/CSS reales y funcionales con diseño responsive
      </Typography>
      
      {/* Rate Limit Info */}
      {rateLimitInfo && (
        <Paper sx={{ p: 2, mb: 3, backgroundColor: rateLimitInfo.can_make_request ? '#e8f5e8' : '#ffeaa7' }}>
          <Box display="flex" alignItems="center" gap={2}>
            <TimerIcon />
            <Typography variant="body2">
              Requests: {rateLimitInfo.requests_made}/{rateLimitInfo.rate_limit}
              {rateLimitInfo.time_until_reset > 0 && (
                <span> | Reset en: {Math.ceil(rateLimitInfo.time_until_reset / 60)} min</span>
              )}
            </Typography>
            <Button size="small" onClick={fetchRateLimitStatus} startIcon={<RefreshIcon />}>
              Actualizar
            </Button>
          </Box>
        </Paper>
      )}
      
      <Grid container spacing={3}>
        {/* Panel de configuración */}
        <Grid item xs={12} md={4}>
          {/* Carga de archivos */}
          <Paper sx={{ p: 3, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Documentos del Sistema
            </Typography>
            
            <Paper
              elevation={0}
              sx={{
                p: 3,
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
                accept=".pdf,.md,.markdown,.txt"
              />
              <UploadIcon sx={{ fontSize: 32, color: 'text.secondary', mb: 1 }} />
              <Typography variant="body2" gutterBottom>
                Arrastra archivos o haz clic
              </Typography>
              <Typography variant="caption" color="text.secondary">
                PDF, Markdown, TXT
              </Typography>
            </Paper>
            
            {files.length > 0 && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Archivos seleccionados:
                </Typography>
                {files.map((file, index) => (
                  <Typography key={index} variant="body2" sx={{ ml: 1, fontSize: '0.8rem' }}>
                    • {file.name}
                  </Typography>
                ))}
              </Box>
            )}
          </Paper>
          
          {/* Contexto adicional */}
          <Paper sx={{ p: 3, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Contexto del Sistema
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Describe las funcionalidades, usuarios, procesos y requerimientos del sistema.
            </Typography>
            
            <TextField
              fullWidth
              multiline
              rows={6}
              variant="outlined"
              placeholder="Ejemplo:
Sistema de gestión de inventarios para retail
- Módulos: Dashboard, Usuarios, Productos, Inventario, Reportes
- Usuarios: Admin, Operadores, Supervisores
- Funcionalidades CRUD completas para cada módulo
- Dashboard con métricas en tiempo real
- Reportes exportables (PDF, Excel)
- Gestión de roles y permisos granulares
- Alertas de stock bajo
- Integración con API de proveedores
- Responsive design para tablet y móvil..."
              value={additionalText}
              onChange={(e) => setAdditionalText(e.target.value)}
              sx={{
                '& .MuiInputBase-input': {
                  fontFamily: 'monospace',
                  fontSize: '0.8rem'
                }
              }}
            />
            
            {additionalText.trim() && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Caracteres: {additionalText.length}
              </Typography>
            )}
          </Paper>
          
          {/* Botón generar */}
          <Button
            variant="contained"
            size="large"
            fullWidth
            onClick={generateHTMLInterfaces}
            disabled={isProcessing || (files.length === 0 && !additionalText.trim()) || (rateLimitInfo && !rateLimitInfo.can_make_request)}
            startIcon={isProcessing ? <CircularProgress size={20} color="inherit" /> : <DashboardIcon />}
            sx={{ py: 1.5 }}
          >
            {isProcessing ? 'Generando Interfaces...' : 'Generar Interfaces HTML/CSS'}
          </Button>
        </Grid>
        
        {/* Panel de visualización */}
        <Grid item xs={12} md={8}>
          {htmlStructure && (
            <Paper sx={{ p: 3 }}>
              {/* Header con info del proyecto */}
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Box>
                  <Typography variant="h6">
                    {htmlStructure.project_name || 'Interfaces Generadas'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {htmlStructure.screens?.length || 0} pantallas HTML/CSS responsive
                  </Typography>
                </Box>
                <Box display="flex" gap={1}>
                  <Button
                    variant="outlined"
                    startIcon={<ContentCopyIcon />}
                    onClick={copyToClipboard}
                    size="small"
                  >
                    Copiar
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<DownloadIcon />}
                    onClick={downloadHTML}
                    size="small"
                  >
                    HTML
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<DownloadIcon />}
                    onClick={downloadAllScreens}
                    size="small"
                  >
                    Todo
                  </Button>
                </Box>
              </Box>
              
              <Divider sx={{ mb: 2 }} />
              
              {/* Selector de pantallas */}
              <Box mb={2}>
                <Typography variant="subtitle2" gutterBottom>
                  Pantallas ({htmlStructure.screens?.length || 0}):
                </Typography>
                <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
                  {htmlStructure.screens?.map((screen, index) => (
                    <Chip
                      key={screen.id}
                      label={screen.title}
                      onClick={() => setSelectedScreen(index)}
                      variant={selectedScreen === index ? "filled" : "outlined"}
                      color={selectedScreen === index ? "primary" : "default"}
                      size="small"
                    />
                  ))}
                </Box>
              </Box>
              
              {/* Device selector */}
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="subtitle2">
                  Vista del dispositivo:
                </Typography>
                <ToggleButtonGroup
                  value={deviceView}
                  exclusive
                  onChange={handleDeviceChange}
                  size="small"
                >
                  <ToggleButton value="desktop">
                    <Tooltip title="Desktop (1200px+)">
                      <DesktopIcon />
                    </Tooltip>
                  </ToggleButton>
                  <ToggleButton value="tablet">
                    <Tooltip title="Tablet (768px)">
                      <TabletIcon />
                    </Tooltip>
                  </ToggleButton>
                  <ToggleButton value="mobile">
                    <Tooltip title="Mobile (375px)">
                      <PhoneIcon />
                    </Tooltip>
                  </ToggleButton>
                </ToggleButtonGroup>
              </Box>
              
              {/* Tabs para vista */}
              <Tabs value={viewMode} onChange={handleViewModeChange} sx={{ mb: 2 }}>
                <Tab icon={<VisibilityIcon />} label="Vista Previa" iconPosition="start" />
                <Tab icon={<CodeIcon />} label="HTML" iconPosition="start" />
                <Tab icon={<CodeIcon />} label="CSS" iconPosition="start" />
              </Tabs>
              
              {viewMode === 0 ? (
                // Vista Previa HTML
                <Box>
                  <Typography variant="body2" color="text.secondary" mb={2}>
                    {htmlStructure.screens[selectedScreen]?.description} 
                    <Chip 
                      label={deviceConfigs[deviceView].label} 
                      size="small" 
                      sx={{ ml: 1 }} 
                    />
                  </Typography>
                  
                  <Paper
                    variant="outlined"
                    sx={{
                      p: 1,
                      backgroundColor: '#f5f5f5',
                      overflow: 'auto',
                      display: 'flex',
                      justifyContent: 'center'
                    }}
                  >
                    <Box
                      sx={{
                        width: deviceConfigs[deviceView].width,
                        height: deviceConfigs[deviceView].height,
                        maxWidth: '100%',
                        border: '1px solid #ddd',
                        borderRadius: deviceView === 'mobile' ? '20px' : '8px',
                        overflow: 'hidden',
                        backgroundColor: 'white',
                        boxShadow: deviceView !== 'desktop' ? '0 4px 20px rgba(0,0,0,0.15)' : 'none'
                      }}
                    >
                      <iframe
                        ref={previewRef}
                        width="100%"
                        height="100%"
                        style={{ 
                          border: 'none',
                          borderRadius: 'inherit'
                        }}
                        title={`Preview - ${deviceView}`}
                      />
                    </Box>
                  </Paper>
                </Box>
              ) : viewMode === 1 ? (
                // Vista HTML
                <TextField
                  fullWidth
                  multiline
                  rows={20}
                  value={htmlStructure.screens[selectedScreen]?.html || ''}
                  variant="outlined"
                  InputProps={{
                    readOnly: true,
                    style: { 
                      fontFamily: 'monospace', 
                      fontSize: '0.8rem',
                      whiteSpace: 'pre-wrap'
                    }
                  }}
                />
              ) : (
                // Vista CSS
                <TextField
                  fullWidth
                  multiline
                  rows={20}
                  value={`/* Global Styles */\n${htmlStructure.global_styles || ''}\n\n/* Screen Specific Styles */\n${htmlStructure.screens[selectedScreen]?.css || ''}`}
                  variant="outlined"
                  InputProps={{
                    readOnly: true,
                    style: { 
                      fontFamily: 'monospace', 
                      fontSize: '0.8rem',
                      whiteSpace: 'pre-wrap'
                    }
                  }}
                />
              )}
            </Paper>
          )}
          
          {!htmlStructure && !isProcessing && (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <DashboardIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Sube documentos y genera interfaces HTML/CSS
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Las interfaces responsive se mostrarán aquí una vez generadas
              </Typography>
            </Paper>
          )}
        </Grid>
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

export default GeneradorUx;