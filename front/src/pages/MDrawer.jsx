import { styled, useTheme } from "@mui/material/styles";
import { CSSTransition, SwitchTransition } from "react-transition-group";
import MuiAppBar from "@mui/material/AppBar";
import {
  Divider,
  Toolbar,
  List,
  Box,
  Drawer,
  CssBaseline,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  FormControl,
  Collapse,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import ExpandLess from "@mui/icons-material/ExpandLess";
import ExpandMore from "@mui/icons-material/ExpandMore";
import React, { useState } from "react";
import Avatar from "@mui/material/Avatar";
import Brightness4Icon from "@mui/icons-material/Brightness4";
import Brightness7Icon from "@mui/icons-material/Brightness7";
import ExitToAppIcon from "@mui/icons-material/ExitToApp";
import SmartToyIcon from '@mui/icons-material/SmartToy';
import { useNavigate } from "react-router-dom";

// Iconos para categorías principales
import AnalyticsIcon from '@mui/icons-material/Analytics';
import PlaylistAddIcon from '@mui/icons-material/PlaylistAdd';
import FindReplaceIcon from '@mui/icons-material/FindReplace';
import AccountTreeOutlinedIcon from '@mui/icons-material/AccountTreeOutlined';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DescriptionIcon from '@mui/icons-material/Description';
import ArchitectureIcon from '@mui/icons-material/Architecture';

// Iconos para submenús
import HomeIcon from '@mui/icons-material/Home';
import CloudAnalyticsIcon from '@mui/icons-material/CloudQueue';
import FunctionalIcon from '@mui/icons-material/Functions';
import SecurityIcon from '@mui/icons-material/Security';
import EngineeringIcon from '@mui/icons-material/Engineering';
import TimelineIcon from '@mui/icons-material/Timeline';

import Home from "./Home/Home";
import "./MenuCss.css";
import Snackbar from "@mui/material/Snackbar";
import MuiAlert from "@mui/material/Alert";
import { alpha } from "@mui/material";
import RefinamientosHus from "./RefinamientosHus/RefinamientosHus";
import GeneradorDiagramasUML from "./ULM/GeneradorDiagramasUML";
import WebScraperApp from "./Chat/Scrap/WebScraperApp";
import GeneraDEF from "./GeneraDef/GeneraDEF";
import GeneradorHistoriasTecnicas from "./GeneraHistoriasTecnicas/GeneraHistoriasTecnicas";
import GeneraRefFuncional from "./GeneraRefFuncional/GeneraRefFuncional";
import GeneraRefNoFuncional from "./GeneraRefNoFuncional/GeneraRefNoFuncional";
import GeneraRefTecnico from "./GeneraRefTecnico/GeneraRefTecnico";
import AnalizarLegadoCloud from "./AnalizarLegadoCloud/AnalizarLegadoCloud";
import AnalizarCodigoO from "./AnalizarCodigoO/AnalizarCodigoO";
import AnalizarCodigoGO from "./AnalizarGO/AnalizarCodigoGO";
import Chatbot from "./Chat/ChatGeneral/Chatbot"
import GeneradorDiagramasMermaid from "./ULM/GenaradorDiagramasMermaid";
import AnalizarCodigoLegadoRepomix from "./AnalizarCodigoLegadoRepomix/AnalizarCodigoLegadoRepomix";
import AnalizarCodigoSQL from "./AnalizarCodigoSQL/AnalizarCodigoSQL";
import AnalizarArquitectura from "./AnalizarArquitectura/AnalizarArquitectura";
import GeneradorArquitecturaToBe from "./GeneraArquitecturaToBE/GeneraArquitecturaToBe";
import GeneradorHistoriasUsuario from "./GeneraHistoriasUsuario/GeneraHistoriasUsuario";
import GeneradorModeladoDatos from "./GenerarModeladoDatos/GenerarModeladoDatos";
import GeneradorDocumentoArquitectura from "./GeneraDocArquitecturaGeneral/GeneraDocArquitecturaGeneral";
import GeneradorDocumentoServicio from "./GeneraDocServicios/GeneraDocServicios";
import GeneradorUx from "./GeneraUx/GeneraUx";

const drawerWidth = 250;
const menuItemStyles = {
  fontSize: '0.875rem',
  lineHeight: '1.2', // Reducido de .75
};

const Main = styled("main", { shouldForwardProp: (prop) => prop !== "open" })(
  ({ theme, open }) => ({
    flexGrow: 1,
    transition: theme.transitions.create("margin", {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
    marginLeft: `-${drawerWidth}px`,
    ...(open && {
      transition: theme.transitions.create("margin", {
        easing: theme.transitions.easing.easeOut,
        duration: theme.transitions.duration.enteringScreen,
      }),
      marginLeft: 0,
    }),
  })
);

const AppBar = styled(MuiAppBar, {
  shouldForwardProp: (prop) => prop !== "open",
})(({ theme, open }) => ({
  transition: theme.transitions.create(["margin", "width"], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  ...(open && {
    width: `calc(100% - ${drawerWidth}px)`,
    marginLeft: `${drawerWidth}px`,
    transition: theme.transitions.create(["margin", "width"], {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
  }),
}));

const DrawerHeader = styled("div")(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  padding: theme.spacing(0, 1),
  ...theme.mixins.toolbar,
  justifyContent: "flex-end",
}));

export default function PersistentDrawerLeft(props) {
  const navigate = useNavigate();
  const theme = useTheme();
  const { onDarkModeChange } = props;
  const [open, setOpen] = React.useState(false);
  const [selectedComponent, setSelectedComponent] = useState(<Home />);

  // Estados para submenús
  const [analysisOpen, setAnalysisOpen] = useState(false);
  const [refinementOpen, setRefinementOpen] = useState(false);
  const [diagramsOpen, setDiagramsOpen] = useState(false);
  const [documentationOpen, setDocumentationOpen] = useState(false);
  const [architectureOpen, setArchitectureOpen] = useState(false);

  const [openAlert, setOpenAlert] = React.useState(false);

  const Alert = React.forwardRef(function Alert(props, ref) {
    return <MuiAlert elevation={6} ref={ref} variant="filled" {...props} />;
  });

  const handleAlertClose = (event, reason) => {
    if (reason === "clickaway") {
      return;
    }
    setOpenAlert(false);
  };

  // Funciones para manejar componentes
  const selectHome = () => setSelectedComponent(<Home />);
  const selectRefFuncional = () => setSelectedComponent(<GeneraRefFuncional/>);
  const selectRefNoFuncional = () => setSelectedComponent(<GeneraRefNoFuncional/>);
  const selectRefTecnico = () => setSelectedComponent(<GeneraRefTecnico/>);
  const selectDef = () => setSelectedComponent(<GeneraDEF/>);
  const selectAnalizarLegadoCloud = () => setSelectedComponent(<AnalizarLegadoCloud/>);
  const selectChatGeneral = () => setSelectedComponent(<Chatbot/>) 
  const selectAnalizarCodigoGo = () => setSelectedComponent(<AnalizarCodigoGO/>);
  const selectAnalizarCodigoJava = () => setSelectedComponent(<AnalizarCodigoGO/>);
  const selectAnalizarCodigoO = () => setSelectedComponent(<AnalizarCodigoO/>);
  const selectAnalizarCodigoLegadoRepomix = () => setSelectedComponent(<AnalizarCodigoLegadoRepomix/>);
  const selectHistoriasTecnicas = () => setSelectedComponent(<GeneradorHistoriasTecnicas/>);
  const selectRefinamientoHus = () => setSelectedComponent(<RefinamientosHus />);
  const selectUML = () => setSelectedComponent(<GeneradorDiagramasUML />);
  const selectUMLMermaid = () => setSelectedComponent(<GeneradorDiagramasMermaid />);
  const selectScrap = () => setSelectedComponent(<WebScraperApp/>);
  const selectAnalizarSQL = () => setSelectedComponent(<AnalizarCodigoSQL/>);
  const selectAnalizarArquitectura = () => setSelectedComponent(<AnalizarArquitectura/>);
  const selectGenerarArquitecturaToBe = () => setSelectedComponent(<GeneradorArquitecturaToBe/>);
  const selectGenerarHistoriasUsuario = () => setSelectedComponent(<GeneradorHistoriasUsuario/>);
  const selectGenerarModeladoDatos = () => setSelectedComponent(<GeneradorModeladoDatos/>);
  const selectGenerarDocumentoArquitectura = () => setSelectedComponent(<GeneradorDocumentoArquitectura/>);
  const selectGenerarDocumentoServicios = () => setSelectedComponent(<GeneradorDocumentoServicio/>);
  const selectGenerarUX = () => setSelectedComponent(<GeneradorUx/>);
  

  const handleDrawerOpen = () => setOpen(true);
  const handleDrawerClose = () => setOpen(false);

  const [darkMode, setDarkMode] = useState(false);
  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    onDarkModeChange();
  };

  const logOut = () => {
    sessionStorage.removeItem("ACCSSTKN");
    navigate("/");
  };

  const iconsStyle = { 
    color: theme.palette.primary.contrastText,
    fontSize: '1.3rem' // Ligeramente más grandes para menús principales
  };
  
  // Estilo específico para botones de submenú
  const subMenuButtonStyle = {
    paddingLeft: 5, // Reducido de 40 para menos margen izquierdo
    
    '& .MuiListItemText-primary': {
      color: theme.palette.gray[300], // Gray 300 (#bdbdbd)
      fontSize: '0.8rem',
      fontWeight: 400,
      lineHeight: '1.1'
    },
    '& .MuiListItemIcon-root': {
      color: theme.palette.gray[300], // Gray 300 para iconos también
      minWidth: '32px' // Reducido de 36px
    },
    '& .MuiSvgIcon-root': {
      fontSize: '1.1rem' // Reducido de 1.2rem
    },
    '&:hover': {
      backgroundColor: alpha('#ffffff', 0.1),
      '& .MuiListItemText-primary': {
        color: '#ffffff' // Blanco en hover
      },
      '& .MuiListItemIcon-root': {
        color: '#ffffff' // Blanco en hover
      }
    }
  };

  const classes = {
    root: {
      width: "100%",
      maxWidth: 360,
      padding: "0px",
      borderRadius: "3px",
    },
  };

  return (
    <Box sx={{ display: "flex" }}>
      <CssBaseline />

<AppBar position="fixed" open={open} sx={{ height: "60px" }}>
        <Toolbar
          style={{
            backgroundColor: theme.palette.primary.main,
            color: theme.palette.primary.main,
          }}
        >
          {/* Contenedor para el icono del menú y la imagen */}
          <Box sx={{ display: "flex", alignItems: "center", mr: 2 }}>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              onClick={handleDrawerOpen}
              edge="start"
              sx={{ 
                mr: 1, 
                ...(open && { display: "none" }), 
                backgroundColor: theme.palette.secondary.contrastText 
              }}
            >
              <MenuIcon />
            </IconButton>
            
            {/* Imagen que siempre permanece visible */}
            <Box
              component="img"
              sx={{
                height: 50, // Ajusta la altura según necesites
                width: 'auto',
                maxWidth: 140, // Limita el ancho máximo
                objectFit: 'contain',
                ml: open ? 0 : 1, // Margen izquierdo cuando el menú está cerrado
              }}
              alt="Logo"
              src="/coppelLogo.png" // Cambia por la ruta de tu imagen
            />
          </Box>

          <Box sx={{ flexGrow: 1 }} />
          <IconButton color="inherit" sx={{ ml: 1 }}>
            Prueba de Concepto
            <Avatar sx={{ ml: 1 }} />
          </IconButton>
        </Toolbar>
      </AppBar>
      <Drawer
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: drawerWidth,
            boxSizing: "border-box",
            backgroundColor: darkMode ? theme.palette.gray[800] : theme.palette.primary.dark,
            color: theme.palette.primary.contrastText, // Usar contrastText del theme
            "& .MuiListItemText-primary": {
              lineHeight: '1.2'
            }
          },
        }}
        variant="persistent"
        anchor="left"
        open={open}
      >
        <DrawerHeader
          sx={{
            justifyContent: "space-between",
            display: "flex",
            backgroundColor: theme.palette.primary.main,
            borderColor: theme.palette.primary.main,
          }}
        >
          <Box sx={{ width: "75%", display: "flex", justifyContent: "center" }}>
            <img src="/bmai.png" alt="Imagen de cabecera" width="40%" />
          </Box>
          <Box sx={{ width: "20%" }}>
            <IconButton
              onClick={handleDrawerClose}
              sx={{ backgroundColor: alpha("#dddddd", 0.3) }}
            >
              {theme.direction === "ltr" ? (
                <ChevronLeftIcon sx={{ color: theme.palette.secondary.contrastText }} />
              ) : (
                <ChevronRightIcon sx={{ color: theme.palette.secondary.contrastText }} />
              )}
            </IconButton>
          </Box>
        </DrawerHeader>
        
        <Divider />

        {/* HOME */}
        <FormControl style={classes.root}>
          <List>
            <ListItemButton onClick={selectHome}>
              <ListItemIcon>
                <HomeIcon sx={iconsStyle} />
              </ListItemIcon>
              <ListItemText 
                primary="Inicio" 
                primaryTypographyProps={{ style: menuItemStyles }} 
              />
            </ListItemButton>
          </List>
        </FormControl>
        <Divider />
        {/* HOME */}
        <FormControl style={classes.root}>
          <List>
            <ListItemButton onClick={selectChatGeneral}>
              <ListItemIcon>
                <SmartToyIcon sx={iconsStyle} />
              </ListItemIcon>
              <ListItemText 
                primary="Chat" 
                primaryTypographyProps={{ style: menuItemStyles }} 
              />
            </ListItemButton>
          </List>
        </FormControl>
        <Divider />
        {/* ANÁLISIS DE CÓDIGO */}
        <FormControl style={classes.root}>
          <List>
            <ListItemButton onClick={() => setAnalysisOpen(!analysisOpen)}>
              <ListItemIcon>
                <AnalyticsIcon sx={iconsStyle} />
              </ListItemIcon>
              <ListItemText 
                primary="Análisis de Código" 
                primaryTypographyProps={{ style: menuItemStyles }} 
              />
              {analysisOpen ? <ExpandLess sx={iconsStyle} /> : <ExpandMore sx={iconsStyle} />}
            </ListItemButton>
            <Collapse in={analysisOpen} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                <ListItemButton sx={subMenuButtonStyle} onClick={selectAnalizarCodigoLegadoRepomix}>
                  <ListItemIcon>
                    <AnalyticsIcon />
                  </ListItemIcon>
                  <ListItemText primary="Legado Repomix" />
                </ListItemButton>           
                <ListItemButton sx={subMenuButtonStyle} onClick={selectAnalizarSQL}>
                  <ListItemIcon>
                    <AnalyticsIcon />
                  </ListItemIcon>
                  <ListItemText primary="Codigo Motores DB" />
                </ListItemButton>                         
                <ListItemButton sx={subMenuButtonStyle} onClick={selectAnalizarCodigoO}>
                  <ListItemIcon>
                    <AnalyticsIcon />
                  </ListItemIcon>
                  <ListItemText primary="Análisis Legado" />
                </ListItemButton>
                <ListItemButton sx={subMenuButtonStyle} onClick={selectAnalizarCodigoGo}>
                  <ListItemIcon>
                    
                    <AnalyticsIcon />
                  </ListItemIcon>
                  <ListItemText primary="GO" />
                </ListItemButton>
                <ListItemButton sx={subMenuButtonStyle} onClick={selectAnalizarCodigoGo}>
                  
                  <ListItemIcon>
                    <AnalyticsIcon />
                  </ListItemIcon>
                  <ListItemText primary="JAVA" />
                </ListItemButton>                                
                <ListItemButton sx={subMenuButtonStyle} onClick={selectAnalizarCodigoJava}>
                  <ListItemIcon>
                    <CloudAnalyticsIcon />
                  </ListItemIcon>
                  <ListItemText primary="Análisis Legado Cloud" />
                </ListItemButton>
              </List>
            </Collapse>
          </List>
        </FormControl>
        <Divider />

        {/* REFINAMIENTOS */}
        <FormControl style={classes.root}>
          <List>
            <ListItemButton onClick={() => setRefinementOpen(!refinementOpen)}>
              <ListItemIcon>
                <FindReplaceIcon sx={iconsStyle} />
              </ListItemIcon>
              <ListItemText 
                primary="Refinamientos" 
                primaryTypographyProps={{ style: menuItemStyles }} 
              />
              {refinementOpen ? <ExpandLess sx={iconsStyle} /> : <ExpandMore sx={iconsStyle} />}
            </ListItemButton>
            <Collapse in={refinementOpen} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                <ListItemButton sx={subMenuButtonStyle} onClick={selectRefinamientoHus}>
                  <ListItemIcon>
                    <FindReplaceIcon />
                  </ListItemIcon>
                  <ListItemText primary="Refinamiento HU's" />
                </ListItemButton>
                <ListItemButton sx={subMenuButtonStyle} onClick={selectRefFuncional}>
                  <ListItemIcon>
                    <FunctionalIcon />
                  </ListItemIcon>
                  <ListItemText primary="Ref. Funcional" />
                </ListItemButton>
                <ListItemButton sx={subMenuButtonStyle} onClick={selectRefNoFuncional}>
                  <ListItemIcon>
                    <SecurityIcon />
                  </ListItemIcon>
                  <ListItemText primary="Ref. No Funcional" />
                </ListItemButton>
                <ListItemButton sx={subMenuButtonStyle} onClick={selectRefTecnico}>
                  <ListItemIcon>
                    <EngineeringIcon />
                  </ListItemIcon>
                  <ListItemText primary="Ref. Técnico" />
                </ListItemButton>
              </List>
            </Collapse>
          </List>
        </FormControl>
        <Divider />

        {/* DIAGRAMAS */}
        <FormControl style={classes.root}>
          <List>
            <ListItemButton onClick={() => setDiagramsOpen(!diagramsOpen)}>
              <ListItemIcon>
                <AccountTreeOutlinedIcon sx={iconsStyle} />
              </ListItemIcon>
              <ListItemText 
                primary="Diagramas" 
                primaryTypographyProps={{ style: menuItemStyles }} 
              />
              {diagramsOpen ? <ExpandLess sx={iconsStyle} /> : <ExpandMore sx={iconsStyle} />}
            </ListItemButton>
            <Collapse in={diagramsOpen} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                <ListItemButton sx={subMenuButtonStyle} onClick={selectUMLMermaid}>
                  <ListItemIcon>
                    <AccountTreeOutlinedIcon />
                  </ListItemIcon>
                  <ListItemText primary="UMLs Mermaid" />
                </ListItemButton>
              </List>
            </Collapse>
            <Collapse in={diagramsOpen} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                <ListItemButton sx={subMenuButtonStyle} onClick={selectUML}>
                  <ListItemIcon>
                    <AccountTreeOutlinedIcon />
                  </ListItemIcon>
                  <ListItemText primary="UMLs" />
                </ListItemButton>
              </List>
            </Collapse>            
          </List>
        </FormControl>
        <Divider />

        {/* DOCUMENTACIÓN */}
        <FormControl style={classes.root}>
          <List>
            <ListItemButton onClick={() => setDocumentationOpen(!documentationOpen)}>
              <ListItemIcon>
                <DescriptionIcon sx={iconsStyle} />
              </ListItemIcon>
              <ListItemText 
                primary="Documentación" 
                primaryTypographyProps={{ style: menuItemStyles }} 
              />
              {documentationOpen ? <ExpandLess sx={iconsStyle} /> : <ExpandMore sx={iconsStyle} />}
            </ListItemButton>
            <Collapse in={documentationOpen} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                <ListItemButton sx={subMenuButtonStyle} onClick={selectDef}>
                  <ListItemIcon>
                    <PlaylistAddIcon />
                  </ListItemIcon>
                  <ListItemText primary="Generación DEF" />
                </ListItemButton>
                <ListItemButton sx={subMenuButtonStyle} onClick={selectGenerarHistoriasUsuario}>
                  <ListItemIcon>
                    <TimelineIcon />
                  </ListItemIcon>
                  <ListItemText primary="Historias Usuario" />
                </ListItemButton>                
                <ListItemButton sx={subMenuButtonStyle} onClick={selectHistoriasTecnicas}>
                  <ListItemIcon>
                    <TimelineIcon />
                  </ListItemIcon>
                  <ListItemText primary="Historias Técnicas" />
                </ListItemButton>
                <ListItemButton sx={subMenuButtonStyle} onClick={selectGenerarModeladoDatos}>
                  <ListItemIcon>
                    <TimelineIcon />
                  </ListItemIcon>
                  <ListItemText primary="Modelado Datos" />
                </ListItemButton>     
                <ListItemButton sx={subMenuButtonStyle} onClick={selectGenerarDocumentoArquitectura}>
                  <ListItemIcon>
                    <TimelineIcon />
                  </ListItemIcon>
                  <ListItemText primary="Doc Arquitectura General" />
                </ListItemButton>    
                <ListItemButton sx={subMenuButtonStyle} onClick={selectGenerarDocumentoServicios}>
                  <ListItemIcon>
                    <TimelineIcon />
                  </ListItemIcon>
                  <ListItemText primary="Doc Servicios" />
                </ListItemButton>                                                
              </List>
            </Collapse>
          </List>
        </FormControl>
        <Divider />

        {/* ANÁLISIS DE ARQUITECTURA */}
        <FormControl style={classes.root}>
          <List>
            <ListItemButton onClick={() => setArchitectureOpen(!architectureOpen)}>
              <ListItemIcon>
                <ArchitectureIcon sx={iconsStyle} />
              </ListItemIcon>
              <ListItemText 
                primary="Análisis de Arquitectura" 
                primaryTypographyProps={{ style: menuItemStyles }} 
              />
              {architectureOpen ? <ExpandLess sx={iconsStyle} /> : <ExpandMore sx={iconsStyle} />}
            </ListItemButton>
            <Collapse in={architectureOpen} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                <ListItemButton sx={subMenuButtonStyle} onClick={selectAnalizarArquitectura}>
                  <ListItemIcon>
                    <ArchitectureIcon />
                  </ListItemIcon>
                  <ListItemText primary="Evaluación Arquitectura" />
                </ListItemButton>
                <ListItemButton sx={subMenuButtonStyle} onClick={selectGenerarArquitecturaToBe}>
                  <ListItemIcon>
                    <ArchitectureIcon />
                  </ListItemIcon>
                  <ListItemText primary="Genera Arqui ToBe" />
                </ListItemButton>                
              </List>
            </Collapse>
          </List>
        </FormControl>
        <Divider />

        {/* DOCUMENTACIÓN */}
        <FormControl style={classes.root}>
          <List>
            <ListItemButton onClick={() => setDocumentationOpen(!documentationOpen)}>
              <ListItemIcon>
                <DescriptionIcon sx={iconsStyle} />
              </ListItemIcon>
              <ListItemText 
                primary="Documentación" 
                primaryTypographyProps={{ style: menuItemStyles }} 
              />
              {documentationOpen ? <ExpandLess sx={iconsStyle} /> : <ExpandMore sx={iconsStyle} />}
            </ListItemButton>
            <Collapse in={documentationOpen} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                <ListItemButton sx={subMenuButtonStyle} onClick={selectGenerarUX}>
                  <ListItemIcon>
                    <PlaylistAddIcon />
                  </ListItemIcon>
                  <ListItemText primary="Genera UX" />
                </ListItemButton>
                <ListItemButton sx={subMenuButtonStyle} onClick={selectGenerarHistoriasUsuario}>
                  <ListItemIcon>
                    <TimelineIcon />
                  </ListItemIcon>
                  <ListItemText primary="Documentación UX" />
                </ListItemButton>                                                 
              </List>
            </Collapse>
          </List>
        </FormControl>
        <Divider />
        {/* CALIDAD*/}
        <FormControl style={classes.root}>
          <List>
            <ListItemButton onClick={() => setDocumentationOpen(!documentationOpen)}>
              <ListItemIcon>
                <DescriptionIcon sx={iconsStyle} />
              </ListItemIcon>
              <ListItemText 
                primary="Calidad" 
                primaryTypographyProps={{ style: menuItemStyles }} 
              />
              {documentationOpen ? <ExpandLess sx={iconsStyle} /> : <ExpandMore sx={iconsStyle} />}
            </ListItemButton>
            <Collapse in={documentationOpen} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                <ListItemButton sx={subMenuButtonStyle} onClick={selectGenerarUX}>
                  <ListItemIcon>
                    <PlaylistAddIcon />
                  </ListItemIcon>
                  <ListItemText primary="Diseño C.Prueba" />
                </ListItemButton>
                <ListItemButton sx={subMenuButtonStyle} onClick={selectGenerarHistoriasUsuario}>
                  <ListItemIcon>
                    <TimelineIcon />
                  </ListItemIcon>
                  <ListItemText primary="Documentación UX" />
                </ListItemButton>                                                 
              </List>
            </Collapse>
          </List>
        </FormControl>
        <Divider />


        {/* HERRAMIENTAS OCULTAS */}
        <FormControl style={classes.root} sx={{ display: 'none' }}>
          <List>
            <ListItemButton onClick={selectScrap}>
              <ListItemIcon>
                <ContentCopyIcon sx={iconsStyle} />
              </ListItemIcon>
              <ListItemText 
                primary="Scrap" 
                primaryTypographyProps={{ style: menuItemStyles }} 
              />
            </ListItemButton>
          </List>
        </FormControl>

        {/* FOOTER CON CONFIGURACIONES */}
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "flex-end",
            flexGrow: 1,
            height: "60px",
          }}
        >
          <Divider />
          <List>
            <ListItemButton color="inherit" onClick={toggleDarkMode}>
              <ListItemIcon>
                {darkMode ? <Brightness4Icon /> : <Brightness7Icon />}
              </ListItemIcon>
              <ListItemText
                primary={darkMode ? "Claro" : "Oscuro"}
                className="listItemText"
                primaryTypographyProps={{ style: menuItemStyles }}
              />
            </ListItemButton>

            <ListItemButton onClick={logOut}>
              <ListItemIcon>
                <ExitToAppIcon />
              </ListItemIcon>
              <ListItemText 
                primary="Cerrar sesión" 
                primaryTypographyProps={{ style: menuItemStyles }}
              />
            </ListItemButton>
          </List>
        </Box>
      </Drawer>

      <Main open={open} sx={{ height: "100vh" }}>
        <DrawerHeader />
        <SwitchTransition>
          <CSSTransition
            key={selectedComponent.type}
            timeout={400}
            classNames="item"
            unmountOnExit
          >
            {selectedComponent}
          </CSSTransition>
        </SwitchTransition>
        <Snackbar
          open={openAlert}
          autoHideDuration={6000}
          onClose={handleAlertClose}
          anchorOrigin={{
            vertical: "bottom",
            horizontal: "center",
          }}
        >
          <Alert
            onClose={handleAlertClose}
            severity="success"
            sx={{ width: "100%" }}
          >
            Mensaje
          </Alert>
        </Snackbar>
      </Main>
    </Box>
  );
}