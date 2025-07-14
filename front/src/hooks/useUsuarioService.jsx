// hooks/useSoftwareService.js
import { useState, useCallback } from 'react';

import { crearUsuario,obtenerUsuarios,actualizarUsuario,obtenerUsuario } from '../api/usuariosApi';
export const useUsuarioService = () => {
  const [usuarios, setUsuarios] = useState([]);
  const [usuario, setUsuario] = useState(null);  
  const [isLoading, setIsLoading] = useState(false);
  const [estaActivo, setEstaActivo] = useState(false);
  const [respuestaModal, setRespuestaModal] = useState(false);
  const [idUsuarioSeleccionado, setIdUsuarioSeleccionado] = useState("");
  const [autorizaciones,setAutorizaciones]=useState()
  const [estaActivoModalOk, setEstaActivoModalOk] = useState(false);
  const [respuestaModalOk, setRespuestaModalOk] = useState({
    msg: "¡Usuario deshabilitado!",
    status: true,
  });
  const [estaActivoModalConfirmacionHabilitar, setEstaActivoModalConfirmacionHabilitar] = useState(false);
  const [respuestaModalConfirmacionHabilitar, setRespuestaModalConfirmacionHabilitar] = useState({
    msg: "¡Confirma para habilitar usuario!",
    status: false,
  });
  const [estaActivoModalConfirmacionDeshabilitar, setEstaActivoModalConfirmacionDeshabilitar] = useState(false);
  const [respuestaModalConfirmacionDeshabilitar, setRespuestaModalConfirmacionDeshabilitar] = useState({
    msg: "¡Confirma para deshabilitar usuario!",
    status: false,
  });  
  const handleTabChange = (event, newValue) => {

    setActiveTab(newValue);

      fetchUsuarios(Boolean(newValue))
  
  };

  const [activeTab, setActiveTab] = useState(1);
  const fetchUsuario = useCallback(async (idUsuario) => {
    try {
      setIsLoading(true);
      const tkn = JSON.parse(sessionStorage.getItem("ACCSSTKN"))?.access_token;
      if (tkn) {
        const json = await obtenerUsuario(tkn,idUsuario);
  
        setUsuario(json.usuario || []);
        setAutorizaciones(json.usuario.permisos || null);
      }
      setIsLoading(false);
    } catch (error) {
      setIsLoading(false);
      console.error(error);
    }
  }, []);
  const fetchUsuarios = useCallback(async (estatus) => {
    try {
      setIsLoading(true);
      const tkn = JSON.parse(sessionStorage.getItem("ACCSSTKN"))?.access_token;
      if (tkn) {
        const json = await obtenerUsuarios(tkn,estatus);
        setUsuarios(json.usuarios || []);
      }
      setIsLoading(false);
    } catch (error) {
      setIsLoading(false);
      console.error(error);
    }
  }, []);
  const handleEditarUsuario = async (data) => {
    try {
      const tkn = JSON.parse(sessionStorage.getItem("ACCSSTKN"))?.access_token;
      const response = await actualizarUsuario(data,tkn)
      

          setRespuestaModalOk({ msg: response.msg, status: response.status });
          setEstaActivoModalOk(true);

      setRespuestaModal(response);;
    } catch (error) {
      console.error(error);
    }
  };

  const handleCrearUsuario = async (data) => {
    try {
      const tkn = JSON.parse(sessionStorage.getItem("ACCSSTKN"))?.access_token;
      if (tkn) {
        const response = await crearUsuario(data, tkn);
        setRespuestaModalOk({ msg: response.msg, status:response.status });
        setEstaActivoModalOk(true);
      }
    } catch (error) {
      console.error(error);
    }
  };

  const deshabilitarUsuario = async (idUsuario) => {
    try {
      const tkn = JSON.parse(sessionStorage.getItem("ACCSSTKN"))?.access_token;
      const data = { idUsuario: idUsuario, estatus: false };
      const response = await actualizarUsuario(data, tkn);

          setRespuestaModalOk({ msg: "¡Usuario deshabilitado exitosamente!", status:response.status });
          setEstaActivoModalOk(true);
          fetchUsuarios(true);

    } catch (error) {
      console.error(error);
    }
  };
  const habilitarUsuario = async (idUsuario) => {
    try {
      const tkn = JSON.parse(sessionStorage.getItem("ACCSSTKN"))?.access_token;
      const data = { idUsuario: idUsuario, estatus: true };
      const response = await actualizarUsuario(data, tkn);

     
      setRespuestaModalOk({ msg: "¡Usuario habilitado exitosamente!", status: response.status });
      setEstaActivoModalOk(true);
      fetchUsuarios(false);
        
      
    } catch (error) {
      console.error(error);
    }
  };

  const cerrarModalOk = () => {
    setEstaActivoModalOk(false);
  };
  const cerrarModalConfirmacionHabilitar = (respuestaSeleccionada) => {

    if (respuestaSeleccionada) {
      habilitarUsuario(idUsuarioSeleccionado);
    }
    setEstaActivoModalConfirmacionHabilitar(false); // Restablecer el estado a false cuando se cierra el modal

  };
  const cerrarModalConfirmacionDeshabilitar = (respuestaSeleccionada) => {

    if (respuestaSeleccionada) {


      deshabilitarUsuario(idUsuarioSeleccionado);
    }
    setEstaActivoModalConfirmacionDeshabilitar(false); // Restablecer el estado a false cuando se cierra el modal

  };  

  const handleDeshabilitarUsuario = async (idUsuario) => {
    setIdUsuarioSeleccionado(idUsuario);
    setEstaActivoModalConfirmacionDeshabilitar(true);
  };
  const handleHabilitarUsuario = async (idUsuario) => {
    setIdUsuarioSeleccionado(idUsuario);
    setEstaActivoModalConfirmacionHabilitar(true);
  };
  return {
    // Estado de la pestaña activa
    activeTab,
    setActiveTab,
    handleTabChange,
  
    // Datos y estados de los usuarios
    usuarios,
    usuario,
    isLoading,
    idUsuarioSeleccionado,
    estaActivo,
    autorizaciones,
  
    // Funciones para gestionar usuarios
    fetchUsuarios,
    fetchUsuario,
    handleCrearUsuario,
    handleEditarUsuario,
    handleHabilitarUsuario,
    handleDeshabilitarUsuario,
  
    // Estados y respuestas de los modales
    estaActivoModalOk,
    respuestaModalOk,
    estaActivoModalConfirmacionHabilitar,
    respuestaModalConfirmacionHabilitar,
    estaActivoModalConfirmacionDeshabilitar,
    respuestaModalConfirmacionDeshabilitar,
  
    // Funciones de manejo de modales
    cerrarModalOk,
    cerrarModalConfirmacionHabilitar,
    cerrarModalConfirmacionDeshabilitar,
  
    // Setters
    setRespuestaModalConfirmacionHabilitar,
    setRespuestaModalConfirmacionDeshabilitar,
    setAutorizaciones,
    setEstaActivoModalConfirmacionHabilitar,
    setEstaActivoModalConfirmacionDeshabilitar,
    setIdUsuarioSeleccionado,
    setEstaActivo,
  
    // Otros
    respuestaModal,
  };
};
