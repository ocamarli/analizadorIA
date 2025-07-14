// src/services/SpeechService.js
import * as SpeechSDK from "microsoft-cognitiveservices-speech-sdk";

const azureSpeechKey = process.env.REACT_APP_AZURE_SPEECH_KEY;
const azureRegion = process.env.REACT_APP_AZURE_REGION;

/**
 * Inicia el reconocimiento de voz utilizando Azure Speech SDK.
 * @param {string} selectedLocale - Idioma seleccionado para el reconocimiento.
 * @returns {Promise<string>} - Texto reconocido.
 */
export const recognizeSpeech = (selectedLocale) => {
  return new Promise((resolve, reject) => {
    try {
      const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(azureSpeechKey, azureRegion);
      speechConfig.speechRecognitionLanguage = selectedLocale;
      const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
      const recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);

      recognizer.recognized = (sender, event) => {
        const recognizedText = event.result.text;
        recognizer.stopContinuousRecognitionAsync();
        resolve(recognizedText);
      };

      recognizer.canceled = (sender, event) => {
        recognizer.stopContinuousRecognitionAsync();
        reject("Error en el reconocimiento de voz.");
      };

      recognizer.startContinuousRecognitionAsync();
    } catch (error) {
      reject(`Error al iniciar el reconocimiento de voz: ${error}`);
    }
  });
};
