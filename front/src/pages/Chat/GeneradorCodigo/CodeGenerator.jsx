import React, { useState, useRef, useEffect } from 'react';
import {
  Button, TextField, Grid, Typography, Box, Paper, CircularProgress, IconButton,
  Tabs, Tab, Snackbar, Alert, Divider, List, ListItem, ListItemIcon, ListItemText,
  Tooltip, Menu, MenuItem, Chip, Stack
} from '@mui/material';
import {
  MicRounded as MicIcon,
  ContentCopyRounded as CopyIcon,
  SaveRounded as SaveIcon,
  CodeRounded as CodeIcon,
  FolderRounded as FolderIcon,
  DownloadRounded as DownloadIcon,
  CreateNewFolderRounded as CreateNewFolderIcon,
  FileDownloadRounded as FileDownloadIcon,
  ArrowBackRounded as ArrowBackIcon,
  DataUsageRounded as DataUsageIcon
} from '@mui/icons-material';
import FolderZipIcon from '@mui/icons-material/FolderZip';
import Editor from '@monaco-editor/react';
import JSZip from 'jszip';
import { saveAs } from 'file-saver';

const CodeGenerator = () => {
  // Estados para la entrada y la respuesta
  const [input, setInput] = useState("");
  const [listening, setListening] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [response, setResponse] = useState("");
  
  // Estado para tokens
  const [tokenUsage, setTokenUsage] = useState({
    prompt_tokens: 0,
    completion_tokens: 0,
    total_tokens: 0
  });
  
  // Estados para los archivos generados
  const [generatedFiles, setGeneratedFiles] = useState([]);
  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  
  // Estado para el explorador de archivos
  const [fileStructure, setFileStructure] = useState({
    name: 'proyecto',
    type: 'folder',
    children: []
  });
  const [currentPath, setCurrentPath] = useState([]);
  const [showFileExplorer, setShowFileExplorer] = useState(true);
  
  // Estado para menú contextual
  const [contextMenu, setContextMenu] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  
  // Estado para notificaciones
  const [notification, setNotification] = useState({
    open: false,
    message: "",
    severity: "success"
  });

  // Referencias
  const editorRef = useRef(null);
  
  // Manejadores de eventos
  const handleInputChange = (event) => setInput(event.target.value);
  
  const handleTabChange = (event, newValue) => {
    setCurrentFileIndex(newValue);
  };

  const copyToClipboard = () => {
    if (generatedFiles.length > 0 && currentFileIndex < generatedFiles.length) {
      navigator.clipboard.writeText(generatedFiles[currentFileIndex].content)
        .then(() => {
          handleOpenSnackbar("Código copiado al portapapeles", "success");
        })
        .catch(err => {
          handleOpenSnackbar("Error al copiar: " + err, "error");
        });
    }
  };

  const handleOpenSnackbar = (message, severity = "success") => {
    setNotification({
      open: true,
      message,
      severity
    });
  };

  const handleCloseSnackbar = () => {
    setNotification(prev => ({ ...prev, open: false }));
  };

  // Función para manejar el editor
  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;
    
    // Configurar el editor
    monaco.editor.defineTheme('codeTheme', {
      base: 'vs-dark',
      inherit: true,
      rules: [],
      colors: {
        'editor.background': '#1e1e1e',
      }
    });
    
    monaco.editor.setTheme('codeTheme');
  };

  // Función para actualizar el contenido del archivo actual en el editor
  const updateFileContent = (value) => {
    if (generatedFiles.length > 0 && currentFileIndex < generatedFiles.length) {
      setGeneratedFiles(prev => 
        prev.map((file, idx) => 
          idx === currentFileIndex ? {...file, content: value} : file
        )
      );
      
      // También actualiza el archivo en la estructura de carpetas
      const updatedFile = generatedFiles[currentFileIndex];
      updateFileInStructure(fileStructure, updatedFile.path, value);
    }
  };
  
  // Función recursiva para actualizar un archivo en la estructura
  const updateFileInStructure = (node, path, content) => {
    if (path.length === 0) return node;
    
    const [current, ...rest] = path;
    
    if (node.type === 'folder') {
      const updatedChildren = node.children.map(child => {
        if (child.name === current) {
          if (rest.length === 0 && child.type === 'file') {
            return { ...child, content };
          } else {
            return updateFileInStructure(child, rest, content);
          }
        }
        return child;
      });
      
      return { ...node, children: updatedChildren };
    }
    
    return node;
  };

  // Función para generar código a partir de la solicitud
  const generateCode = async (prompt) => {
    if (!prompt) return;
    
    setIsGenerating(true);
    setResponse("");
    setGeneratedFiles([]);
    // Reiniciar los tokens
    setTokenUsage({
      prompt_tokens: 0,
      completion_tokens: 0,
      total_tokens: 0
    });
    
    try {
      // Llamar directamente al endpoint de generación de código
      const response = await fetch("http://127.0.0.1:5000/api/generate-code", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: prompt }),
      });
      
      if (!response.ok) {
        throw new Error(`Error al generar código: ${response.statusText}`);
      }
      
      const responseData = await response.json();
      
      // Guardar información de tokens si existe
      if (responseData.token_usage) {
        setTokenUsage(responseData.token_usage);
      }
      
      // Construir la estructura de archivos
      const structure = {
        name: 'proyecto',
        type: 'folder',
        children: []
      };
      
      // Procesar los archivos generados
      const processedFiles = responseData.files.map(file => {
        const pathParts = file.name.split('/');
        const fileName = pathParts.pop();
        
        // Construir la estructura de carpetas
        let currentLevel = structure;
        
        for (const part of pathParts) {
          // Buscar si ya existe la carpeta
          let folder = currentLevel.children.find(child => child.name === part && child.type === 'folder');
          
          // Si no existe, crearla
          if (!folder) {
            folder = {
              name: part,
              type: 'folder',
              children: []
            };
            currentLevel.children.push(folder);
          }
          
          currentLevel = folder;
        }
        
        // Añadir el archivo a la estructura
        const fileObj = {
          name: fileName,
          type: 'file',
          language: file.language,
          content: file.content,
          path: pathParts.concat(fileName)
        };
        
        currentLevel.children.push(fileObj);
        
        return {
          ...file,
          path: pathParts.concat(fileName)
        };
      });
      
      // Actualizar el estado con los resultados
      setResponse(responseData.explanation);
      setGeneratedFiles(processedFiles);
      setFileStructure(structure);
      setCurrentPath([]);
      
      // Configurar el editor para el primer archivo
      if (processedFiles.length > 0) {
        setCurrentFileIndex(0);
      }
      
    } catch (error) {
      console.error("Error al generar código:", error);
      handleOpenSnackbar("Error al generar código: " + error.message, "error");
    } finally {
      setIsGenerating(false);
    }
  };

  // Función para reconocer voz
  const startListening = async () => {
    try {
      setListening(true);
      
      // Iniciar el reconocimiento de voz del navegador
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      
      if (!SpeechRecognition) {
        throw new Error("El reconocimiento de voz no está soportado en este navegador");
      }
      
      const recognition = new SpeechRecognition();
      recognition.lang = "es-MX";
      recognition.continuous = false;
      recognition.interimResults = false;
      
      return new Promise((resolve, reject) => {
        recognition.onresult = (event) => {
          const transcript = event.results[0][0].transcript;
          resolve(transcript);
        };
        
        recognition.onerror = (event) => {
          reject(new Error(`Error en el reconocimiento: ${event.error}`));
        };
        
        recognition.start();
      })
      .then(text => {
        setInput(text);
        setListening(false);
        // Generar código automáticamente después del reconocimiento
        generateCode(text);
      });
      
    } catch (error) {
      console.error("Error en el reconocimiento de voz:", error);
      setListening(false);
      handleOpenSnackbar("Error en el reconocimiento de voz: " + error.message, "error");
    }
  };

  // Función para obtener el color de la etiqueta del archivo basado en el lenguaje
  const getLanguageColor = (language) => {
    const colors = {
      javascript: "#f0db4f",
      typescript: "#007acc",
      python: "#306998",
      java: "#b07219",
      go: "#00ADD8",
      html: "#e34c26",
      css: "#563d7c",
      csharp: "#178600",
      php: "#4F5D95",
      ruby: "#CC342D"
    };
    
    return colors[language?.toLowerCase()] || "#777";
  };
  
  // Funciones para el explorador de archivos
  const getCurrentFolder = () => {
    let folder = fileStructure;
    
    for (const part of currentPath) {
      folder = folder.children.find(child => child.name === part);
      if (!folder || folder.type !== 'folder') break;
    }
    
    return folder;
  };
  
  const navigateToFolder = (folderName) => {
    setCurrentPath(prev => [...prev, folderName]);
  };
  
  const navigateBack = () => {
    setCurrentPath(prev => prev.slice(0, -1));
  };
  
  const openFile = (file, path) => {
    // Buscar el archivo en la lista de archivos generados
    const fileIndex = generatedFiles.findIndex(f => 
      JSON.stringify(f.path) === JSON.stringify(path.concat(file.name))
    );
    
    if (fileIndex !== -1) {
      setCurrentFileIndex(fileIndex);
    } else {
      // Si no está en la lista, añadirlo
      const newFile = {
        name: path.concat(file.name).join('/'),
        language: file.language || 'plaintext',
        content: file.content || '',
        path: path.concat(file.name)
      };
      
      setGeneratedFiles(prev => [...prev, newFile]);
      setCurrentFileIndex(prev => prev.length);
    }
  };
  
  // Menú contextual
  const handleContextMenu = (event, item, path) => {
    event.preventDefault();
    setContextMenu({ x: event.clientX, y: event.clientY });
    setSelectedItem({ item, path });
  };
  
  const handleCloseContextMenu = () => {
    setContextMenu(null);
    setSelectedItem(null);
  };

  // Función para descargar todos los archivos como ZIP
  const downloadAsZip = () => {
    const zip = new JSZip();
    
    // Función recursiva para agregar archivos al ZIP
    const addFilesToZip = (node, path = '') => {
      if (node.type === 'folder') {
        node.children.forEach(child => {
          const childPath = path ? `${path}/${node.name}` : node.name;
          addFilesToZip(child, childPath);
        });
      } else {
        const filePath = path ? `${path}/${node.name}` : node.name;
        zip.file(filePath, node.content || '');
      }
    };
    
    // Agregar todos los archivos al ZIP
    fileStructure.children.forEach(child => {
      addFilesToZip(child, '');
    });
    
    // Generar el archivo ZIP y descargarlo
    zip.generateAsync({ type: 'blob' })
      .then(content => {
        saveAs(content, 'proyecto.zip');
        handleOpenSnackbar('Proyecto descargado como ZIP', 'success');
      })
      .catch(error => {
        console.error('Error al generar ZIP:', error);
        handleOpenSnackbar('Error al descargar el proyecto', 'error');
      });
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Cabecera */}
      <Paper elevation={2} sx={{ p: 2, borderRadius: 0 }}>
        <Typography variant="h5" component="div">
          <CodeIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Generador de Código
        </Typography>
      </Paper>
      
      <Grid container sx={{ flexGrow: 1, overflow: 'hidden' }}>
        {/* Panel izquierdo: Explorador de archivos */}
        {showFileExplorer && (
          <Grid item xs={12} md={2} sx={{ 
            borderRight: 1, 
            borderColor: 'divider',
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            overflow: 'hidden'
          }}>
            <Box sx={{ 
              p: 1, 
              borderBottom: 1, 
              borderColor: 'divider', 
              display: 'flex', 
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <Typography variant="subtitle2">Explorador</Typography>
              <Tooltip title="Descargar proyecto">
                <IconButton size="small" onClick={downloadAsZip} disabled={generatedFiles.length === 0}>
                  <FolderZipIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
            
            <Box sx={{ p: 1, borderBottom: 1, borderColor: 'divider' }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                {currentPath.length > 0 && (
                  <IconButton size="small" onClick={navigateBack}>
                    <ArrowBackIcon fontSize="small" />
                  </IconButton>
                )}
                <Typography variant="body2" noWrap>
                  /{currentPath.join('/')}
                </Typography>
              </Box>
            </Box>
            
            <List dense sx={{ overflow: 'auto', flexGrow: 1 }}>
              {getCurrentFolder()?.children?.map((item, index) => (
                <ListItem 
                  key={index}
                  button
                  onClick={() => item.type === 'folder' ? navigateToFolder(item.name) : openFile(item, currentPath)}
                  onContextMenu={(e) => handleContextMenu(e, item, currentPath)}
                  sx={{ 
                    py: 0.5,
                    pl: 1,
                    borderLeft: item.type === 'file' ? `3px solid ${getLanguageColor(item.language)}` : 'none'
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 30 }}>
                    {item.type === 'folder' ? (
                      <FolderIcon fontSize="small" color="primary" />
                    ) : (
                      <CodeIcon fontSize="small" color="default" />
                    )}
                  </ListItemIcon>
                  <ListItemText 
                    primary={item.name}
                    primaryTypographyProps={{ 
                      variant: 'body2',
                      noWrap: true
                    }}
                  />
                </ListItem>
              ))}
            </List>
          </Grid>
        )}
        
        {/* Panel central: Entrada y respuesta */}
        <Grid item xs={12} md={showFileExplorer ? 4 : 5} sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          height: '100%',
          overflow: 'hidden'
        }}>
          {/* Área de entrada */}
          <Paper elevation={0} sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            <Typography variant="subtitle1" gutterBottom>
              Descripción del código
            </Typography>
            
            <TextField
              label="¿Qué código necesitas generar?"
              placeholder="Ej: Crea una API REST en Go que se conecte a PostgreSQL siguiendo los estándares de Coppel"
              multiline
              rows={4}
              fullWidth
              value={input}
              onChange={handleInputChange}
              variant="outlined"
              disabled={isGenerating}
              sx={{ mb: 2 }}
            />
            
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                color="primary"
                fullWidth
                onClick={() => generateCode(input)}
                disabled={isGenerating || !input.trim()}
                startIcon={isGenerating ? <CircularProgress size={20} color="inherit" /> : <CodeIcon />}
              >
                {isGenerating ? "Generando..." : "Generar Código"}
              </Button>
              
              <IconButton 
                onClick={startListening} 
                color="primary"
                disabled={listening || isGenerating}
                sx={{ bgcolor: 'rgba(0, 0, 0, 0.05)' }}
              >
                {listening ? <CircularProgress size={24} /> : <MicIcon />}
              </IconButton>
            </Box>
          </Paper>
          
          {/* Área de respuesta */}
          <Box sx={{ 
            flexGrow: 1, 
            overflow: 'auto', 
            p: 2,
            borderBottom: { xs: 1, md: 0 },
            borderColor: 'divider' 
          }}>
            <Typography variant="subtitle1" gutterBottom>
              Explicación
            </Typography>
            
            {response ? (
              <Paper elevation={1} sx={{ p: 2 }}>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {response}
                </Typography>
                
                {/* Mostrar información de tokens directamente integrada */}
                {tokenUsage.total_tokens > 0 && (
                  <Box sx={{ mt: 2, borderTop: 1, borderColor: 'divider', pt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <DataUsageIcon sx={{ mr: 1, fontSize: 20 }} />
                      Información de uso
                    </Typography>
                    
                    <Stack direction="row" spacing={2} sx={{ flexWrap: 'wrap' }}>
                      <Tooltip title="Tokens utilizados en el prompt">
                        <Chip 
                          label={`Prompt: ${tokenUsage.prompt_tokens.toLocaleString()}`}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      </Tooltip>
                      
                      <Tooltip title="Tokens generados en la respuesta">
                        <Chip 
                          label={`Respuesta: ${tokenUsage.completion_tokens.toLocaleString()}`}
                          size="small"
                          color="secondary"
                          variant="outlined"
                        />
                      </Tooltip>
                      
                      <Tooltip title="Total de tokens utilizados">
                        <Chip 
                          label={`Total: ${tokenUsage.total_tokens.toLocaleString()}`}
                          size="small"
                          color="info"
                          sx={{ fontWeight: 'bold' }}
                        />
                      </Tooltip>
                    </Stack>
                  </Box>
                )}
              </Paper>
            ) : (
              isGenerating ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                  <CircularProgress />
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  La explicación del código generado aparecerá aquí...
                </Typography>
              )
            )}
          </Box>
        </Grid>
        
        {/* Panel derecho: Editor */}
        <Grid item xs={12} md={showFileExplorer ? 6 : 7} sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          height: '100%',
          overflow: 'hidden',
          borderLeft: { md: 1, xs: 0 },
          borderColor: 'divider'
        }}>
          {/* Pestañas de archivos */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <IconButton 
                  size="small" 
                  onClick={() => setShowFileExplorer(!showFileExplorer)}
                  sx={{ mr: 1 }}
                >
                  <FolderIcon fontSize="small" />
                </IconButton>
                <Typography variant="subtitle2">
                  Archivos
                </Typography>
              </Box>
              
              <Box>
                <Tooltip title="Copiar código">
                  <IconButton onClick={copyToClipboard} disabled={generatedFiles.length === 0} size="small">
                    <CopyIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Descargar archivo actual">
                  <IconButton 
                    onClick={() => {
                      if (generatedFiles.length > 0 && currentFileIndex < generatedFiles.length) {
                        const file = generatedFiles[currentFileIndex];
                        const blob = new Blob([file.content], { type: 'text/plain' });
                        saveAs(blob, file.name.split('/').pop());
                      }
                    }} 
                    disabled={generatedFiles.length === 0} 
                    size="small"
                  >
                    <FileDownloadIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Descargar proyecto">
                  <IconButton onClick={downloadAsZip} disabled={generatedFiles.length === 0} size="small">
                    <DownloadIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
            
            <Tabs 
              value={currentFileIndex} 
              onChange={handleTabChange}
              variant="scrollable"
              scrollButtons="auto"
              sx={{ minHeight: '36px' }}
            >
              {generatedFiles.map((file, index) => (
                <Tab 
                  key={index} 
                  label={file.name.split('/').pop()}
                  sx={{ 
                    minHeight: '36px', 
                    textTransform: 'none',
                    fontSize: '0.75rem',
                    py: 0.5,
                    borderBottom: `3px solid ${getLanguageColor(file.language)}`,
                    opacity: 1
                  }} 
                />
              ))}
            </Tabs>
          </Box>
          
          {/* Editor de código */}
          <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
            {generatedFiles.length > 0 ? (
              <Editor
                height="100%"
                language={generatedFiles[currentFileIndex]?.language || 'plaintext'}
                value={generatedFiles[currentFileIndex]?.content || ''}
                theme="vs-dark"
                onMount={handleEditorDidMount}
                onChange={updateFileContent}
                options={{
                  minimap: { enabled: true },
                  scrollBeyondLastLine: false,
                  fontSize: 14,
                  wordWrap: 'on',
                  readOnly: false,
                  automaticLayout: true,
                  lineNumbers: 'on',
                  folding: true
                }}
              />
            ) : (
              <Box 
                sx={{ 
                  height: '100%',
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  flexDirection: 'column',
                  bgcolor: '#1e1e1e',
                  color: '#cccccc',
                }}
              >
                <CodeIcon sx={{ fontSize: 60, opacity: 0.5, mb: 2 }} />
                <Typography variant="body1">
                  {isGenerating ? "Generando código..." : "El código generado aparecerá aquí"}
                </Typography>
              </Box>
            )}
          </Box>
        </Grid>
      </Grid>
      
      {/* Menú contextual */}
      <Menu
        open={Boolean(contextMenu)}
        onClose={handleCloseContextMenu}
        anchorReference="anchorPosition"
        anchorPosition={contextMenu ? { top: contextMenu.y, left: contextMenu.x } : undefined}
      >
        {selectedItem?.item.type === 'file' ? (
          [
            <MenuItem key="open" onClick={() => {
              openFile(selectedItem.item, selectedItem.path);
              handleCloseContextMenu();
            }}>
              Abrir
            </MenuItem>,
            <MenuItem key="download" onClick={() => {
              const blob = new Blob([selectedItem.item.content], { type: 'text/plain' });
              saveAs(blob, selectedItem.item.name);
              handleCloseContextMenu();
            }}>
              Descargar
            </MenuItem>
          ]
        ) : (
          <MenuItem key="open" onClick={() => {
            navigateToFolder(selectedItem.item.name);
            handleCloseContextMenu();
          }}>
            Abrir
          </MenuItem>
        )}
      </Menu>
      
      {/* Notificaciones */}
      <Snackbar 
        open={notification.open} 
        autoHideDuration={4000} 
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={notification.severity}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default CodeGenerator;