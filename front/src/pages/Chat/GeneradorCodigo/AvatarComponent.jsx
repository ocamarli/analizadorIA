// src/components/AvatarComponent.jsx
import React, { useState, useRef, useEffect } from 'react';
import * as SpeechSDK from 'microsoft-cognitiveservices-speech-sdk';
import { Box, Paper, Button } from '@mui/material';

const azureSpeechKey = process.env.REACT_APP_AZURE_SPEECH_KEY;
const azureRegion = process.env.REACT_APP_AZURE_REGION;

const AvatarComponent = ({ setSpeakRef, onSpeak , config}) => {
  const videoRef = useRef(null);
  const audioRef = useRef(null);
  const [avatarSynthesizer, setAvatarSynthesizer] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  const getIceServerConfig = async (azureRegion, azureSpeechKey) => {
    const response = await fetch(
      `https://${azureRegion}.tts.speech.microsoft.com/cognitiveservices/avatar/relay/token/v1`,
      {
        method: "GET",
        headers: {
          "Ocp-Apim-Subscription-Key": azureSpeechKey,
        },
      }
    );
    const data = await response.json();
    return {
      iceServerUrl: data.Urls[0],
      iceServerUsername: data.Username,
      iceServerCredential: data.Password,
    };
  };
  const startSession = async () => {
    const { avatarCharacter, avatarStyle, ttsVoice } = config;

    const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(azureSpeechKey, azureRegion);
    speechConfig.speechSynthesisVoiceName = ttsVoice;

    const avatarConfig = new SpeechSDK.AvatarConfig(avatarCharacter, avatarStyle);
    const synthesizer = new SpeechSDK.AvatarSynthesizer(speechConfig, avatarConfig);
    setAvatarSynthesizer(synthesizer);
    const iceServerConfig = await getIceServerConfig(azureRegion, azureSpeechKey);
    const peerConnection = new RTCPeerConnection({
      iceServers: [
        {
          urls: [iceServerConfig.iceServerUrl],
          username: iceServerConfig.iceServerUsername,
          credential: iceServerConfig.iceServerCredential,
        },
      ],
    });
    peerConnection.ontrack = (event) => {
      if (event.track.kind === 'video' && videoRef.current) {
        videoRef.current.srcObject = event.streams[0];
      }
      if (event.track.kind === 'audio' && audioRef.current) {
        audioRef.current.srcObject = event.streams[0];
      }
    };

    peerConnection.addTransceiver('video', { direction: 'recvonly' });
    peerConnection.addTransceiver('audio', { direction: 'recvonly' });

    try {
      await synthesizer.startAvatarAsync(peerConnection);
      setIsConnected(true);
    } catch (error) {
      console.error('Error al conectar el avatar:', error);
      synthesizer.close();
    }
  };

  const stopSession = () => {
    if (avatarSynthesizer) {
      avatarSynthesizer.close();
      setAvatarSynthesizer(null);
      setIsConnected(false);
    }
  };

  const speakText = (text) => {
    if (avatarSynthesizer && isConnected) {
        console.log(text)
      avatarSynthesizer.speakTextAsync(text).then((result) => {
        if (result.reason === SpeechSDK.ResultReason.SynthesizingAudioCompleted) {
          console.log('Texto sintetizado en el avatar.');
        } else {
          console.log('Error al sintetizar el texto.');
        }
      }).catch((error) => {
        console.error('Error en la síntesis de voz:', error);
      });
    }
  };
  useEffect(() => {
    if (setSpeakRef) {
      setSpeakRef(speakText);
    }
  }, [setSpeakRef, avatarSynthesizer, isConnected]);
  return (
    <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
      <video ref={videoRef} style={{ width: '100%', height: 'auto', borderRadius: '80%' }} autoPlay muted />
      <audio ref={audioRef} autoPlay />
      <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
        <Button variant="contained" color="primary" onClick={startSession} disabled={isConnected}>
          Iniciar Avatar
        </Button>
        <Button variant="contained" color="secondary" onClick={stopSession} disabled={!isConnected}>
          Detener Avatar
        </Button>
      </Box>
    </Paper>
  );
};

export default AvatarComponent;